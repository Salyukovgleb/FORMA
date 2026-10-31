"""Own-profile operations; the account lock serializes password change with login."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from forma_backend.modules.identity.application import AccountProfile
from forma_backend.modules.identity.sessions import AuthenticationFailed, Principal, SessionRecord


@dataclass(frozen=True)
class ProfileAccount:
    profile: AccountProfile
    password_hash: str = field(repr=False)
    is_active: bool


class ProfileStore(Protocol):
    def account(self, identifier: UUID, lock: bool = False) -> ProfileAccount | None: ...
    def session(self, identifier: UUID, lock: bool = False) -> SessionRecord | None: ...
    def save_name(self, identifier: UUID, display_name: str) -> None: ...
    def save_password(self, identifier: UUID, encoded: str) -> None: ...
    def revoke_all(self, user_id: UUID, now: datetime) -> None: ...
    def commit(self) -> None: ...


class Passwords(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, encoded: str) -> bool: ...


class ProfileUseCases:
    def __init__(
        self,
        work: Callable[[], AbstractContextManager[ProfileStore]],
        passwords: Passwords,
    ) -> None:
        self._work = work
        self._passwords = passwords

    def _account(self, store: ProfileStore, actor: Principal, lock: bool) -> ProfileAccount:
        account = store.account(actor.user_id, lock)
        # Recheck after the user lock: another password change may revoke this actor while waiting.
        session = store.session(actor.session_id)
        if (
            not account
            or not account.is_active
            or not session
            or session.user_id != actor.user_id
            or session.revoked_at
            or session.expires_at <= datetime.now(UTC)
        ):
            raise AuthenticationFailed("SESSION_EXPIRED")
        return account

    def read(self, actor: Principal) -> AccountProfile:
        with self._work() as store:
            return self._account(store, actor, False).profile

    def update(self, actor: Principal, name: str) -> AccountProfile:
        with self._work() as store:
            account = self._account(store, actor, True)
            store.save_name(actor.user_id, name)
            store.commit()
            profile = account.profile
            return AccountProfile(profile.id, profile.email, name, profile.created_at)

    def change_password(self, actor: Principal, current: str, new: str) -> None:
        with self._work() as store:
            account = self._account(store, actor, True)
            if not self._passwords.verify(current, account.password_hash):
                raise AuthenticationFailed()
            encoded = self._passwords.hash(new)
            store.save_password(actor.user_id, encoded)
            store.revoke_all(actor.user_id, datetime.now(UTC))
            store.commit()
