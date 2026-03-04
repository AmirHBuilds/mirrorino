from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class UserPublic(BaseModel):
    id: int
    username: str
    role: UserRole
    created_at: datetime
    model_config = {"from_attributes": True}

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_banned: bool
    storage_used: int
    storage_limit: int
    storage_remaining: int
    storage_usage_percent: float
    created_at: datetime
    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None

class UserAdminUpdate(BaseModel):
    role: UserRole | None = None
    storage_limit: int | None = None
    is_banned: bool | None = None
    plan_id: int | None = None

class StorageInfo(BaseModel):
    storage_used: int
    storage_limit: int
    storage_remaining: int
    storage_usage_percent: float
