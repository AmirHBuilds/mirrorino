from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Request, Form
from pydantic import BaseModel
from fastapi.responses import StreamingResponse, RedirectResponse
from starlette.background import BackgroundTask
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import io
import tempfile
import zipfile
from app.db.session import get_db
from app.core.security import get_current_user
from app.core.rate_limiter import limiter, upload_limiter
from app.core.storage import get_file_content, get_presigned_url, update_file_content
from app.models.repo import Repo
from app.models.file import File
from app.models.directory import Directory
from app.models.user import User
from app.schemas.file import FileResponse, FileUploadResult, RepoTreeResponse, DirectoryCreate, DirectoryResponse, RepoTreeDirectory
from app.services.file_service import upload_file, delete_file_record, normalize_directory_path, ensure_directory_exists, delete_directory_record

router = APIRouter(tags=["Files"])


class FileContentUpdate(BaseModel):
    content: str


async def _get_repo_by_identity(db: AsyncSession, username: str, repo_slug: str) -> Repo | None:
    result = await db.execute(
        select(Repo)
        .join(User, Repo.owner_id == User.id)
        .where(User.username == username, Repo.slug == repo_slug)
    )
    return result.scalar_one_or_none()


@router.get("/{username}/{repo_slug}/clone")
@limiter.limit("10/hour")
async def clone_repo_archive(request: Request, username: str, repo_slug: str, db: AsyncSession = Depends(get_db)):
    repo = await _get_repo_by_identity(db, username, repo_slug)
    if not repo or not repo.is_public:
        raise HTTPException(status_code=404, detail="Repository not found")

    files_result = await db.execute(select(File).where(File.repo_id == repo.id).order_by(File.uploaded_at.asc()))
    files = files_result.scalars().all()

    dirs_result = await db.execute(select(Directory.path).where(Directory.repo_id == repo.id))
    all_dirs = dirs_result.scalars().all()

    archive_name = f"{repo.slug}.zip"
    archive_file = tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024, mode="w+b")
    with zipfile.ZipFile(archive_file, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for directory in all_dirs:
            dir_path = directory.strip("/")
            if dir_path:
                zip_file.writestr(f"{dir_path}/", "")

        for file in files:
            file_content = await get_file_content(file.storage_path)
            archive_path = f"{file.directory_path}/{file.original_name}" if file.directory_path else file.original_name
            zip_file.writestr(archive_path, file_content)

    archive_file.seek(0)
    repo.download_count += 1
    repo.clone_count += 1
    await db.commit()

    return StreamingResponse(
        archive_file,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{archive_name}"'},
        background=BackgroundTask(archive_file.close),
    )


@router.get("/users/{username}/repos/{repo_slug}/tree", response_model=RepoTreeResponse)
async def list_repo_tree(username: str, repo_slug: str, path: str = "", db: AsyncSession = Depends(get_db)):
    repo = await _get_repo_by_identity(db, username, repo_slug)
    if not repo or not repo.is_public:
        raise HTTPException(status_code=404, detail="Repository not found")

    normalized = normalize_directory_path(path)
    files_result = await db.execute(select(File).where(File.repo_id == repo.id, File.directory_path == normalized).order_by(File.uploaded_at.desc()))
    files = files_result.scalars().all()

    all_files_result = await db.execute(select(File.directory_path, File.size_bytes).where(File.repo_id == repo.id))
    file_rows = all_files_result.all()

    dirs_result = await db.execute(select(Directory.path).where(Directory.repo_id == repo.id))
    all_dirs = dirs_result.scalars().all()
    prefix = f"{normalized}/" if normalized else ""

    child_paths: set[str] = set()
    for directory in all_dirs:
        if prefix and not directory.startswith(prefix):
            continue
        if not prefix and "/" in directory:
            child_paths.add(directory.split("/", 1)[0])
            continue
        remainder = directory[len(prefix):] if prefix else directory
        if not remainder:
            continue
        child = remainder.split("/", 1)[0]
        if child:
            child_paths.add(f"{prefix}{child}" if prefix else child)

    for directory_path, _ in file_rows:
        if not directory_path:
            continue
        if prefix:
            if not directory_path.startswith(prefix):
                continue
            remainder = directory_path[len(prefix):]
            if not remainder:
                continue
            child = remainder.split("/", 1)[0]
            child_paths.add(f"{prefix}{child}")
        else:
            child_paths.add(directory_path.split("/", 1)[0])

    directory_sizes: dict[str, int] = {path: 0 for path in child_paths}
    for directory_path, size_bytes in file_rows:
        if not directory_path:
            continue
        for child_path in child_paths:
            if directory_path == child_path or directory_path.startswith(f"{child_path}/"):
                directory_sizes[child_path] += size_bytes

    latest_release_version = (repo.latest_release_version or "").strip().strip("/")

    directory_items = [
        RepoTreeDirectory(
            name=path.split("/")[-1],
            path=path,
            size_bytes=directory_sizes[path],
            is_releases_dir=(not normalized and path.lower() == "releases"),
            is_latest_release=bool(normalized.lower() == "releases" and latest_release_version and path.split("/")[-1] == latest_release_version),
        )
        for path in child_paths
    ]

    def sort_key(entry: RepoTreeDirectory):
        if entry.is_releases_dir:
            return (0, entry.name.lower())
        if entry.is_latest_release:
            return (1, entry.name.lower())
        return (2, entry.name.lower())

    directories = sorted(directory_items, key=sort_key)

    return RepoTreeResponse(path=normalized, directories=directories, files=files)


@router.post("/users/{username}/repos/{repo_slug}/directories", response_model=DirectoryResponse, status_code=201)
async def create_repo_directory(
    username: str,
    repo_slug: str,
    payload: DirectoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = await _get_repo_by_identity(db, username, repo_slug)
    if not repo or repo.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")

    normalized = normalize_directory_path(payload.path)
    if not normalized:
        raise HTTPException(status_code=400, detail="Directory path is required")

    await ensure_directory_exists(repo.id, normalized, db)
    await db.flush()
    result = await db.execute(select(Directory).where(Directory.repo_id == repo.id, Directory.path == normalized))
    directory = result.scalar_one_or_none()
    if not directory:
        raise HTTPException(status_code=500, detail="Directory could not be created")
    return directory

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
async def upload_to_repo(request: Request, repo_id: int, file: UploadFile = FastAPIFile(...), directory_path: str = Form(default=""), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Repo).where(Repo.id == repo_id, Repo.owner_id == current_user.id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")
    file_record = await upload_file(file, repo, current_user, db, directory_path=directory_path)
    return FileUploadResult(file=file_record, storage_remaining=current_user.storage_remaining, storage_usage_percent=current_user.storage_usage_percent)


@router.post("/users/{username}/repos/{repo_slug}/files", response_model=FileUploadResult, status_code=201)
@upload_limiter.limit("1000/hour")
async def upload_to_repo_by_identity(
    request: Request,
    username: str,
    repo_slug: str,
    file: UploadFile = FastAPIFile(...),
    directory_path: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = await _get_repo_by_identity(db, username, repo_slug)
    if not repo or repo.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")
    file_record = await upload_file(file, repo, current_user, db, directory_path=directory_path)
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


@router.get("/users/{username}/repos/{repo_slug}/files/{file_id}/download")
@limiter.limit("50/hour")
async def download_file_by_identity(request: Request, username: str, repo_slug: str, file_id: int, db: AsyncSession = Depends(get_db)):
    repo = await _get_repo_by_identity(db, username, repo_slug)
    if not repo or not repo.is_public:
        raise HTTPException(status_code=404, detail="Repository not found")

    result = await db.execute(select(File).where(File.id == file_id, File.repo_id == repo.id))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    file.download_count += 1
    repo.download_count += 1
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


@router.delete("/users/{username}/repos/{repo_slug}/directories")
async def delete_repo_directory(
    username: str,
    repo_slug: str,
    path: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = await _get_repo_by_identity(db, username, repo_slug)
    if not repo or repo.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")

    normalized = normalize_directory_path(path)
    if not normalized:
        raise HTTPException(status_code=400, detail="Directory path is required")

    freed = await delete_directory_record(repo.id, normalized, current_user, db)
    return {"message": "Directory deleted", "storage_freed_bytes": freed, "storage_remaining": current_user.storage_remaining}


@router.put("/files/{file_id}/content")
async def update_file_content_endpoint(
    file_id: int,
    payload: FileContentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    repo_result = await db.execute(select(Repo).where(Repo.id == file.repo_id, Repo.owner_id == current_user.id))
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        content_bytes = payload.content.encode("utf-8")
    except UnicodeEncodeError:
        raise HTTPException(status_code=400, detail="Content must be valid UTF-8 text")

    owner_result = await db.execute(select(User).where(User.id == current_user.id))
    owner = owner_result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    size_delta = len(content_bytes) - file.size_bytes
    if size_delta > 0 and owner.storage_used + size_delta > owner.storage_limit:
        remaining = owner.storage_limit - owner.storage_used
        raise HTTPException(
            status_code=413,
            detail={
                "code": "QUOTA_EXCEEDED",
                "message": f"Storage quota exceeded. You have {remaining} bytes remaining.",
                "storage_remaining": remaining,
                "storage_limit": owner.storage_limit,
            },
        )

    await update_file_content(file.storage_path, content_bytes, file.original_name)
    file.size_bytes = len(content_bytes)
    file.mime_type = "text/plain"
    file.detected_type = "text/plain"
    owner.storage_used = max(0, owner.storage_used + size_delta)
    await db.flush()

    return {
        "message": "File updated",
        "size_bytes": file.size_bytes,
        "storage_remaining": owner.storage_remaining,
        "storage_usage_percent": owner.storage_usage_percent,
    }
