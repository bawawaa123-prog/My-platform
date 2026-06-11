from pydantic import BaseModel, ConfigDict


class AnalyticsOverviewRead(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    urgent_tickets: int
    ai_suggestions_count: int
    ai_approved_count: int
    ai_adoption_rate: float
    category_distribution: dict[str, int]
    priority_distribution: dict[str, int]

    model_config = ConfigDict(extra="forbid")
