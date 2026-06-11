from __future__ import annotations

from app.agents.base_agent import BaseTicketAgent


class KnowledgeAgent(BaseTicketAgent):
    agent_name = "KnowledgeAgent"

    def run(self, *, ticket_id: int) -> dict:
        ticket = self.ticket_service.get_ticket(ticket_id)
        query = "\n".join(
            filter(
                None,
                [
                    ticket.title,
                    ticket.content,
                    ticket.category,
                    ticket.priority,
                    ticket.ai_summary or "",
                ],
            )
        )
        context = self.rag_service.retrieve_context(query, top_k=5)
        return {
            "agent_name": self.agent_name,
            "query": query,
            "confidence": context.confidence,
            "low_confidence_reason": context.low_confidence_reason,
            "hits": [
                {
                    "doc_id": chunk.doc_id,
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "content_preview": chunk.content_preview,
                    "score": chunk.score,
                    "embedding_id": chunk.embedding_id,
                }
                for chunk in context.chunks
            ],
        }
