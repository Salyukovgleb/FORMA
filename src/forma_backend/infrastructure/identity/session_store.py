"""Concrete identity transaction adapter; no HTTP dependencies."""

from datetime import datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from sqlalchemy import Engine, select, tuple_, update, case, func
from sqlalchemy.orm import Session

from forma_backend.infrastructure.database.models import User, AuthSession, UsedRefreshToken
from forma_backend.modules.identity.sessions import Credential, SessionRecord
from forma_backend.infrastructure.identity.rate_limit import consume_bucket, subject_hash


def record(row: AuthSession) -> SessionRecord:
    return SessionRecord(
        row.id,
        row.user_id,
        row.refresh_token_hash,
        row.csrf_token_hash,
        row.expires_at,
        row.created_at,
        row.revoked_at,
    )


class SqlSessionStore:
    def __init__(self, engine: Engine, key: str) -> None:
        self._key = key.encode()
        self._db = Session(engine, expire_on_commit=False)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._db.close()

    def commit(self) -> None:
        self._db.commit()

    def user_by_email(self, email: str) -> Credential | None:
        user = self._db.scalar(select(User).where(User.email == email).with_for_update())
        return Credential(user.id, user.password_hash, user.is_active) if user else None

    def user_by_id(self, identifier: UUID) -> Credential | None:
        user = self._db.get(User, identifier)
        return Credential(user.id, user.password_hash, user.is_active) if user else None

    def lookup_session(self, token_hash: str) -> UUID | None:
        found = self._db.scalar(
            select(AuthSession.id).where(AuthSession.refresh_token_hash == token_hash)
        )
        return found or self._db.scalar(
            select(UsedRefreshToken.session_id).where(UsedRefreshToken.token_hash == token_hash)
        )

    def session(self, identifier: UUID, lock: bool = False) -> SessionRecord | None:
        query = select(AuthSession).where(AuthSession.id == identifier)
        if lock:
            query = query.with_for_update()
        row = self._db.scalar(query)
        return record(row) if row else None

    def create(self, value: SessionRecord) -> None:
        self._db.add(
            AuthSession(
                id=value.id,
                user_id=value.user_id,
                refresh_token_hash=value.refresh_hash,
                csrf_token_hash=value.csrf_hash,
                expires_at=value.expires_at,
                created_at=value.created_at,
                rotated_at=value.created_at,
            )
        )
        self._db.flush()

    def save(self, value: SessionRecord) -> None:
        self._db.execute(
            update(AuthSession)
            .where(AuthSession.id == value.id)
            .values(
                refresh_token_hash=value.refresh_hash,
                csrf_token_hash=value.csrf_hash,
                revoked_at=value.revoked_at,
                rotated_at=case(
                    (AuthSession.refresh_token_hash != value.refresh_hash, func.now()),
                    else_=AuthSession.rotated_at,
                ),
            )
        )

    def remember(self, token_hash: str, session_id: UUID, expires_at: datetime) -> None:
        self._db.add(
            UsedRefreshToken(token_hash=token_hash, session_id=session_id, expires_at=expires_at)
        )
        self._db.flush()

    def revoke_all(self, user_id: UUID, now: datetime) -> None:
        self._db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    def allow_refresh(self, identifier: UUID) -> bool:
        return consume_bucket(
            self._db, "refresh-session", subject_hash(self._key, str(identifier)), 30, 60
        )

    def list_active(
        self, user_id: UUID, now: datetime, limit: int, before: tuple[datetime, UUID] | None
    ) -> list[SessionRecord]:
        query = select(AuthSession).where(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
        if before:
            query = query.where(tuple_(AuthSession.created_at, AuthSession.id) < before)
        return [
            record(row)
            for row in self._db.scalars(
                query.order_by(AuthSession.created_at.desc(), AuthSession.id.desc()).limit(limit)
            )
        ]
