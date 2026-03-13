from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserMessage(Base):
    __tablename__ = "user_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    acknowledgements = relationship("UserMessageAck", back_populates="message", cascade="all, delete-orphan", lazy="dynamic")


class UserMessageAck(Base):
    __tablename__ = "user_message_acks"
    __table_args__ = (UniqueConstraint("message_id", "user_id", name="uq_user_message_ack_message_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    message = relationship("UserMessage", back_populates="acknowledgements")
