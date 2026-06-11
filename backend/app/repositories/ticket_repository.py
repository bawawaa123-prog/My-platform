from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket


class TicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def list_all(self) -> list[Ticket]:
        statement = select(Ticket).order_by(Ticket.created_at.desc(), Ticket.id.desc())
        return list(self.db.scalars(statement).all())

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        statement = select(Ticket).where(Ticket.id == ticket_id)
        return self.db.scalar(statement)

    def list_resolved_or_closed_excluding(self, ticket_id: int) -> list[Ticket]:
        statement = (
            select(Ticket)
            .where(
                Ticket.id != ticket_id,
                Ticket.status.in_(("resolved", "closed")),
            )
            .order_by(Ticket.updated_at.desc(), Ticket.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def save(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket
