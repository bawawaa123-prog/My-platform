from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentAuditTrailItemRead(BaseModel):
    agent_name: str
    action: str
    input_summary: str
    output_summary: str
    status: str
    timestamp: str


class AgentRunLogRead(BaseModel):
    id: int
    ticket_id: int
    run_id: str
    run_type: str
    status: str
    input_json: dict
    output_json: dict
    audit_trail_json: list[AgentAuditTrailItemRead]
    error_message: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
