from datetime import datetime
from pydantic import BaseModel

class FileResponse(BaseModel):
    id: int
    original_name: str
    stored_name: str
    mime_type: str
    detected_type: str
    size_bytes: int
    download_count: int
    uploaded_at: datetime
    model_config = {"from_attributes": True}

class FileUploadResult(BaseModel):
    file: FileResponse
    storage_remaining: int
    storage_usage_percent: float
