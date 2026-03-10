from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AdminPermissionsPayload(BaseModel):
    manage_users: bool = False
    manage_repos: bool = False
    manage_ads: bool = False
    view_stats: bool = True


class AdminUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    permissions: AdminPermissionsPayload


class AdminUserSummary(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime
    permissions: AdminPermissionsPayload


class AdminAnalyticsPoint(BaseModel):
    day: str
    users: int
    repos: int
    files: int


class AdminAnalyticsResponse(BaseModel):
    totals: dict
    growth: dict
    timeline: list[AdminAnalyticsPoint]
