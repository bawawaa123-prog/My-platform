from __future__ import annotations

from fastmcp import FastMCP

from app.db.session import SessionLocal
from app.schemas.knowledge import KnowledgeChunkRead, KnowledgeDocRead
from app.schemas.ticket import SimilarTicketRead, TicketRead
from app.schemas.ticket_message import TicketMessageRead
from app.services.analytics_service import AnalyticsService
from app.services.knowledge_service import KnowledgeService
from app.services.ticket_service import TicketService
from app.services.ticket_similarity_service import TicketSimilarityService


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource("ticket://{ticket_id}")
    def ticket_resource(ticket_id: int) -> dict:
        """Structured ticket context including core fields, messages, and similar cases."""
        db = SessionLocal()
        try:
            ticket_service = TicketService(db)
            ticket = ticket_service.get_ticket(ticket_id)
            messages = ticket_service.list_ticket_messages(ticket_id)
            similar_tickets = TicketSimilarityService(db).list_similar_tickets(ticket_id, top_k=5)
            return {
                "ticket": TicketRead.model_validate(ticket).model_dump(mode="json"),
                "messages": [
                    TicketMessageRead.model_validate(message).model_dump(mode="json")
                    for message in messages
                ],
                "similar_tickets": [
                    SimilarTicketRead.model_validate(item).model_dump(mode="json")
                    for item in similar_tickets
                ],
            }
        finally:
            db.close()

    @mcp.resource("knowledge-doc://{doc_id}")
    def knowledge_doc_resource(doc_id: int) -> dict:
        """Structured knowledge document content with chunk details."""
        db = SessionLocal()
        try:
            service = KnowledgeService(db)
            knowledge_doc = service.get_document(doc_id)
            chunks = service.list_chunks(doc_id)
            return {
                "document": KnowledgeDocRead.model_validate(knowledge_doc)
                .model_copy(update={"chunks_count": service.get_chunks_count(doc_id)})
                .model_dump(mode="json"),
                "chunks": [
                    KnowledgeChunkRead.model_validate(chunk).model_dump(mode="json")
                    for chunk in chunks
                ],
            }
        finally:
            db.close()

    @mcp.resource("analytics://overview")
    def analytics_overview_resource() -> dict:
        """Structured analytics overview for ticket operations and AI adoption."""
        db = SessionLocal()
        try:
            return AnalyticsService(db).get_overview()
        finally:
            db.close()
