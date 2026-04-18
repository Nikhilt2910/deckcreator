import os
import smtplib
from email.message import EmailMessage
from html import escape

from dotenv import load_dotenv

from app.schemas.ticket import TicketResponse
from app.services.review_token_service import build_review_token


load_dotenv()

DEFAULT_DEVELOPER_EMAIL = "nikhil.t2910@gmail.com"


def send_ticket_review_email(ticket: TicketResponse) -> tuple[bool, str | None]:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM_EMAIL", smtp_username or DEFAULT_DEVELOPER_EMAIL)

    if not smtp_host or not smtp_username or not smtp_password:
        return False, "SMTP is not configured."

    review_url = ticket.review_url or f"http://127.0.0.1:8000/ticket/{ticket.id}/review"
    token = build_review_token(ticket.id)
    approve_url = f"{review_url}?token={token}&action=approve"
    reject_url = f"{review_url}?token={token}&action=reject"
    secure_review_url = f"{review_url}?token={token}"
    jira_fragment = f"Jira issue: {ticket.jira_issue_key}\n" if ticket.jira_issue_key else ""
    resolution = ticket.resolution
    files = "\n".join(f"- {path}" for path in (resolution.files if resolution else [])) or "- No file suggestions"
    explanation = resolution.explanation if resolution else "No explanation generated."
    patch = resolution.patch if resolution else "No patch generated."
    safe_description = escape(ticket.description)
    safe_jira = escape(ticket.jira_issue_key or "Not synced")
    safe_files = escape(files)
    safe_explanation = escape(explanation)
    safe_patch = escape(patch)

    message = EmailMessage()
    message["Subject"] = f"Ticket review needed: {ticket.type} {ticket.id}"
    message["From"] = smtp_from
    message["To"] = ticket.developer_email or DEFAULT_DEVELOPER_EMAIL
    message.set_content(
        (
            f"Ticket: {ticket.id}\n"
            f"Type: {ticket.type}\n"
            f"{jira_fragment}"
            f"Description:\n{ticket.description}\n\n"
            f"Proposed files:\n{files}\n\n"
            f"Explanation:\n{explanation}\n\n"
            f"Patch:\n{patch}\n\n"
            f"Approve:\n{approve_url}\n\n"
            f"Reject:\n{reject_url}\n\n"
            f"Review this ticket here:\n{secure_review_url}\n"
        )
    )
    message.add_alternative(
        (
            "<html><body style=\"font-family:Arial,sans-serif;background:#0b1016;color:#e8eef5;padding:24px;\">"
            f"<h2>Ticket review needed: {ticket.type} {ticket.id}</h2>"
            f"<p><strong>Description:</strong> {safe_description}</p>"
            f"<p><strong>Jira issue:</strong> {safe_jira}</p>"
            "<p style=\"margin:24px 0;\">"
            f"<a href=\"{approve_url}\" style=\"display:inline-block;padding:12px 20px;border-radius:999px;background:#8ef3ff;color:#061018;text-decoration:none;font-weight:700;margin-right:12px;\">Approve</a>"
            f"<a href=\"{reject_url}\" style=\"display:inline-block;padding:12px 20px;border-radius:999px;background:#202833;color:#f3f7fb;text-decoration:none;font-weight:700;\">Reject</a>"
            "</p>"
            f"<p><a href=\"{secure_review_url}\" style=\"color:#8ef3ff;\">Open secure review page</a></p>"
            f"<p><strong>Proposed files:</strong></p><pre style=\"white-space:pre-wrap;background:#121922;padding:16px;border-radius:16px;\">{safe_files}</pre>"
            f"<p><strong>Explanation:</strong></p><pre style=\"white-space:pre-wrap;background:#121922;padding:16px;border-radius:16px;\">{safe_explanation}</pre>"
            f"<p><strong>Patch:</strong></p><pre style=\"white-space:pre-wrap;background:#121922;padding:16px;border-radius:16px;max-height:360px;overflow:auto;\">{safe_patch}</pre>"
            "</body></html>"
        ),
        subtype="html",
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
    except Exception as exc:
        return False, str(exc)
    return True, None
