from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.config import settings
from app.core.captcha import generate_captcha
from app.core.rate_limiter import limiter
from app.db.session import get_db
from app.dependencies import get_redis
from app.schemas.auth import CaptchaResponse, LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserProfile
from app.services.auth_service import login_user, logout_user, refresh_access_token, register_user

router = APIRouter(prefix="/auth", tags=["Auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        expires=expires_at,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/auth",
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


@router.get("/captcha", response_model=CaptchaResponse)
async def get_captcha(redis: aioredis.Redis = Depends(get_redis)):
    return await generate_captcha(redis)


@router.post("/register", response_model=UserProfile, status_code=201)
@limiter.limit("10/hour")
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    return await register_user(data, db, redis)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/hour")
async def login(
    request: Request,
    response: Response,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    token_response, refresh_token = await login_user(data, db, redis)
    _set_refresh_cookie(response, refresh_token)
    return token_response


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/hour")
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    refresh_token_cookie = request.cookies.get(REFRESH_COOKIE_NAME)
    token_response, next_refresh_token = await refresh_access_token(refresh_token_cookie or "", db, redis)
    _set_refresh_cookie(response, next_refresh_token)
    return token_response


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, redis: aioredis.Redis = Depends(get_redis)) -> Response:
    await logout_user(request.cookies.get(REFRESH_COOKIE_NAME), redis)
    _clear_refresh_cookie(response)
    return response
