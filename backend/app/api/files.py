from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Request
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import io
from app.db.session import get_db
from app.core.security import get_current_user
from app.core.rate_limiter import limiter, upload_limiter
from app.core.storage import get_file_content, get_presigned_url
from app.models.repo import Repo
from app.models.file import File
from app.models.user import User
from app.schemas.file import FileResponse, FileUploadResult
from app.services.file_service import upload_file, delete_file_record

router = APIRouter(tags=["Files"])


async def _get_repo_by_identity(db: AsyncSession, username: str, repo_slug: str) -> Repo | None:
    result = await db.execute(
        select(Repo)
        .join(User, Repo.owner_id == User.id)
        .where(User.username == username, Repo.slug == repo_slug)
    )
    return result.scalar_one_or_none()

@router.get("/repos/{repo_id}/files", response_model=list[FileResponse])
async def list_repo_files(repo_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repo).where(Repo.id == repo_id, Repo.is_public == True))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")
    result = await db.execute(select(File).where(File.repo_id == repo_id).order_by(File.uploaded_at.desc()))
    return result.scalars().all()


@router.get("/users/{username}/repos/{repo_slug}/files", response_model=list[FileResponse])
async def list_repo_files_by_identity(username: str, repo_slug: str, db: AsyncSession = Depends(get_db)):
    repo = await _get_repo_by_identity(db, username, repo_slug)
    if not repo or not repo.is_public:
        raise HTTPException(status_code=404, detail="Repository not found")
    result = await db.execute(select(File).where(File.repo_id == repo.id).order_by(File.uploaded_at.desc()))
    return result.scalars().all()

@router.post("/repos/{repo_id}/files", response_model=FileUploadResult, status_code=201)
@upload_limiter.limit("10/hour")
async def upload_to_repo(request: Request, repo_id: int, file: UploadFile = FastAPIFile(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Repo).where(Repo.id == repo_id, Repo.owner_id == current_user.id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")
    file_record = await upload_file(file, repo, current_user, db)
    return FileUploadResult(file=file_record, storage_remaining=current_user.storage_remaining, storage_usage_percent=current_user.storage_usage_percent)


@router.post("/users/{username}/repos/{repo_slug}/files", response_model=FileUploadResult, status_code=201)
@upload_limiter.limit("10/hour")
async def upload_to_repo_by_identity(
    request: Request,
    username: str,
    repo_slug: str,
    file: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = await _get_repo_by_identity(db, username, repo_slug)
    if not repo or repo.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")
    file_record = await upload_file(file, repo, current_user, db)
    return FileUploadResult(file=file_record, storage_remaining=current_user.storage_remaining, storage_usage_percent=current_user.storage_usage_percent)

@router.get("/files/{file_id}/download")
@limiter.limit("50/hour")
async def download_file(request: Request, file_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    repo_result = await db.execute(select(Repo).where(Repo.id == file.repo_id, Repo.is_public == True))
    if not repo_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied")
    file.download_count += 1
    presigned = await get_presigned_url(file.storage_path, file.original_name)
    if presigned:
        return RedirectResponse(url=presigned)
    content = await get_file_content(file.storage_path)
    return StreamingResponse(io.BytesIO(content), media_type=file.mime_type, headers={"Content-Disposition": f'attachment; filename="{file.original_name}"'})

@router.delete("/files/{file_id}")
async def delete_file_endpoint(file_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    repo_result = await db.execute(select(Repo).where(Repo.id == file.repo_id, Repo.owner_id == current_user.id))
    if not repo_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied")
    freed = file.size_bytes
    await delete_file_record(file, current_user, db)
    return {"message": "File deleted", "storage_freed_bytes": freed, "storage_remaining": current_user.storage_remaining}
