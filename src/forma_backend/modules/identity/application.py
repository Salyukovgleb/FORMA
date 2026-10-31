"""Registration orchestration and ports; no FastAPI or SQLAlchemy imports."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4


class PasswordCapacityExceeded(Exception):
    pass


class EmailAlreadyRegistered(Exception):
    pass


@dataclass(frozen=True)
class AccountProfile:
    id: UUID
    email: str
    display_name: str
    created_at: datetime


class RateLimiter(Protocol):
    def consume(self, subject: str) -> bool: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...


class UserRepository(Protocol):
    def add(
        self, identifier: UUID, email: str, password_hash: str, display_name: str
    ) -> AccountProfile: ...


class IdentityUnitOfWork(Protocol):
    @property
    def users(self) -> UserRepository: ...
    def commit(self) -> None: ...


class RegisterUser:
    def __init__(
        self, work: Callable[[], AbstractContextManager[IdentityUnitOfWork]], hasher: PasswordHasher
    ) -> None:
        self._work = work
        self._hasher = hasher

    def execute(self, email: str, password: str, display_name: str) -> AccountProfile:
        normalized = email.strip().lower()
        password_hash = self._hasher.hash(password)
        with self._work() as work:
            result = work.users.add(uuid4(), normalized, password_hash, display_name)
            work.commit()
            return result
