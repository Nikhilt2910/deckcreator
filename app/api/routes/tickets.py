from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.schemas.ticket import TicketCreate, TicketResponse
from app.services.review_token_service import validate_review_token
from app.services.ticket_service import (
    approve_ticket,
    create_ticket,
    get_ticket,
    regenerate_ticket_resolution,
    reject_ticket,
)


router = APIRouter(tags=["tickets"])
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.post("/ticket", response_model=TicketResponse)
async def submit_ticket(payload: TicketCreate) -> TicketResponse:
    return await create_ticket(payload)


@router.post("/ticket/{ticket_id}/resolution", response_model=TicketResponse)
async def regenerate_resolution(ticket_id: str) -> TicketResponse:
    return await regenerate_ticket_resolution(ticket_id)


@router.get("/ticket/{ticket_id}/review", response_class=HTMLResponse)
async def review_ticket(
    request: Request,
    ticket_id: str,
    token: str = Query(...),
    action: str | None = Query(default=None),
) -> HTMLResponse:
    if not validate_review_token(ticket_id, token):
        raise HTTPException(status_code=403, detail="Invalid review token.")
    if action == "approve":
        ticket = await approve_ticket(ticket_id)
    elif action == "reject":
        ticket = await reject_ticket(ticket_id)
    else:
        ticket = get_ticket(ticket_id)
    return templates.TemplateResponse(
        request=request,
        name="ticket_review.html",
        context={"request": request, "ticket": ticket, "token": token},
    )


@router.post("/ticket/{ticket_id}/approve", response_model=TicketResponse)
async def approve_ticket_route(ticket_id: str, token: str = Query(...)) -> TicketResponse:
    if not validate_review_token(ticket_id, token):
        raise HTTPException(status_code=403, detail="Invalid review token.")
    return await approve_ticket(ticket_id)


@router.post("/ticket/{ticket_id}/reject", response_model=TicketResponse)
async def reject_ticket_route(ticket_id: str, token: str = Query(...)) -> TicketResponse:
    if not validate_review_token(ticket_id, token):
        raise HTTPException(status_code=403, detail="Invalid review token.")
    return await reject_ticket(ticket_id)
