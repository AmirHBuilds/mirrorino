from datetime import datetime
from pydantic import BaseModel

class FileResponse(BaseModel):
    id: int
    original_name: str
    directory_path: str
    stored_name: str
    mime_type: str
    detected_type: str
    size_bytes: int
    download_count: int
    uploaded_at: datetime
    model_config = {"from_attributes": True}


class DirectoryCreate(BaseModel):
    path: str


class DirectoryResponse(BaseModel):
    id: int
    path: str
    created_at: datetime
    model_config = {"from_attributes": True}


class RepoTreeDirectory(BaseModel):
    name: str
    path: str
    size_bytes: int
    is_releases_dir: bool = False
    is_latest_release: bool = False


class RepoTreeResponse(BaseModel):
    path: str
    directories: list[RepoTreeDirectory]
    files: list[FileResponse]

class FileUploadResult(BaseModel):
    file: FileResponse
    storage_remaining: int
    storage_usage_percent: float
