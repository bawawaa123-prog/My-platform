from __future__ import annotations

from app.agents.base_agent import BaseTicketAgent


class SimilarCaseAgent(BaseTicketAgent):
    agent_name = "SimilarCaseAgent"

    def run(self, *, ticket_id: int) -> dict:
        similar_tickets = self.ticket_similarity_service.list_similar_tickets(ticket_id, top_k=3)
        serialized_tickets = [ticket.model_dump(mode="json") for ticket in similar_tickets]
        return {
            "agent_name": self.agent_name,
            "similar_tickets": serialized_tickets,
            "historical_summary": self._build_historical_summary(serialized_tickets),
        }

    @staticmethod
    def _build_historical_summary(similar_tickets: list[dict]) -> str:
        if not similar_tickets:
            return "No resolved or closed historical tickets were similar enough to reuse."

        summary_parts = []
        for item in similar_tickets:
            summary_parts.append(
                f"Ticket #{item['ticket_id']} ({item['title']}) was resolved with: {item['resolution']}"
            )
        return " ".join(summary_parts)
