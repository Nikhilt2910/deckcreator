from fastapi import APIRouter, HTTPException, Query

from app.schemas.ticket import TicketCreate, TicketResponse
from app.services.review_token_service import validate_review_token
from app.services.ticket_service import create_ticket, get_ticket, get_ticket_automation_payload


router = APIRouter(prefix="/api", tags=["api-ticket"])


@router.post("/ticket", response_model=TicketResponse)
async def submit_ticket(payload: TicketCreate) -> TicketResponse:
    return await create_ticket(payload)


@router.get("/ticket/{ticket_id}", response_model=TicketResponse)
async def ticket_status(ticket_id: str) -> TicketResponse:
    return get_ticket(ticket_id)


@router.get("/ticket/{ticket_id}/automation")
async def ticket_automation_payload(ticket_id: str, token: str = Query(...)) -> dict[str, object]:
    if not validate_review_token(ticket_id, token):
        raise HTTPException(status_code=403, detail="Invalid automation token.")
    return get_ticket_automation_payload(ticket_id, token)
