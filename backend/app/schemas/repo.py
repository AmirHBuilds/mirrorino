from datetime import datetime
from pydantic import BaseModel, field_validator
from app.models.repo import VerificationStatus
from app.schemas.user import UserPublic
import re

class RepoCreate(BaseModel):
    name: str
    description: str | None = None
    is_public: bool = True

    @field_validator("name")
    @classmethod
    def name_valid(cls, v):
        if not re.match(r"^[a-zA-Z0-9_\-\.]{1,100}$", v):
            raise ValueError("Repo name must be 1-100 chars, letters/numbers/-_. only")
        return v

class RepoUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None

    @field_validator("name")
    @classmethod
    def name_valid(cls, v: str | None):
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9_\-\.]{1,100}$", v):
            raise ValueError("Repo name must be 1-100 chars, letters/numbers/-_. only")
        return v

class RepoResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    is_public: bool
    verification_status: VerificationStatus
    download_count: int
    clone_count: int
    owner: UserPublic
    file_count: int = 0
    total_size: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class RepoVerifyRequest(BaseModel):
    note: str | None = None

class AdminVerifyAction(BaseModel):
    action: str
    note: str | None = None


class AdminRepoUpdate(BaseModel):
    verification_status: VerificationStatus | None = None
    verification_note: str | None = None
    is_public: bool | None = None
