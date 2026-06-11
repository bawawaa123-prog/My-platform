from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.rag_service import RagService
from app.services.risk_service import RiskService
from app.services.ticket_similarity_service import TicketSimilarityService
from app.services.ticket_service import TicketService


class BaseTicketAgent:
    agent_name = "BaseTicketAgent"

    def __init__(self, db: Session):
        self.db = db
        self.ticket_service = TicketService(db)
        self.rag_service = RagService(db)
        self.risk_service = RiskService()
        self.ticket_similarity_service = TicketSimilarityService(db)
