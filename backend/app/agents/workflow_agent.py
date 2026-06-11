from __future__ import annotations

from app.agents.base_agent import BaseTicketAgent


class WorkflowAgent(BaseTicketAgent):
    agent_name = "WorkflowAgent"

    def run(
        self,
        *,
        ticket_id: int,
        triage_result: dict,
        risk_result: dict,
    ) -> dict:
        ticket = self.ticket_service.get_ticket(ticket_id)
        classification = triage_result.get("classification", {})
        risk_check = risk_result.get("risk_check", {})

        assign_to_department = (
            classification.get("recommended_department")
            or ticket.recommended_department
            or "customer_support"
        )
        requires_human_review = risk_check.get("requires_human_review", True)
        risk_level = risk_check.get("risk_level", "medium")
        next_status = "waiting_review"
        next_action = (
            "Queue for human approval before sending any customer-facing reply."
            if requires_human_review
            else "Queue for standard human approval, then hand off to the assigned team for follow-up."
        )
        internal_note = (
            f"Workflow recommendation based on risk={risk_level}, "
            f"priority={classification.get('priority', ticket.priority)}, "
            f"department={assign_to_department}. Ticket remains in waiting_review because AI replies require human approval."
        )

        updated_ticket = self.ticket_service.apply_workflow_recommendation(
            ticket_id=ticket_id,
            next_status=next_status,
            assign_to_department=assign_to_department,
            next_action=next_action,
            internal_note=internal_note,
        )

        return {
            "agent_name": self.agent_name,
            "next_status": next_status,
            "assign_to_department": assign_to_department,
            "next_action": next_action,
            "internal_note": internal_note,
            "updated_ticket": self.ticket_service.serialize_ticket(updated_ticket),
        }
