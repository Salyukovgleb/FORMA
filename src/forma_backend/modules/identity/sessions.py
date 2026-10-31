"""Session use cases and transaction ports; HTTP/SQL/JWT implementations stay outside."""

import hashlib
import hmac
import secrets
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4


class AuthenticationFailed(Exception):
    def __init__(self, code: str = "UNAUTHENTICATED", status: int = 401) -> None:
        self.code = code
        self.status = status


@dataclass(frozen=True)
class Principal:
    user_id: UUID
    session_id: UUID


@dataclass(frozen=True)
class Credential:
    id: UUID
    password_hash: str = field(repr=False)
    is_active: bool


@dataclass(frozen=True)
class SessionRecord:
    id: UUID
    user_id: UUID
    refresh_hash: str = field(repr=False)
    csrf_hash: str = field(repr=False)
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None = None


@dataclass(frozen=True)
class TokenBundle:
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    csrf_token: str = field(repr=False)
    expires_at: datetime


class SessionStore(Protocol):
    def user_by_email(self, email: str) -> Credential | None: ...
    def user_by_id(self, identifier: UUID) -> Credential | None: ...
    def lookup_session(self, token_hash: str) -> UUID | None: ...
    def session(self, identifier: UUID, lock: bool = False) -> SessionRecord | None: ...
    def create(self, record: SessionRecord) -> None: ...
    def save(self, record: SessionRecord) -> None: ...
    def remember(self, token_hash: str, session_id: UUID, expires_at: datetime) -> None: ...
    def revoke_all(self, user_id: UUID, now: datetime) -> None: ...
    def list_active(
        self, user_id: UUID, now: datetime, limit: int, before: tuple[datetime, UUID] | None
    ) -> list[SessionRecord]: ...
    def allow_refresh(self, identifier: UUID) -> bool: ...
    def commit(self) -> None: ...


class PasswordVerifier(Protocol):
    def verify(self, password: str, encoded: str) -> bool: ...


class AccessTokens(Protocol):
    def issue(self, principal: Principal, now: datetime) -> str: ...
    def verify(self, token: str) -> Principal: ...


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# Public dummy, never a real account credential. Unknown users incur the same scrypt cost.
DUMMY_HASH = "scrypt$v1$32768$8$1$00000000000000000000000000000000$845e14b99194a9bff74ebb82a6ef0dda123bbac4460538a6dcc87791392e3045a4157ef0c8f57e98fc2ae2eafeb33c2bf34cb324d69a4aca215b52c5bdf5ad98"


class SessionUseCases:
    def __init__(
        self,
        work: Callable[[], AbstractContextManager[SessionStore]],
        passwords: PasswordVerifier,
        tokens: AccessTokens,
    ) -> None:
        self._work = work
        self._passwords = passwords
        self._tokens = tokens

    def _bundle(self, record: SessionRecord, refresh: str, csrf: str, now: datetime) -> TokenBundle:
        return TokenBundle(
            self._tokens.issue(Principal(record.user_id, record.id), now),
            refresh,
            csrf,
            record.expires_at,
        )

    def login(self, email: str, password: str) -> TokenBundle:
        with self._work() as store:
            user = store.user_by_email(email)
            valid = self._passwords.verify(password, user.password_hash if user else DUMMY_HASH)
            if not user or not user.is_active or not valid:
                raise AuthenticationFailed()
            now = datetime.now(UTC)
            refresh = secrets.token_urlsafe(32)
            csrf = secrets.token_urlsafe(32)
            record = SessionRecord(
                uuid4(), user.id, digest(refresh), digest(csrf), now + timedelta(days=30), now
            )
            store.create(record)
            result = self._bundle(record, refresh, csrf, now)
            store.commit()
            return result

    def authenticate(self, access: str) -> Principal:
        principal = self._tokens.verify(access)
        with self._work() as store:
            session = store.session(principal.session_id)
            user = store.user_by_id(principal.user_id)
            if (
                not session
                or session.user_id != principal.user_id
                or session.revoked_at
                or session.expires_at <= datetime.now(UTC)
                or not user
                or not user.is_active
            ):
                raise AuthenticationFailed("SESSION_EXPIRED")
        return principal

    def _refresh_session(
        self, store: SessionStore, refresh: str, csrf: str, allow_revoked: bool = False
    ) -> SessionRecord:
        if not 32 <= len(refresh) <= 128:
            raise AuthenticationFailed()
        token_hash = digest(refresh)
        identifier = store.lookup_session(token_hash)
        record = store.session(identifier, lock=True) if identifier else None
        if not record:
            raise AuthenticationFailed()
        now = datetime.now(UTC)
        # Resolve ID first, then lock by ID: a concurrent rotation cannot hide an old token.
        if not hmac.compare_digest(record.refresh_hash, token_hash):
            store.save(replace(record, revoked_at=record.revoked_at or now))
            store.commit()
            raise AuthenticationFailed("TOKEN_REPLAY")
        if record.expires_at <= now or (record.revoked_at is not None and not allow_revoked):
            raise AuthenticationFailed("SESSION_EXPIRED")
        if not hmac.compare_digest(record.csrf_hash, digest(csrf)):
            raise AuthenticationFailed("CSRF_FAILED", 403)
        user = store.user_by_id(record.user_id)
        if not user or not user.is_active:
            raise AuthenticationFailed()
        return record

    def refresh(self, refresh: str, csrf: str) -> TokenBundle:
        with self._work() as store:
            record = self._refresh_session(store, refresh, csrf)
            if not store.allow_refresh(record.id):
                store.commit()
                raise AuthenticationFailed("RATE_LIMITED", 429)
            new_refresh = secrets.token_urlsafe(32)
            new_csrf = secrets.token_urlsafe(32)
            now = datetime.now(UTC)
            store.remember(record.refresh_hash, record.id, record.expires_at)
            updated = replace(record, refresh_hash=digest(new_refresh), csrf_hash=digest(new_csrf))
            store.save(updated)
            result = self._bundle(updated, new_refresh, new_csrf, now)
            store.commit()
            return result

    def logout(self, refresh: str, csrf: str) -> None:
        with self._work() as store:
            record = self._refresh_session(store, refresh, csrf, allow_revoked=True)
            store.save(replace(record, revoked_at=record.revoked_at or datetime.now(UTC)))
            store.commit()

    def logout_all(self, principal: Principal) -> None:
        with self._work() as store:
            store.revoke_all(principal.user_id, datetime.now(UTC))
            store.commit()

    def revoke(self, principal: Principal, identifier: UUID) -> None:
        with self._work() as store:
            record = store.session(identifier, lock=True)
            if not record or record.user_id != principal.user_id:
                raise AuthenticationFailed("NOT_FOUND", 404)
            store.save(replace(record, revoked_at=record.revoked_at or datetime.now(UTC)))
            store.commit()

    def list_sessions(
        self, principal: Principal, limit: int, before: tuple[datetime, UUID] | None
    ) -> list[SessionRecord]:
        with self._work() as store:
            return store.list_active(principal.user_id, datetime.now(UTC), limit, before)
