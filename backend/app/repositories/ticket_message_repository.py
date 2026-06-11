from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket_message import TicketMessage


class TicketMessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, message: TicketMessage) -> TicketMessage:
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_by_ticket_id(self, ticket_id: int) -> list[TicketMessage]:
        statement = (
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket_id)
            .order_by(TicketMessage.created_at.asc(), TicketMessage.id.asc())
        )
        return list(self.db.scalars(statement).all())
