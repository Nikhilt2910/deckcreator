from fastapi import APIRouter

from app.schemas.ticket import TicketCreate, TicketResponse
from app.services.ticket_service import create_ticket, get_ticket


router = APIRouter(prefix="/api", tags=["api-ticket"])


@router.post("/ticket", response_model=TicketResponse)
async def submit_ticket(payload: TicketCreate) -> TicketResponse:
    return await create_ticket(payload)


@router.get("/ticket/{ticket_id}", response_model=TicketResponse)
async def ticket_status(ticket_id: str) -> TicketResponse:
    return get_ticket(ticket_id)
