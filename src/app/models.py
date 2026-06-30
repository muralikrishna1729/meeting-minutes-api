import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass

class User(Base):
    __tablename__ = 'users'
    id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4)
    email : Mapped[str] = mapped_column(String(255), unique=True, nullable=False,index = True)
    hashed_password : Mapped[str] = mapped_column(String(255), nullable=False)
    role : Mapped[str] = mapped_column(String(50), nullable=False, default='user')
    is_active : Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True),default=func.now(), nullable=False)


class MeetingMinutes(Base):
    __tablename__ = 'meeting_minutes'
    id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index = True)
    original_text : Mapped[str] = mapped_column(Text, nullable=False)
    summary : Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_items : Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    decisions : Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status : Mapped[str] = mapped_column(String(50), nullable=False, default='pending',index = True)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at : Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class Task(Base):
    __tablename__ = 'tasks'
    id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('meeting_minutes.id'), nullable=False, unique=True)
    status : Mapped[str] =  mapped_column(String(50), nullable=False, default='pending',index = True)
    result : Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error : Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)