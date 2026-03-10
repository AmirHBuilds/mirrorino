from sqlalchemy import Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AdminPermission(Base):
    __tablename__ = "admin_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    manage_users: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manage_repos: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manage_ads: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_stats: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", lazy="selectin")
