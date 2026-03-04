import enum
from datetime import datetime
from sqlalchemy import String, Boolean, BigInteger, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class UserRole(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    storage_used: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    storage_limit: Mapped[int] = mapped_column(BigInteger, default=104_857_600, nullable=False)
    plan_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("plans.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    plan = relationship("Plan", back_populates="users", lazy="selectin")
    repos = relationship("Repo", back_populates="owner", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def storage_remaining(self) -> int:
        return max(0, self.storage_limit - self.storage_used)

    @property
    def storage_usage_percent(self) -> float:
        if self.storage_limit == 0:
            return 100.0
        return round((self.storage_used / self.storage_limit) * 100, 2)

    @property
    def is_admin_or_above(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.SUPERADMIN)
