from datetime import datetime
import re

from pydantic import BaseModel, field_validator

from app.models.repo import VerificationStatus
from app.schemas.user import UserPublic


def _valid_release_version(v: str | None) -> str | None:
    if v is None:
        return None
    value = v.strip().strip("/")
    if not value:
        return None
    if len(value) > 255:
        raise ValueError("Latest release folder name is too long")
    if "/" in value or "\\" in value:
        raise ValueError("Latest release must be a single folder name")
    return value


def _valid_source_url(v: str | None) -> str | None:
    if v is None:
        return None
    value = v.strip()
    if not value:
        return None
    if len(value) > 2000:
        raise ValueError("Source URL is too long")
    if not re.match(r"^https?://", value, re.IGNORECASE):
        raise ValueError("Source URL must start with http:// or https://")
    return value


class RepoCreate(BaseModel):
    name: str
    description: str | None = None
    is_public: bool = True
    is_mirror: bool = False
    source_url: str | None = None

    @field_validator("name")
    @classmethod
    def name_valid(cls, v):
        if not re.match(r"^[a-zA-Z0-9_\-\.]{1,100}$", v):
            raise ValueError("Repo name must be 1-100 chars, letters/numbers/-_. only")
        return v

    @field_validator("source_url")
    @classmethod
    def source_url_valid(cls, v: str | None):
        return _valid_source_url(v)


class RepoUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None
    is_mirror: bool | None = None
    source_url: str | None = None
    latest_release_version: str | None = None

    @field_validator("name")
    @classmethod
    def name_valid(cls, v: str | None):
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9_\-\.]{1,100}$", v):
            raise ValueError("Repo name must be 1-100 chars, letters/numbers/-_. only")
        return v

    @field_validator("source_url")
    @classmethod
    def source_url_valid(cls, v: str | None):
        return _valid_source_url(v)

    @field_validator("latest_release_version")
    @classmethod
    def latest_release_version_valid(cls, v: str | None):
        return _valid_release_version(v)


class RepoResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    is_public: bool
    verification_status: VerificationStatus
    download_count: int
    clone_count: int
    is_mirror: bool
    source_url: str | None
    latest_release_version: str | None
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
