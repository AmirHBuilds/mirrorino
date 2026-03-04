from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from app.db.session import get_db
from app.core.captcha import generate_captcha
from app.core.rate_limiter import limiter
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, CaptchaResponse
from app.schemas.user import UserProfile
from app.services.auth_service import register_user, login_user
from app.dependencies import get_redis

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/captcha", response_model=CaptchaResponse)
async def get_captcha(redis: aioredis.Redis = Depends(get_redis)):
    return await generate_captcha(redis)

@router.post("/register", response_model=UserProfile, status_code=201)
@limiter.limit("10/hour")
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db), redis: aioredis.Redis = Depends(get_redis)):
    return await register_user(data, db, redis)

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/hour")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db), redis: aioredis.Redis = Depends(get_redis)):
    return await login_user(data, db, redis)
