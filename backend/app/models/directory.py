from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Directory(Base):
    __tablename__ = "directories"
    __table_args__ = (UniqueConstraint("repo_id", "path", name="uq_directories_repo_id_path"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_id: Mapped[int] = mapped_column(Integer, ForeignKey("repos.id", ondelete="CASCADE"), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
