from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.core.rate_limiter import limiter, upload_limiter, rate_limit_exceeded_handler
from app.db.session import engine
from app.db.base import Base
from app.dependencies import close_redis
from app.api import auth, users, repos, files, ads, admin, raw

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_superadmin()
    yield
    await close_redis()
    await engine.dispose()

async def _seed_superadmin():
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.models.user import User, UserRole
    from app.core.security import hash_password
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == settings.SUPERADMIN_USERNAME))
        if not result.scalar_one_or_none():
            db.add(User(
                username=settings.SUPERADMIN_USERNAME,
                email=settings.SUPERADMIN_EMAIL,
                password_hash=hash_password(settings.SUPERADMIN_PASSWORD),
                role=UserRole.SUPERADMIN,
                storage_limit=settings.VERIFIED_STORAGE_LIMIT * 100,
            ))
            await db.commit()
            print(f"✅ Superadmin '{settings.SUPERADMIN_USERNAME}' created.")

app = FastAPI(
    title="Downloadino API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.state.upload_limiter = upload_limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.add_middleware(CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

PREFIX = "/api"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(users.router, prefix=PREFIX)
app.include_router(repos.router, prefix=PREFIX)
app.include_router(files.router, prefix=PREFIX)
app.include_router(ads.router, prefix=PREFIX)
app.include_router(admin.router, prefix=PREFIX)
app.include_router(raw.router)  # /raw/* — no /api prefix

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
