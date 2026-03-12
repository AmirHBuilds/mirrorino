from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.file import File
from app.models.directory import Directory
from app.models.repo import Repo
from app.models.user import User
from app.core.file_validator import validate_file
from app.core.storage import save_file, delete_file

def normalize_directory_path(path: str | None) -> str:
    if not path:
        return ""
    parts = [part.strip() for part in path.replace("\\", "/").split("/") if part.strip() and part.strip() not in {".", ".."}]
    return "/".join(parts)


async def ensure_directory_exists(repo_id: int, path: str, db: AsyncSession) -> None:
    normalized = normalize_directory_path(path)
    if not normalized:
        return

    current_parts: list[str] = []
    for part in normalized.split("/"):
        current_parts.append(part)
        current_path = "/".join(current_parts)
        existing = await db.execute(select(Directory).where(Directory.repo_id == repo_id, Directory.path == current_path))
        if not existing.scalar_one_or_none():
            db.add(Directory(repo_id=repo_id, path=current_path))


async def upload_file(upload: UploadFile, repo: Repo, owner: User, db: AsyncSession, directory_path: str = "") -> File:
    content, detected_mime = await validate_file(upload)
    file_size = len(content)
    if owner.storage_used + file_size > owner.storage_limit:
        remaining = owner.storage_limit - owner.storage_used
        raise HTTPException(status_code=413, detail={"code": "QUOTA_EXCEEDED", "message": f"Storage quota exceeded. You have {remaining} bytes remaining.", "storage_remaining": remaining, "storage_limit": owner.storage_limit})
    normalized_directory = normalize_directory_path(directory_path)
    await ensure_directory_exists(repo.id, normalized_directory, db)
    stored_name, storage_path = await save_file(content, upload.filename, repo.id)
    file_record = File(repo_id=repo.id, original_name=upload.filename, directory_path=normalized_directory, stored_name=stored_name, mime_type=upload.content_type or detected_mime, detected_type=detected_mime, size_bytes=file_size, storage_path=storage_path)
    db.add(file_record)
    owner.storage_used += file_size
    await db.flush()
    return file_record

async def delete_file_record(file: File, owner: User, db: AsyncSession) -> None:
    await delete_file(file.storage_path)
    owner.storage_used = max(0, owner.storage_used - file.size_bytes)
    await db.delete(file)
    await db.flush()


async def delete_directory_record(repo_id: int, directory_path: str, owner: User, db: AsyncSession) -> int:
    normalized = normalize_directory_path(directory_path)
    if not normalized:
        raise HTTPException(status_code=400, detail="Directory path is required")

    file_result = await db.execute(
        select(File).where(
            File.repo_id == repo_id,
            (File.directory_path == normalized) | (File.directory_path.startswith(f"{normalized}/")),
        )
    )
    files = file_result.scalars().all()

    freed_bytes = 0
    for file in files:
        await delete_file(file.storage_path)
        freed_bytes += file.size_bytes
        await db.delete(file)

    dir_result = await db.execute(
        select(Directory).where(
            Directory.repo_id == repo_id,
            (Directory.path == normalized) | (Directory.path.startswith(f"{normalized}/")),
        )
    )
    directories = dir_result.scalars().all()
    for directory in directories:
        await db.delete(directory)

    owner.storage_used = max(0, owner.storage_used - freed_bytes)
    await db.flush()
    return freed_bytes
