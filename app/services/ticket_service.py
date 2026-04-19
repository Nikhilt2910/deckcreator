import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

from app.core.config import TICKETS_FILE
from app.schemas.ticket import TicketCreate, TicketResolution, TicketResponse, TicketReviewOutcome
from app.services.email_service import DEFAULT_DEVELOPER_EMAIL, send_ticket_review_email
from app.services.engineering_agent_service import generate_ticket_resolution
from app.services.patch_service import apply_unified_diff, revert_unified_diff
from app.services.repo_automation_service import run_post_approval_pipeline


load_dotenv()


async def create_ticket(payload: TicketCreate) -> TicketResponse:
    created_at = datetime.now(timezone.utc)
    ticket_id = uuid4().hex[:10]
    jira_issue_key = await _create_jira_issue(payload, ticket_id)
    resolution = _safe_generate_resolution(payload.description)
    review_url = _build_review_url(ticket_id)
    ticket = TicketResponse(
        id=ticket_id,
        type=payload.type,
        description=payload.description,
        created_at=created_at,
        jira_synced=bool(jira_issue_key),
        jira_issue_key=jira_issue_key,
        resolution=resolution,
        status="pending",
        developer_email=DEFAULT_DEVELOPER_EMAIL,
        review_url=review_url,
    )
    email_sent, email_error = _maybe_send_review_email(ticket)
    ticket.email_sent = email_sent
    ticket.email_error = email_error
    _persist_ticket(ticket)
    return ticket


async def regenerate_ticket_resolution(ticket_id: str) -> TicketResponse:
    ticket, index, tickets = _load_ticket(ticket_id)
    ticket.resolution = _safe_generate_resolution(ticket.description)
    if ticket.resolution is not None and not ticket.email_sent:
        email_sent, email_error = _maybe_send_review_email(ticket)
        ticket.email_sent = email_sent
        ticket.email_error = email_error
    _write_ticket(ticket, index, tickets)
    return ticket


def get_ticket(ticket_id: str) -> TicketResponse:
    ticket, _, _ = _load_ticket(ticket_id)
    return ticket


async def approve_ticket(ticket_id: str) -> TicketResponse:
    ticket, index, tickets = _load_ticket(ticket_id)
    ticket.status = "approved"
    ticket.review_outcome = _apply_resolution_with_refresh(ticket)
    if ticket.review_outcome.applied:
        ticket.automation_result = run_post_approval_pipeline(
            ticket.id,
            files_to_stage=ticket.resolution.files if ticket.resolution else None,
        )
        if not ticket.automation_result.pushed:
            rollback = _rollback_resolution(ticket.resolution)
            ticket.review_outcome = TicketReviewOutcome(
                applied=False,
                message=(
                    f"{ticket.review_outcome.message}\n"
                    f"Automation did not finish cleanly, so the local patch was rolled back.\n"
                    f"{rollback.message}"
                ).strip(),
                applied_at=datetime.now(timezone.utc),
            )
    _write_ticket(ticket, index, tickets)
    return ticket


async def reject_ticket(ticket_id: str) -> TicketResponse:
    ticket, index, tickets = _load_ticket(ticket_id)
    ticket.status = "rejected"
    ticket.review_outcome = TicketReviewOutcome(
        applied=False,
        message="Resolution rejected by developer.",
        applied_at=datetime.now(timezone.utc),
    )
    _write_ticket(ticket, index, tickets)
    return ticket


def _persist_ticket(ticket: TicketResponse) -> None:
    existing = _read_tickets()
    existing.append(ticket.model_dump(mode="json"))
    TICKETS_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def _read_tickets() -> list[dict]:
    if not TICKETS_FILE.exists():
        return []
    try:
        return json.loads(TICKETS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _safe_generate_resolution(ticket_description: str) -> TicketResolution | None:
    try:
        return generate_ticket_resolution(ticket_description)
    except Exception:
        return None


def _maybe_send_review_email(ticket: TicketResponse) -> tuple[bool, str | None]:
    if ticket.resolution is None:
        return False, "No valid resolution was generated, so no developer approval email was sent."
    return send_ticket_review_email(ticket)


def _apply_resolution(resolution: TicketResolution | None) -> TicketReviewOutcome:
    if resolution is None:
        return TicketReviewOutcome(
            applied=False,
            message="No generated resolution was available to apply.",
            applied_at=datetime.now(timezone.utc),
        )
    return apply_unified_diff(resolution.patch)


def _apply_resolution_with_refresh(ticket: TicketResponse) -> TicketReviewOutcome:
    initial = _apply_resolution(ticket.resolution)
    if initial.applied:
        return initial

    refreshed = _safe_generate_resolution(ticket.description)
    if refreshed is None:
        return initial

    ticket.resolution = refreshed
    retried = _apply_resolution(ticket.resolution)
    if retried.applied:
        retried.message = (
            "The original patch was stale, so the app regenerated the resolution against the current codebase and applied the refreshed patch."
        )
    return retried


def _rollback_resolution(resolution: TicketResolution | None) -> TicketReviewOutcome:
    if resolution is None:
        return TicketReviewOutcome(
            applied=False,
            message="No generated resolution was available to roll back.",
            applied_at=datetime.now(timezone.utc),
        )
    return revert_unified_diff(resolution.patch)


def _load_ticket(ticket_id: str) -> tuple[TicketResponse, int, list[dict]]:
    tickets = _read_tickets()
    for index, raw_ticket in enumerate(tickets):
        if raw_ticket.get("id") == ticket_id:
            return TicketResponse.model_validate(raw_ticket), index, tickets
    raise HTTPException(status_code=404, detail="Ticket not found.")


def _write_ticket(ticket: TicketResponse, index: int, tickets: list[dict]) -> None:
    tickets[index] = ticket.model_dump(mode="json")
    TICKETS_FILE.write_text(json.dumps(tickets, indent=2), encoding="utf-8")


def _build_review_url(ticket_id: str) -> str:
    base_url = os.getenv("FRONTEND_APP_URL", "http://localhost:3000").rstrip("/")
    return f"{base_url}/review/{ticket_id}"


async def _create_jira_issue(payload: TicketCreate, ticket_id: str) -> str | None:
    jira_base_url = os.getenv("JIRA_BASE_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_api_token = os.getenv("JIRA_API_TOKEN")
    jira_project_key = os.getenv("JIRA_PROJECT_KEY", "DEC")

    if not jira_base_url or not jira_email or not jira_api_token:
        return None

    summary = f"[App Feedback] {payload.type.title()} #{ticket_id}"
    description = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": payload.description},
                ],
            }
        ],
    }

    try:
        async with httpx.AsyncClient(auth=(jira_email, jira_api_token), timeout=20.0) as client:
            issue_type_name = await _resolve_issue_type_name(
                client=client,
                jira_base_url=jira_base_url,
                jira_project_key=jira_project_key,
                ticket_type=payload.type,
            )
            body = {
                "fields": {
                    "project": {"key": jira_project_key},
                    "summary": summary,
                    "issuetype": {"name": issue_type_name},
                    "description": description,
                    "labels": ["app-feedback", payload.type],
                }
            }
            response = await client.post(
                f"{jira_base_url.rstrip('/')}/rest/api/3/issue",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json=body,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Jira sync failed: {response.text}")
        data = response.json()
        return data.get("key")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Jira sync failed: {exc}") from exc


async def _resolve_issue_type_name(
    client: httpx.AsyncClient,
    jira_base_url: str,
    jira_project_key: str,
    ticket_type: str,
) -> str:
    preferred_name = (
        os.getenv("JIRA_BUG_ISSUE_TYPE", "Bug")
        if ticket_type == "bug"
        else os.getenv("JIRA_FEATURE_ISSUE_TYPE", "Task")
    )
    available_types = await _fetch_available_issue_types(client, jira_base_url, jira_project_key)
    available_names = [item["name"] for item in available_types]

    if preferred_name in available_names:
        return preferred_name

    fallback_candidates = (
        ["Bug", "Task", "Story", "Issue", "Epic"]
        if ticket_type == "bug"
        else ["Task", "Story", "Issue", "Epic", "Bug"]
    )
    for candidate in fallback_candidates:
        if candidate in available_names:
            return candidate

    for item in available_types:
        if not item.get("subtask"):
            return item["name"]

    raise HTTPException(status_code=502, detail="Jira sync failed: no valid issue type is available for this project.")


async def _fetch_available_issue_types(
    client: httpx.AsyncClient,
    jira_base_url: str,
    jira_project_key: str,
) -> list[dict]:
    response = await client.get(
        f"{jira_base_url.rstrip('/')}/rest/api/3/issue/createmeta/{jira_project_key}/issuetypes",
        headers={"Accept": "application/json"},
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Jira sync failed: {response.text}")
    data = response.json()
    return data.get("issueTypes", [])
