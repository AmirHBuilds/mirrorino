from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_admin, hash_password, require_admin_permission
from app.db.session import get_db
from app.models.admin_permission import AdminPermission
from app.models.file import File
from app.models.plan import Plan
from app.models.repo import Repo, VerificationStatus
from app.models.user import User, UserRole
from app.models.user_message import UserMessage, UserMessageAck
from app.schemas.admin import AdminAnalyticsResponse, AdminPermissionsPayload, AdminUserCreate, AdminUserSummary
from app.schemas.repo import AdminRepoUpdate, AdminVerifyAction, RepoResponse
from app.schemas.user import UserAdminUpdate, UserProfile
from app.schemas.user_message import UserMessageCreate, UserMessageResponse, UserMessageStatus, UserMessageUpdate
from app.services.repo_service import delete_repo_and_free_storage, apply_verification_bonus, remove_verification_bonus

router = APIRouter(prefix="/admin", tags=["Admin"])


async def _enrich(repo: Repo, db: AsyncSession) -> dict:
    stats = await db.execute(select(func.count(File.id), func.coalesce(func.sum(File.size_bytes), 0)).where(File.repo_id == repo.id))
    file_count, total_size = stats.one()
    return {
        **repo.__dict__,
        "owner": repo.owner,
        "file_count": file_count,
        "total_size": total_size,
    }


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db), _=Depends(require_admin_permission("view_stats"))):
    return {
        "total_users": (await db.execute(select(func.count(User.id)))).scalar(),
        "total_repos": (await db.execute(select(func.count(Repo.id)))).scalar(),
        "total_files": (await db.execute(select(func.count(File.id)))).scalar(),
        "total_storage_bytes": (await db.execute(select(func.coalesce(func.sum(File.size_bytes), 0)))).scalar(),
        "pending_verifications": (await db.execute(select(func.count(Repo.id)).where(Repo.verification_status == VerificationStatus.PENDING))).scalar(),
        "banned_users": (await db.execute(select(func.count(User.id)).where(User.is_banned == True))).scalar(),
    }


@router.get("/analytics", response_model=AdminAnalyticsResponse)
async def get_analytics(db: AsyncSession = Depends(get_db), _=Depends(require_admin_permission("view_stats"))):
    now = datetime.utcnow()
    start_7d = now - timedelta(days=7)
    prev_7d_start = now - timedelta(days=14)
    start_30d = now - timedelta(days=29)

    def growth(curr: int, prev: int) -> float:
        if prev == 0:
            return 100.0 if curr > 0 else 0.0
        return round(((curr - prev) / prev) * 100, 2)

    users_curr = (await db.execute(select(func.count(User.id)).where(User.created_at >= start_7d))).scalar() or 0
    users_prev = (await db.execute(select(func.count(User.id)).where(User.created_at >= prev_7d_start, User.created_at < start_7d))).scalar() or 0
    repos_curr = (await db.execute(select(func.count(Repo.id)).where(Repo.created_at >= start_7d))).scalar() or 0
    repos_prev = (await db.execute(select(func.count(Repo.id)).where(Repo.created_at >= prev_7d_start, Repo.created_at < start_7d))).scalar() or 0
    files_curr = (await db.execute(select(func.count(File.id)).where(File.uploaded_at >= start_7d))).scalar() or 0
    files_prev = (await db.execute(select(func.count(File.id)).where(File.uploaded_at >= prev_7d_start, File.uploaded_at < start_7d))).scalar() or 0

    totals = {
        "users": (await db.execute(select(func.count(User.id)))).scalar() or 0,
        "repos": (await db.execute(select(func.count(Repo.id)))).scalar() or 0,
        "files": (await db.execute(select(func.count(File.id)))).scalar() or 0,
        "storage_bytes": (await db.execute(select(func.coalesce(func.sum(File.size_bytes), 0)))).scalar() or 0,
        "downloads": (await db.execute(select(func.coalesce(func.sum(Repo.download_count), 0)))).scalar() or 0,
    }

    users_daily = {
        day.date(): cnt
        for day, cnt in (await db.execute(select(func.date(User.created_at), func.count(User.id)).where(User.created_at >= start_30d).group_by(func.date(User.created_at)))).all()
    }
    repos_daily = {
        day.date(): cnt
        for day, cnt in (await db.execute(select(func.date(Repo.created_at), func.count(Repo.id)).where(Repo.created_at >= start_30d).group_by(func.date(Repo.created_at)))).all()
    }
    files_daily = {
        day.date(): cnt
        for day, cnt in (await db.execute(select(func.date(File.uploaded_at), func.count(File.id)).where(File.uploaded_at >= start_30d).group_by(func.date(File.uploaded_at)))).all()
    }

    timeline = []
    cursor = start_30d.date()
    while cursor <= now.date():
        timeline.append(
            {
                "day": cursor.isoformat(),
                "users": users_daily.get(cursor, 0),
                "repos": repos_daily.get(cursor, 0),
                "files": files_daily.get(cursor, 0),
            }
        )
        cursor += timedelta(days=1)

    return {
        "totals": totals,
        "growth": {
            "users_7d": growth(users_curr, users_prev),
            "repos_7d": growth(repos_curr, repos_prev),
            "files_7d": growth(files_curr, files_prev),
            "users_current_7d": users_curr,
            "repos_current_7d": repos_curr,
            "files_current_7d": files_curr,
        },
        "timeline": timeline,
    }


@router.get("/my-permissions", response_model=AdminPermissionsPayload)
async def get_my_permissions(current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    if current_admin.role == UserRole.SUPERADMIN:
        return AdminPermissionsPayload(manage_users=True, manage_repos=True, manage_ads=True, view_stats=True)
    result = await db.execute(select(AdminPermission).where(AdminPermission.user_id == current_admin.id))
    perm = result.scalar_one_or_none()
    if not perm:
        return AdminPermissionsPayload()
    return AdminPermissionsPayload(
        manage_users=perm.manage_users,
        manage_repos=perm.manage_repos,
        manage_ads=perm.manage_ads,
        view_stats=perm.view_stats,
    )


@router.get("/admins", response_model=list[AdminUserSummary])
async def list_admins(db: AsyncSession = Depends(get_db), _=Depends(require_admin_permission("manage_users"))):
    result = await db.execute(select(User).where(User.role.in_([UserRole.ADMIN, UserRole.SUPERADMIN])).order_by(User.created_at.desc()))
    admins = result.scalars().all()
    perm_result = await db.execute(select(AdminPermission))
    perm_map = {p.user_id: p for p in perm_result.scalars().all()}

    output = []
    for admin in admins:
        if admin.role == UserRole.SUPERADMIN:
            permissions = AdminPermissionsPayload(manage_users=True, manage_repos=True, manage_ads=True, view_stats=True)
        else:
            perm = perm_map.get(admin.id)
            permissions = AdminPermissionsPayload(
                manage_users=perm.manage_users if perm else False,
                manage_repos=perm.manage_repos if perm else False,
                manage_ads=perm.manage_ads if perm else False,
                view_stats=perm.view_stats if perm else False,
            )
        output.append(AdminUserSummary(id=admin.id, username=admin.username, email=admin.email, role=admin.role.value, created_at=admin.created_at, permissions=permissions))
    return output


@router.post("/admins", response_model=AdminUserSummary, status_code=201)
async def create_admin(data: AdminUserCreate, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    if current_admin.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmin can create admins")

    existing = await db.execute(select(User).where((User.username == data.username.lower()) | (User.email == data.email.lower())))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username or email already exists")

    admin_user = User(
        username=data.username.lower(),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=UserRole.ADMIN,
    )
    db.add(admin_user)
    await db.flush()

    permissions = AdminPermission(user_id=admin_user.id, **data.permissions.model_dump())
    db.add(permissions)
    await db.flush()

    return AdminUserSummary(
        id=admin_user.id,
        username=admin_user.username,
        email=admin_user.email,
        role=admin_user.role.value,
        created_at=admin_user.created_at,
        permissions=data.permissions,
    )


@router.put("/admins/{user_id}/permissions", response_model=AdminUserSummary)
async def update_admin_permissions(
    user_id: int,
    data: AdminPermissionsPayload,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if current_admin.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmin can update admin permissions")

    user_r = await db.execute(select(User).where(User.id == user_id))
    user = user_r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(status_code=400, detail="Superadmin always has full permissions")
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Target user is not an admin")

    perm_r = await db.execute(select(AdminPermission).where(AdminPermission.user_id == user.id))
    perm = perm_r.scalar_one_or_none()
    if not perm:
        perm = AdminPermission(user_id=user.id)
        db.add(perm)

    for key, value in data.model_dump().items():
        setattr(perm, key, value)

    await db.flush()
    return AdminUserSummary(id=user.id, username=user.username, email=user.email, role=user.role.value, created_at=user.created_at, permissions=data)


@router.get("/verify-queue")
async def get_verify_queue(db: AsyncSession = Depends(get_db), _=Depends(require_admin_permission("manage_repos"))):
    result = await db.execute(select(Repo).where(Repo.verification_status == VerificationStatus.PENDING).order_by(Repo.updated_at.asc()))
    return result.scalars().all()


@router.post("/repos/{repo_id}/verify")
async def verify_repo(repo_id: int, action: AdminVerifyAction, db: AsyncSession = Depends(get_db), _=Depends(require_admin_permission("manage_repos"))):
    if action.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
    result = await db.execute(select(Repo).where(Repo.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    previous_status = repo.verification_status

    if action.action == "approve":
        repo.verification_status = VerificationStatus.VERIFIED
        owner_r = await db.execute(select(User).where(User.id == repo.owner_id))
        owner = owner_r.scalar_one_or_none()
        if owner and previous_status != VerificationStatus.VERIFIED:
            apply_verification_bonus(owner)
    else:
        repo.verification_status = VerificationStatus.REJECTED
        if previous_status == VerificationStatus.VERIFIED:
            owner_r = await db.execute(select(User).where(User.id == repo.owner_id))
            owner = owner_r.scalar_one_or_none()
            if owner:
                remove_verification_bonus(owner)
    repo.verification_note = action.note
    return {"message": f"Repository {action.action}d", "repo_id": repo_id}


@router.get("/repos", response_model=list[RepoResponse])
async def list_repos(
    q: str | None = Query(None),
    owner: str | None = Query(None),
    verification_status: VerificationStatus | None = Query(None),
    is_public: bool | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin_permission("manage_repos")),
):
    query = select(Repo).options(selectinload(Repo.owner)).join(User, Repo.owner_id == User.id)

    if q:
        like = f"%{q}%"
        query = query.where(or_(Repo.name.ilike(like), Repo.slug.ilike(like), Repo.description.ilike(like), User.username.ilike(like)))
    if owner:
        query = query.where(User.username.ilike(f"%{owner}%"))
    if verification_status is not None:
        query = query.where(Repo.verification_status == verification_status)
    if is_public is not None:
        query = query.where(Repo.is_public == is_public)

    result = await db.execute(query.order_by(Repo.updated_at.desc()).offset((page - 1) * limit).limit(limit))
    repos = result.scalars().all()
    return [await _enrich(r, db) for r in repos]


@router.put("/repos/{repo_id}", response_model=RepoResponse)
async def update_repo(
    repo_id: int,
    data: AdminRepoUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin_permission("manage_repos")),
):
    result = await db.execute(select(Repo).options(selectinload(Repo.owner)).where(Repo.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    previous_status = repo.verification_status

    if data.verification_status is not None:
        repo.verification_status = data.verification_status
        owner_r = await db.execute(select(User).where(User.id == repo.owner_id))
        owner = owner_r.scalar_one_or_none()
        if owner and previous_status != VerificationStatus.VERIFIED and data.verification_status == VerificationStatus.VERIFIED:
            apply_verification_bonus(owner)
        if owner and previous_status == VerificationStatus.VERIFIED and data.verification_status != VerificationStatus.VERIFIED:
            remove_verification_bonus(owner)
    if data.verification_note is not None:
        repo.verification_note = data.verification_note
    if data.is_public is not None:
        repo.is_public = data.is_public

    return await _enrich(repo, db)


@router.get("/users", response_model=list[UserProfile])
async def list_users(
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin_permission("manage_users")),
):
    query = select(User)
    if q:
        query = query.where(User.username.ilike(f"%{q}%") | User.email.ilike(f"%{q}%"))
    result = await db.execute(query.offset((page - 1) * limit).limit(limit).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.put("/users/{user_id}", response_model=UserProfile)
async def update_user(
    user_id: int,
    data: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    _=Depends(require_admin_permission("manage_users")),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == UserRole.SUPERADMIN and current_admin.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot modify a superadmin")
    if data.role is not None:
        user.role = data.role
    if data.storage_limit is not None:
        user.storage_limit = data.storage_limit
    if data.is_banned is not None:
        user.is_banned = data.is_banned
    if data.plan_id is not None:
        plan_result = await db.execute(select(Plan).where(Plan.id == data.plan_id, Plan.is_active == True))
        plan = plan_result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=400, detail="Invalid or inactive plan_id")
        user.plan_id = data.plan_id
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    _=Depends(require_admin_permission("manage_users")),
):
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
async def admin_delete_repo(repo_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin_permission("manage_repos"))):
    result = await db.execute(select(Repo).where(Repo.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    owner_r = await db.execute(select(User).where(User.id == repo.owner_id))
    freed = await delete_repo_and_free_storage(repo, owner_r.scalar_one(), db)
    return {"message": "Repository deleted", "storage_freed_bytes": freed}


@router.get("/user-messages", response_model=list[UserMessageStatus])
async def list_user_messages(db: AsyncSession = Depends(get_db), _=Depends(require_admin_permission("manage_users"))):
    total_users = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.USER))).scalar() or 0

    ack_counts_subquery = (
        select(UserMessageAck.message_id.label("message_id"), func.count(UserMessageAck.id).label("acknowledged_users"))
        .join(User, User.id == UserMessageAck.user_id)
        .where(User.role == UserRole.USER)
        .group_by(UserMessageAck.message_id)
        .subquery()
    )

    rows = (
        await db.execute(
            select(
                UserMessage,
                func.coalesce(ack_counts_subquery.c.acknowledged_users, 0).label("acknowledged_users"),
            )
            .outerjoin(ack_counts_subquery, ack_counts_subquery.c.message_id == UserMessage.id)
            .order_by(UserMessage.created_at.desc())
        )
    ).all()

    output: list[UserMessageStatus] = []
    for message, acknowledged_users in rows:
        pending_users = max(0, total_users - acknowledged_users)
        output.append(
            UserMessageStatus(
                id=message.id,
                title=message.title,
                body=message.body,
                is_active=message.is_active,
                created_by=message.created_by,
                created_at=message.created_at,
                updated_at=message.updated_at,
                acknowledged_users=acknowledged_users,
                pending_users=pending_users,
            )
        )
    return output


@router.post("/user-messages", response_model=UserMessageResponse, status_code=201)
async def create_user_message(
    data: UserMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    _=Depends(require_admin_permission("manage_users")),
):
    message = UserMessage(title=data.title.strip(), body=data.body.strip(), is_active=data.is_active, created_by=current_admin.id)
    db.add(message)
    await db.flush()
    return message


@router.put("/user-messages/{message_id}", response_model=UserMessageResponse)
async def update_user_message(
    message_id: int,
    data: UserMessageUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin_permission("manage_users")),
):
    result = await db.execute(select(UserMessage).where(UserMessage.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if data.title is not None:
        message.title = data.title.strip()
    if data.body is not None:
        message.body = data.body.strip()
    if data.is_active is not None:
        message.is_active = data.is_active
    await db.flush()
    return message


@router.delete("/user-messages/{message_id}", status_code=204)
async def delete_user_message(message_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin_permission("manage_users"))):
    result = await db.execute(select(UserMessage).where(UserMessage.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    await db.delete(message)
