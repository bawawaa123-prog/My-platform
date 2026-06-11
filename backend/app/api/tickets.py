from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.models.user import User
from app.db.session import get_db
from app.schemas.ticket import SimilarTicketRead, TicketCreate, TicketRead, TicketUpdate
from app.schemas.ticket_message import TicketMessageCreate, TicketMessageRead
from app.services.ticket_similarity_service import TicketSimilarityService
from app.services.ticket_service import TicketService


router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("", response_model=TicketRead)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    ticket = TicketService(db).create_ticket(payload, created_by=current_user)
    return TicketRead.model_validate(ticket)


@router.get("", response_model=list[TicketRead])
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketRead]:
    tickets = TicketService(db).list_tickets()
    return [TicketRead.model_validate(ticket) for ticket in tickets]


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    ticket = TicketService(db).get_ticket(ticket_id)
    return TicketRead.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    ticket = TicketService(db).update_ticket(ticket_id, payload, current_user)
    return TicketRead.model_validate(ticket)


@router.get("/{ticket_id}/messages", response_model=list[TicketMessageRead])
def list_ticket_messages(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketMessageRead]:
    messages = TicketService(db).list_ticket_messages(ticket_id)
    return [TicketMessageRead.model_validate(message) for message in messages]


@router.post("/{ticket_id}/messages", response_model=TicketMessageRead)
def add_ticket_message(
    ticket_id: int,
    payload: TicketMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketMessageRead:
    message = TicketService(db).add_ticket_message(ticket_id, payload, current_user)
    return TicketMessageRead.model_validate(message)


@router.get("/{ticket_id}/similar", response_model=list[SimilarTicketRead])
def list_similar_tickets(
    ticket_id: int,
    top_k: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SimilarTicketRead]:
    return TicketSimilarityService(db).list_similar_tickets(ticket_id, top_k=top_k)
