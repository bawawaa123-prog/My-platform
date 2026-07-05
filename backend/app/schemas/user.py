from pydantic import BaseModel, ConfigDict, EmailStr

from app.utils.datetime_utils import UTCDatetime


class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: str
    is_active: bool
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)
