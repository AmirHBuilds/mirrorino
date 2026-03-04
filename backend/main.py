# backend/main.py
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

from config import settings  # <--- Import settings
from database import engine, Base
from routers import auth_router, users_router, repos_router, files_router, admin_router, public_router

Base.metadata.create_all(bind=engine)

# Use settings.REDIS_URL securely
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

app = FastAPI(title="Downloadino API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(repos_router.router)
app.include_router(files_router.router)
app.include_router(admin_router.router)
app.include_router(public_router.router)

@app.get("/")
def health_check():
    return {"status": "ok", "system": "Downloadino Backend Online"}