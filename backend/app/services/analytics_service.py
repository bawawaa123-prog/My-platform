from __future__ import annotations

from collections import Counter

from sqlalchemy.orm import Session

from app.models.ai_suggestion import AISuggestion
from app.models.ticket import Ticket

TICKET_CATEGORY_ORDER = (
    "payment",
    "account",
    "product",
    "refund",
    "invoice",
    "technical",
    "hr",
    "it",
    "other",
)

TICKET_PRIORITY_ORDER = ("low", "medium", "high", "urgent")


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_overview(self) -> dict:
        tickets = list(self.db.query(Ticket).all())
        suggestions = list(self.db.query(AISuggestion).all())

        total_tickets = len(tickets)
        open_tickets = sum(1 for ticket in tickets if ticket.status in {"open", "ai_processing", "waiting_review", "in_progress"})
        resolved_tickets = sum(1 for ticket in tickets if ticket.status in {"resolved", "closed"})
        urgent_tickets = sum(1 for ticket in tickets if ticket.priority == "urgent")
        ai_suggestions_count = len(suggestions)
        ai_approved_count = sum(1 for suggestion in suggestions if suggestion.status in {"approved", "edited"})
        ai_adoption_rate = round((ai_approved_count / ai_suggestions_count), 4) if ai_suggestions_count else 0.0

        category_counts = Counter(ticket.category for ticket in tickets)
        priority_counts = Counter(ticket.priority for ticket in tickets)

        category_distribution = {
            category: category_counts.get(category, 0) for category in TICKET_CATEGORY_ORDER
        }
        priority_distribution = {
            priority: priority_counts.get(priority, 0) for priority in TICKET_PRIORITY_ORDER
        }

        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "resolved_tickets": resolved_tickets,
            "urgent_tickets": urgent_tickets,
            "ai_suggestions_count": ai_suggestions_count,
            "ai_approved_count": ai_approved_count,
            "ai_adoption_rate": ai_adoption_rate,
            "category_distribution": category_distribution,
            "priority_distribution": priority_distribution,
        }
