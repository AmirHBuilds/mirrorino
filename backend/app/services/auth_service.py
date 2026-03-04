from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.captcha import verify_captcha
from app.config import settings

async def register_user(data: RegisterRequest, db: AsyncSession, redis: aioredis.Redis) -> User:
    if not await verify_captcha(redis, data.captcha_id, data.captcha_answer):
        raise HTTPException(status_code=400, detail="Invalid CAPTCHA.")
    result = await db.execute(select(User).where((User.username == data.username.lower()) | (User.email == data.email.lower())))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already taken")
    user = User(username=data.username.lower(), email=data.email.lower(), password_hash=hash_password(data.password), storage_limit=settings.DEFAULT_STORAGE_LIMIT)
    db.add(user)
    await db.flush()
    return user

async def login_user(data: LoginRequest, db: AsyncSession, redis: aioredis.Redis) -> TokenResponse:
    if not await verify_captcha(redis, data.captcha_id, data.captcha_answer):
        raise HTTPException(status_code=400, detail="Invalid CAPTCHA.")
    result = await db.execute(select(User).where(User.username == data.username.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account is banned")
    token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role.value}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return TokenResponse(access_token=token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
