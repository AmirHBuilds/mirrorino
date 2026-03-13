from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.security import get_current_user, hash_password
from app.models.user import User
from app.models.user_message import UserMessage, UserMessageAck
from app.schemas.user import UserProfile, UserUpdate, StorageInfo
from app.schemas.user_message import ActiveUserMessageResponse, UserMessageAckResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserProfile)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/me/storage", response_model=StorageInfo)
async def get_my_storage(current_user: User = Depends(get_current_user)):
    return StorageInfo(storage_used=current_user.storage_used, storage_limit=current_user.storage_limit, storage_remaining=current_user.storage_remaining, storage_usage_percent=current_user.storage_usage_percent)

@router.put("/me", response_model=UserProfile)
async def update_profile(data: UserUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.email:
        r = await db.execute(select(User).where(User.email == data.email.lower(), User.id != current_user.id))
        if r.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already in use")
        current_user.email = data.email.lower()
    if data.password:
        if len(data.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        current_user.password_hash = hash_password(data.password)
    return current_user

@router.delete("/me", status_code=204)
async def delete_my_account(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from sqlalchemy import select as sa_select
    from app.models.repo import Repo
    from app.services.repo_service import delete_repo_and_free_storage
    result = await db.execute(sa_select(Repo).where(Repo.owner_id == current_user.id))
    for repo in result.scalars().all():
        await delete_repo_and_free_storage(repo, current_user, db)
    await db.delete(current_user)


@router.get("/me/messages", response_model=list[ActiveUserMessageResponse])
async def get_my_messages(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = (
        await db.execute(
            select(UserMessage)
            .where(UserMessage.is_active == True)
            .order_by(UserMessage.created_at.desc())
        )
    ).scalars().all()

    acked_ids = set(
        (
            await db.execute(
                select(UserMessageAck.message_id).where(UserMessageAck.user_id == current_user.id)
            )
        ).scalars().all()
    )

    return [
        ActiveUserMessageResponse(
            id=message.id,
            title=message.title,
            body=message.body,
            is_active=message.is_active,
            created_by=message.created_by,
            created_at=message.created_at,
            updated_at=message.updated_at,
            acknowledged=message.id in acked_ids,
        )
        for message in messages
    ]


@router.post("/me/messages/{message_id}/acknowledge", response_model=UserMessageAckResponse)
async def acknowledge_message(message_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    message = (await db.execute(select(UserMessage).where(UserMessage.id == message_id, UserMessage.is_active == True))).scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    ack = (
        await db.execute(
            select(UserMessageAck).where(UserMessageAck.message_id == message_id, UserMessageAck.user_id == current_user.id)
        )
    ).scalar_one_or_none()
    if not ack:
        ack = UserMessageAck(message_id=message_id, user_id=current_user.id)
        db.add(ack)
        await db.flush()

    return UserMessageAckResponse(message_id=ack.message_id, acknowledged_at=ack.acknowledged_at)
