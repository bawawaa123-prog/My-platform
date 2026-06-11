from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket_embedding import TicketEmbedding


class TicketEmbeddingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_ticket_id(self, ticket_id: int) -> TicketEmbedding | None:
        statement = select(TicketEmbedding).where(TicketEmbedding.ticket_id == ticket_id)
        return self.db.scalar(statement)

    def create(self, ticket_embedding: TicketEmbedding) -> TicketEmbedding:
        self.db.add(ticket_embedding)
        self.db.commit()
        self.db.refresh(ticket_embedding)
        return ticket_embedding

    def save(self, ticket_embedding: TicketEmbedding) -> TicketEmbedding:
        self.db.add(ticket_embedding)
        self.db.commit()
        self.db.refresh(ticket_embedding)
        return ticket_embedding
