from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.ticket import Ticket
from app.schemas.ai import AIReplyDraftRead


class RiskCheckResult(BaseModel):
    risk_level: str = Field(pattern="^(low|medium|high)$")
    requires_human_review: bool
    reasons: list[str]


class RiskService:
    def evaluate_ticket_reply(
        self,
        *,
        ticket: Ticket,
        reply_suggestion: AIReplyDraftRead,
    ) -> RiskCheckResult:
        reasons: list[str] = []

        text = f"{ticket.title}\n{ticket.content}".lower()
        if ticket.priority in {"high", "urgent"}:
            reasons.append("High-priority ticket requires manual attention.")
        if ticket.sentiment == "angry":
            reasons.append("Customer sentiment is angry.")
        if ticket.category in {"payment", "refund", "invoice"}:
            reasons.append("Ticket category involves financial or refund risk.")
        if reply_suggestion.confidence < 0.35:
            reasons.append("Reply confidence is low.")
        if any(keyword in text for keyword in ["privacy", "gdpr", "legal", "lawsuit", "投诉", "赔偿"]):
            reasons.append("Potential legal or privacy sensitivity detected.")

        requires_human_review = bool(reasons)
        risk_level = "low"
        if len(reasons) >= 3:
            risk_level = "high"
        elif len(reasons) >= 1:
            risk_level = "medium"

        return RiskCheckResult(
            risk_level=risk_level,
            requires_human_review=requires_human_review,
            reasons=reasons,
        )
