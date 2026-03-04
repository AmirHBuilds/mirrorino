from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.user import User, UserRole
from app.models.repo import Repo, VerificationStatus
from app.models.file import File
from app.models.ad import Ad
from app.schemas.user import UserProfile, UserAdminUpdate
from app.schemas.repo import AdminVerifyAction
from app.services.repo_service import delete_repo_and_free_storage

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return {
        "total_users": (await db.execute(select(func.count(User.id)))).scalar(),
        "total_repos": (await db.execute(select(func.count(Repo.id)))).scalar(),
        "total_files": (await db.execute(select(func.count(File.id)))).scalar(),
        "total_storage_bytes": (await db.execute(select(func.coalesce(func.sum(File.size_bytes), 0)))).scalar(),
        "pending_verifications": (await db.execute(select(func.count(Repo.id)).where(Repo.verification_status == VerificationStatus.PENDING))).scalar(),
        "banned_users": (await db.execute(select(func.count(User.id)).where(User.is_banned == True))).scalar(),
    }

@router.get("/verify-queue")
async def get_verify_queue(db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    result = await db.execute(select(Repo).where(Repo.verification_status == VerificationStatus.PENDING).order_by(Repo.updated_at.asc()))
    return result.scalars().all()

@router.post("/repos/{repo_id}/verify")
async def verify_repo(repo_id: int, action: AdminVerifyAction, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    if action.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
    result = await db.execute(select(Repo).where(Repo.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if action.action == "approve":
        repo.verification_status = VerificationStatus.VERIFIED
        owner_r = await db.execute(select(User).where(User.id == repo.owner_id))
        owner = owner_r.scalar_one_or_none()
        if owner:
            from app.config import settings
            owner.storage_limit = max(owner.storage_limit, settings.VERIFIED_STORAGE_LIMIT)
    else:
        repo.verification_status = VerificationStatus.REJECTED
    repo.verification_note = action.note
    return {"message": f"Repository {action.action}d", "repo_id": repo_id}

@router.get("/users", response_model=list[UserProfile])
async def list_users(q: str | None = Query(None), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    query = select(User)
    if q:
        query = query.where(User.username.ilike(f"%{q}%") | User.email.ilike(f"%{q}%"))
    result = await db.execute(query.offset((page - 1) * limit).limit(limit).order_by(User.created_at.desc()))
    return result.scalars().all()

@router.put("/users/{user_id}", response_model=UserProfile)
async def update_user(user_id: int, data: UserAdminUpdate, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == UserRole.SUPERADMIN and current_admin.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot modify a superadmin")
    if data.role is not None: user.role = data.role
    if data.storage_limit is not None: user.storage_limit = data.storage_limit
    if data.is_banned is not None: user.is_banned = data.is_banned
    if data.plan_id is not None: user.plan_id = data.plan_id
    return user

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete a superadmin")
    repos_r = await db.execute(select(Repo).where(Repo.owner_id == user_id))
    for repo in repos_r.scalars().all():
        await delete_repo_and_free_storage(repo, user, db)
    await db.delete(user)
    return {"message": "User deleted"}

@router.delete("/repos/{repo_id}")
async def admin_delete_repo(repo_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    result = await db.execute(select(Repo).where(Repo.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    owner_r = await db.execute(select(User).where(User.id == repo.owner_id))
    freed = await delete_repo_and_free_storage(repo, owner_r.scalar_one(), db)
    return {"message": "Repository deleted", "storage_freed_bytes": freed}
