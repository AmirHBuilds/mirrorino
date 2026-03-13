import re
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.repo import Repo, VerificationStatus
from app.models.file import File
from app.models.user import User
from app.schemas.repo import RepoCreate
from app.config import settings

def _slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9\-_]", "-", slug)
    return re.sub(r"-+", "-", slug).strip("-")


def apply_verification_bonus(owner: User) -> None:
    owner.storage_limit += settings.VERIFICATION_BONUS_BYTES


def remove_verification_bonus(owner: User) -> None:
    owner.storage_limit = max(0, owner.storage_limit - settings.VERIFICATION_BONUS_BYTES)

async def create_repo(data: RepoCreate, owner: User, db: AsyncSession) -> Repo:
    slug = _slugify(data.name)
    result = await db.execute(select(Repo).where(Repo.owner_id == owner.id, Repo.slug == slug))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You already have a repo with this name")
    repo = Repo(
        owner_id=owner.id,
        name=data.name,
        slug=slug,
        description=data.description,
        is_public=data.is_public,
        is_mirror=data.is_mirror,
        source_url=data.source_url if data.is_mirror else None,
    )
    db.add(repo)
    await db.flush()
    return repo

async def delete_repo_and_free_storage(repo: Repo, owner: User, db: AsyncSession) -> int:
    from app.core.storage import delete_file as storage_delete
    result = await db.execute(select(File).where(File.repo_id == repo.id))
    files = result.scalars().all()
    total_freed = sum(f.size_bytes for f in files)
    for f in files:
        await storage_delete(f.storage_path)
    await db.delete(repo)
    await db.flush()
    owner.storage_used = max(0, owner.storage_used - total_freed)
    if repo.verification_status == VerificationStatus.VERIFIED:
        remove_verification_bonus(owner)
    return total_freed


async def rename_repo(repo: Repo, new_name: str, db: AsyncSession) -> None:
    slug = _slugify(new_name)
    result = await db.execute(
        select(Repo).where(Repo.owner_id == repo.owner_id, Repo.slug == slug, Repo.id != repo.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You already have a repo with this name")
    repo.name = new_name
    repo.slug = slug
