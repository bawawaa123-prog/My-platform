'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-05-30 16:12:09
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-03 14:56:59
FilePath: \My-platform\backend\app\api\tickets.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from fastapi import APIRouter, Depends,Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.models.user import User
from app.db.session import get_db
from app.schemas.ticket import SimilarTicketRead, TicketCreate, TicketPage, TicketRead, TicketUpdate
from app.schemas.ticket_message import TicketMessageCreate, TicketMessageRead
from app.services.ticket_similarity_service import TicketSimilarityService
from app.services.ticket_service import TicketService
from app.schemas.ticket import (
    TicketStatus,
    TicketPriority,
    TicketCategory,
)

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
    status: TicketStatus | None = Query(default=None),
    priority: TicketPriority | None = Query(default=None),
    category: TicketCategory | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketRead]:
    tickets = TicketService(db).list_tickets(status=status, priority=priority, category=category)
    return [TicketRead.model_validate(ticket) for ticket in tickets]


@router.get("/page", response_model=TicketPage)
def list_tickets_page(
    status: TicketStatus | None = Query(default=None),
    priority: TicketPriority | None = Query(default=None),
    category: TicketCategory | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketPage:
    page = TicketService(db).list_tickets_page(
        status=status,
        priority=priority,
        category=category,
        limit=limit,
        offset=offset,
    )
    return TicketPage(
        items=[TicketRead.model_validate(t) for t in page["items"]],
        total=page["total"],
        limit=page["limit"],
        offset=page["offset"],
    )


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