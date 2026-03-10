from datetime import datetime
from pydantic import BaseModel

class AdCreate(BaseModel):
    title: str
    image_url: str
    target_url: str
    position: str = "sidebar"
    description: str | None = None
    is_active: bool = True

class AdUpdate(BaseModel):
    title: str | None = None
    image_url: str | None = None
    target_url: str | None = None
    position: str | None = None
    description: str | None = None
    is_active: bool | None = None

class AdResponse(BaseModel):
    id: int
    title: str
    image_url: str
    target_url: str
    position: str
    description: str | None = None
    is_active: bool
    click_count: int
    created_at: datetime
    model_config = {"from_attributes": True}
