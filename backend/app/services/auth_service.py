from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.config import settings
from app.core.captcha import verify_captcha
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


def _refresh_ttl_seconds() -> int:
    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


async def _store_refresh_jti(redis: aioredis.Redis, user_id: int, jti: str) -> None:
    await redis.setex(f"auth:refresh:{user_id}:{jti}", _refresh_ttl_seconds(), b"1")


async def _revoke_refresh_jti(redis: aioredis.Redis, user_id: int, jti: str) -> None:
    await redis.delete(f"auth:refresh:{user_id}:{jti}")


async def register_user(data: RegisterRequest, db: AsyncSession, redis: aioredis.Redis) -> User:
    if not await verify_captcha(redis, data.captcha_id, data.captcha_answer):
        raise HTTPException(status_code=400, detail="Invalid CAPTCHA.")

    result = await db.execute(
        select(User).where((User.username == data.username.lower()) | (User.email == data.email.lower()))
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already taken")

    user = User(
        username=data.username.lower(),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        storage_limit=settings.DEFAULT_STORAGE_LIMIT,
    )
    db.add(user)
    await db.flush()
    return user


async def login_user(
    data: LoginRequest,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> tuple[TokenResponse, str]:
    if not await verify_captcha(redis, data.captcha_id, data.captcha_answer):
        raise HTTPException(status_code=400, detail="Invalid CAPTCHA.")

    result = await db.execute(select(User).where(User.username == data.username.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account is banned")

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token, refresh_jti = create_refresh_token(user_id=user.id)
    await _store_refresh_jti(redis, user.id, refresh_jti)

    return TokenResponse(access_token=access_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60), refresh_token


async def refresh_access_token(refresh_token: str, db: AsyncSession, redis: aioredis.Redis) -> tuple[TokenResponse, str]:
    payload = decode_refresh_token(refresh_token)
    user_id_raw = payload.get("sub")
    jti = payload.get("jti")
    if not user_id_raw or not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    key = f"auth:refresh:{user_id}:{jti}"
    if not await redis.exists(key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is no longer valid")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.is_banned:
        await _revoke_refresh_jti(redis, user_id, jti)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is banned")

    await _revoke_refresh_jti(redis, user_id, jti)
    next_refresh_token, next_refresh_jti = create_refresh_token(user_id=user.id)
    await _store_refresh_jti(redis, user.id, next_refresh_jti)

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(access_token=access_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60), next_refresh_token


async def logout_user(refresh_token: str | None, redis: aioredis.Redis) -> None:
    if not refresh_token:
        return
    try:
        payload = decode_refresh_token(refresh_token)
    except HTTPException:
        return

    user_id = payload.get("sub")
    jti = payload.get("jti")
    if not user_id or not jti:
        return

    await _revoke_refresh_jti(redis, int(user_id), jti)
