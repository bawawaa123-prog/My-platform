from __future__ import annotations

from app.agents.base_agent import BaseTicketAgent
from app.services.rag_service import RetrievedContext


class ReplyAgent(BaseTicketAgent):
    agent_name = "ReplyAgent"

    def run(
        self,
        *,
        ticket_id: int,
        triage_result: dict,
        knowledge_result: dict,
        similar_case_result: dict,
    ) -> dict:
        ticket = self.ticket_service.get_ticket(ticket_id)
        context = RetrievedContext(
            chunks=self.rag_service.deserialize_knowledge_hits(knowledge_result.get("hits", [])),
            confidence=knowledge_result.get("confidence", 0.15),
            low_confidence_reason=knowledge_result.get("low_confidence_reason"),
        )
        supplemental_context = self._build_supplemental_context(
            triage_result=triage_result,
            similar_case_result=similar_case_result,
        )
        suggestion = self.rag_service.generate_ticket_reply_from_context(
            ticket,
            context,
            supplemental_context=supplemental_context,
            source_workflow="multi_agent",
        )
        return {
            "agent_name": self.agent_name,
            "supplemental_context": supplemental_context,
            "reply_suggestion": suggestion.model_dump(mode="json"),
        }

    @staticmethod
    def _build_supplemental_context(*, triage_result: dict, similar_case_result: dict) -> str:
        classification = triage_result.get("classification", {})
        summary_lines = [
            "Triage summary:",
            f"- Category: {classification.get('category', 'unknown')}",
            f"- Priority: {classification.get('priority', 'unknown')}",
            f"- Sentiment: {classification.get('sentiment', 'unknown')}",
            f"- Need human: {classification.get('need_human', True)}",
            f"- Summary: {classification.get('summary', 'N/A')}",
            f"- Recommended department: {classification.get('recommended_department', 'N/A')}",
            "",
            "Historical similar cases:",
        ]

        similar_tickets = similar_case_result.get("similar_tickets", [])
        if not similar_tickets:
            summary_lines.append("- No resolved or closed similar tickets were found.")
        else:
            for item in similar_tickets[:3]:
                summary_lines.append(
                    f"- Ticket #{item['ticket_id']} ({item['title']}) "
                    f"similarity={item['similarity']}: resolution={item['resolution']}"
                )

        historical_summary = similar_case_result.get("historical_summary")
        if historical_summary:
            summary_lines.extend(["", "Historical handling summary:", historical_summary])

        return "\n".join(summary_lines)
