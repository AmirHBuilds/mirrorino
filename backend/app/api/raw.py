"""
Raw file serving — like raw.githubusercontent.com
Usage: bash <(curl -Ls https://api.mirrorino.com/raw/username/repo-slug/install.sh)
"""
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.rate_limiter import limiter
from app.core.storage import get_file_content
from app.models.user import User
from app.models.repo import Repo
from app.models.file import File

router = APIRouter(tags=["Raw"])

TEXT_MIMES = {"text/x-shellscript","application/x-sh","text/x-python","text/javascript","text/plain","text/markdown","text/xml","application/json","application/xml","text/css","text/html"}
SCRIPT_EXTS = {".sh",".bash",".zsh",".py",".rb",".js",".ts",".json",".yaml",".yml",".toml",".conf",".cfg",".txt",".md",".xml",".env"}

@router.get("/raw/{username}/{repo_slug}/{filename:path}")
@limiter.limit("100/hour")
async def get_raw_file(request: Request, username: str, repo_slug: str, filename: str, db: AsyncSession = Depends(get_db)):
    user_r = await db.execute(select(User).where(User.username == username.lower()))
    user = user_r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    repo_r = await db.execute(select(Repo).where(Repo.owner_id == user.id, Repo.slug == repo_slug, Repo.is_public == True))
    repo = repo_r.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_slug}' not found or is private")

    normalized = filename.strip("/")
    if "/" in normalized:
        directory_path, original_name = normalized.rsplit("/", 1)
    else:
        directory_path, original_name = "", normalized

    file_r = await db.execute(
        select(File).where(
            File.repo_id == repo.id,
            File.original_name == original_name,
            File.directory_path == directory_path,
        )
    )
    file = file_r.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

    content = await get_file_content(file.storage_path)
    file.download_count += 1
    repo.download_count += 1
    await db.commit()

    ext = os.path.splitext(filename)[1].lower()
    if file.detected_type in TEXT_MIMES or ext in SCRIPT_EXTS:
        content_type = "text/plain; charset=utf-8"
    else:
        content_type = file.detected_type or "application/octet-stream"

    return Response(content=content, media_type=content_type, headers={"X-File-Name": file.original_name, "Cache-Control": "public, max-age=300"})
