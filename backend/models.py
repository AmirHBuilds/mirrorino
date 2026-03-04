from sqlalchemy import Column, String, Boolean, BigInteger, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="USER") # USER, ADMIN, SUPERADMIN
    storage_used = Column(BigInteger, default=0)
    storage_limit = Column(BigInteger, default=104857600) # 100 MB in bytes
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Repository(Base):
    __tablename__ = "repositories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    
    owner = relationship("User")

class File(Base):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"))
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    filename = Column(String)
    s3_key = Column(String)
    file_size = Column(BigInteger)
    is_raw = Column(Boolean, default=False)
    status = Column(String, default="APPROVED") # PENDING_REVIEW or APPROVED
    
    repo = relationship("Repository")
    uploader = relationship("User")