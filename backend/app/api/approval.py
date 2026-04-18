from fastapi import APIRouter, HTTPException, Query

from app.schemas.ticket import TicketResponse
from app.services.review_token_service import validate_review_token
from app.services.ticket_service import approve_ticket, reject_ticket


router = APIRouter(prefix="/api", tags=["api-approval"])


@router.get("/approve", response_model=TicketResponse)
async def approve(ticket_id: str = Query(...), token: str = Query(...)) -> TicketResponse:
    if not validate_review_token(ticket_id, token):
        raise HTTPException(status_code=403, detail="Invalid review token.")
    return await approve_ticket(ticket_id)


@router.get("/reject", response_model=TicketResponse)
async def reject(ticket_id: str = Query(...), token: str = Query(...)) -> TicketResponse:
    if not validate_review_token(ticket_id, token):
        raise HTTPException(status_code=403, detail="Invalid review token.")
    return await reject_ticket(ticket_id)
