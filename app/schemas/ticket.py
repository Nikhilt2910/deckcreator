from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TicketReviewOutcome(BaseModel):
    applied: bool = False
    message: str = ""
    applied_at: datetime | None = None


class TicketAutomationResult(BaseModel):
    patch_applied: bool = False
    tests_passed: bool = False
    pushed: bool = False
    branch: str | None = None
    commit_sha: str | None = None
    message: str = ""
    completed_at: datetime | None = None


class TicketCreate(BaseModel):
    type: Literal["bug", "feature"]
    description: str = Field(..., min_length=5, max_length=4000)


class TicketResolution(BaseModel):
    files: list[str] = Field(default_factory=list)
    patch: str = ""
    explanation: str = ""
    generated_at: datetime


class TicketResponse(BaseModel):
    id: str
    type: Literal["bug", "feature"]
    description: str
    created_at: datetime
    jira_synced: bool
    jira_issue_key: str | None = None
    resolution: TicketResolution | None = None
    status: Literal["pending", "approved", "rejected"] = "pending"
    developer_email: str | None = None
    review_url: str | None = None
    email_sent: bool = False
    email_error: str | None = None
    review_outcome: TicketReviewOutcome | None = None
    automation_result: TicketAutomationResult | None = None
