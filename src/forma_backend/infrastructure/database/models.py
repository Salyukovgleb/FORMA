"""Implemented persistence subset of the approved PostgreSQL design."""

from datetime import datetime
from uuid import UUID
from typing import Literal

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(btrim(email))", name="ck_users_email_normalized"),
        CheckConstraint("length(display_name)>0", name="ck_users_display_name"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_sessions_expiry"),
        Index("auth_sessions_user", "user_id", "expires_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    refresh_token_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)
    csrf_token_hash: Mapped[str] = mapped_column(CHAR(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    rotated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class UsedRefreshToken(Base):
    __tablename__ = "used_refresh_tokens"
    token_hash: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("auth_sessions.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RateLimitBucket(Base):
    __tablename__ = "rate_limit_buckets"
    __table_args__ = (CheckConstraint("count>=0", name="ck_rate_count"),)
    scope: Mapped[str] = mapped_column(String(80), primary_key=True)
    subject_hash: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)


class ProjectRow(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("length(btrim(title))>0", name="ck_projects_title"),
        CheckConstraint("engine IN ('pdflatex','xelatex','lualatex')", name="ck_projects_engine"),
        CheckConstraint("status IN ('active','deleted')", name="ck_projects_status"),
        CheckConstraint("revision>0", name="ck_projects_revision"),
        CheckConstraint(
            "(status='deleted') = (deleted_at IS NOT NULL)", name="ck_projects_deleted"
        ),
        CheckConstraint("main_file_id IS NULL", name="ck_projects_main_pending_nodes"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(2000), server_default=text("''"))
    main_file_id: Mapped[UUID | None] = mapped_column()
    engine: Mapped[str] = mapped_column(Text, server_default=text("'xelatex'"))
    status: Mapped[Literal["active", "deleted"]] = mapped_column(
        Text, server_default=text("'active'")
    )
    revision: Mapped[int] = mapped_column(BigInteger, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


Index("projects_owner", ProjectRow.owner_id, ProjectRow.created_at.desc(), ProjectRow.id.desc())


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (
        CheckConstraint("role IN ('editor','viewer')", name="ck_project_members_role"),
        Index("project_members_user", "user_id", "project_id"),
    )
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True
    )
    role: Mapped[str] = mapped_column(Text)
    invited_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
