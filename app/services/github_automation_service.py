import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

from app.schemas.ticket import TicketAutomationResult, TicketResponse
from app.services.review_token_service import build_review_token, validate_review_token


load_dotenv()


def should_use_github_actions_automation() -> bool:
    return os.getenv("GITHUB_AUTOMATION_MODE", "").lower() == "actions"


def build_automation_payload(ticket: TicketResponse, token: str) -> dict[str, object]:
    if not validate_review_token(ticket.id, token):
        raise ValueError("Invalid automation token.")
    if ticket.resolution is None:
        raise ValueError("Ticket has no valid resolution.")
    return {
        "ticket_id": ticket.id,
        "ticket_type": ticket.type,
        "description": ticket.description,
        "files": ticket.resolution.files,
        "patch": ticket.resolution.patch,
        "explanation": ticket.resolution.explanation,
        "generated_at": ticket.resolution.generated_at.isoformat(),
    }


async def dispatch_github_automation(ticket: TicketResponse) -> TicketAutomationResult:
    repo_owner, repo_name = _parse_repo()
    github_token = os.getenv("GITHUB_TOKEN")
    app_base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    if not github_token or not repo_owner or not repo_name:
        return TicketAutomationResult(
            message="GitHub Actions automation is enabled, but GitHub repository configuration is incomplete.",
            completed_at=datetime.now(timezone.utc),
        )

    token = build_review_token(ticket.id)
    branch = os.getenv("GITHUB_BRANCH", "master")
    payload = {
        "event_type": "approved-ticket",
        "client_payload": {
            "ticket_id": ticket.id,
            "token": token,
            "backend_url": app_base_url,
            "branch": branch,
        },
    }
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches",
            headers=headers,
            json=payload,
        )

    if response.status_code >= 300:
        return TicketAutomationResult(
            message=f"GitHub Actions dispatch failed: {response.text}",
            completed_at=datetime.now(timezone.utc),
        )

    return TicketAutomationResult(
        patch_applied=False,
        tests_passed=False,
        pushed=False,
        branch=branch,
        message="Developer approval received. GitHub Actions automation was queued.",
        completed_at=datetime.now(timezone.utc),
    )


def _parse_repo() -> tuple[str | None, str | None]:
    repo_url = os.getenv("GITHUB_REPO_URL", "").strip()
    if not repo_url:
        return None, None
    if repo_url.startswith("git@github.com:"):
        tail = repo_url.split(":", 1)[1]
        owner_repo = tail.removesuffix(".git")
        if "/" in owner_repo:
            owner, repo = owner_repo.split("/", 1)
            return owner, repo
        return None, None

    parsed = urlparse(repo_url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None, None
    owner = parts[0]
    repo = parts[1].removesuffix(".git")
    return owner, repo
