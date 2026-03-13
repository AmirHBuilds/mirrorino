from datetime import datetime

from pydantic import BaseModel, Field


class UserMessageCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=3, max_length=5000)
    is_active: bool = True
    recipient_user_id: int | None = Field(default=None, ge=0)


class UserMessageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    body: str | None = Field(default=None, min_length=3, max_length=5000)
    is_active: bool | None = None
    recipient_user_id: int | None = Field(default=None, ge=0)


class UserMessageResponse(BaseModel):
    id: int
    title: str
    body: str
    is_active: bool
    created_by: int | None
    recipient_user_id: int | None
    recipient_username: str | None
    created_at: datetime
    updated_at: datetime


class UserMessageStatus(UserMessageResponse):
    acknowledged_users: int
    pending_users: int


class ActiveUserMessageResponse(UserMessageResponse):
    acknowledged: bool


class UserMessageAckResponse(BaseModel):
    message_id: int
    acknowledged_at: datetime
