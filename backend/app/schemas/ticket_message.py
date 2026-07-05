from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.utils.datetime_utils import UTCDatetime


MessageSenderType = Literal["customer", "agent", "ai", "system"]


class TicketMessageCreate(BaseModel):
    sender_type: MessageSenderType = "agent"
    content: str = Field(min_length=1)


class TicketMessageRead(BaseModel):
    id: int
    ticket_id: int
    sender_type: str
    sender_name: str
    content: str
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)
