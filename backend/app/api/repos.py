from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.repo import Repo, VerificationStatus
from app.models.file import File
from app.models.user import User
from app.schemas.repo import RepoCreate, RepoUpdate, RepoResponse, RepoVerifyRequest
from app.services.repo_service import create_repo, delete_repo_and_free_storage, rename_repo

router = APIRouter(prefix="/repos", tags=["Repositories"])

async def _enrich(repo: Repo, db: AsyncSession) -> dict:
    stats = await db.execute(select(func.count(File.id), func.coalesce(func.sum(File.size_bytes), 0)).where(File.repo_id == repo.id))
    file_count, total_size = stats.one()
    return {
        **repo.__dict__,
        "owner": repo.owner,
        "file_count": file_count,
        "total_size": total_size,
    }

@router.get("/", response_model=list[RepoResponse])
async def list_public_repos(
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("recent"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Repo).options(selectinload(Repo.owner)).join(User, Repo.owner_id == User.id).where(Repo.is_public == True)
    if q:
        like = f"%{q}%"
        query = query.where(
            or_(
                Repo.name.ilike(like),
                Repo.slug.ilike(like),
                Repo.description.ilike(like),
                User.username.ilike(like),
            )
        )
    if sort == "downloads":
        order = Repo.download_count.desc()
    elif sort == "clones":
        order = Repo.clone_count.desc()
    else:
        order = Repo.created_at.desc()
    result = await db.execute(query.offset((page - 1) * limit).limit(limit).order_by(order))
    return [await _enrich(r, db) for r in result.scalars().all()]

@router.post("/", response_model=RepoResponse, status_code=201)
async def create_new_repo(data: RepoCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    data.is_public = True
    if data.is_mirror and not data.source_url:
        raise HTTPException(status_code=400, detail="Mirror repositories must include a source URL")
    if not data.is_mirror:
        data.source_url = None
    repo = await create_repo(data, current_user, db)
    return await _enrich(repo, db)

@router.get("/mine", response_model=list[RepoResponse])
async def list_my_repos(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Repo)
        .options(selectinload(Repo.owner))
        .where(Repo.owner_id == current_user.id)
        .order_by(Repo.created_at.desc())
    )
    return [await _enrich(r, db) for r in result.scalars().all()]


@router.get("/users/{username}", response_model=list[RepoResponse])
async def list_user_public_repos(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Repo)
        .options(selectinload(Repo.owner))
        .join(User, Repo.owner_id == User.id)
        .where(User.username == username, Repo.is_public == True)
        .order_by(Repo.created_at.desc())
    )
    return [await _enrich(r, db) for r in result.scalars().all()]


@router.get("/users/{username}/{repo_slug}", response_model=RepoResponse)
async def get_repo_by_identity(username: str, repo_slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Repo)
        .options(selectinload(Repo.owner))
        .join(User, Repo.owner_id == User.id)
        .where(User.username == username, Repo.slug == repo_slug, Repo.is_public == True)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return await _enrich(repo, db)

@router.get("/{repo_id}", response_model=RepoResponse)
async def get_repo(repo_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repo).options(selectinload(Repo.owner)).where(Repo.id == repo_id, Repo.is_public == True))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return await _enrich(repo, db)

@router.put("/{repo_id}", response_model=RepoResponse)
async def update_repo(repo_id: int, data: RepoUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Repo).options(selectinload(Repo.owner)).where(Repo.id == repo_id, Repo.owner_id == current_user.id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")
    if "name" in data.model_fields_set and data.name is not None and data.name != repo.name:
        await rename_repo(repo, data.name, db)
    if "description" in data.model_fields_set:
        repo.description = data.description
    if data.is_public is not None and data.is_public is False:
        raise HTTPException(status_code=400, detail="Private repositories are only available via support")
    if data.is_public is not None:
        repo.is_public = True

    if "is_mirror" in data.model_fields_set and data.is_mirror is not None:
        repo.is_mirror = data.is_mirror
        if not repo.is_mirror:
            repo.source_url = None

    if "source_url" in data.model_fields_set:
        repo.source_url = data.source_url if repo.is_mirror else None

    if repo.is_mirror and not repo.source_url:
        raise HTTPException(status_code=400, detail="Mirror repositories must include a source URL")

    return await _enrich(repo, db)

@router.delete("/{repo_id}")
async def delete_repo(repo_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Repo).where(Repo.id == repo_id, Repo.owner_id == current_user.id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")
    freed = await delete_repo_and_free_storage(repo, current_user, db)
    return {"message": "Repository deleted", "storage_freed_bytes": freed, "storage_remaining": current_user.storage_remaining}

@router.post("/{repo_id}/request-verification")
async def request_verification(repo_id: int, data: RepoVerifyRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Repo).where(Repo.id == repo_id, Repo.owner_id == current_user.id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")
    if repo.verification_status == VerificationStatus.VERIFIED:
        raise HTTPException(status_code=400, detail="Already verified")
    if repo.verification_status == VerificationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Verification already pending")
    repo.verification_status = VerificationStatus.PENDING
    repo.verification_note = data.note
    return {"message": "Verification request submitted"}
