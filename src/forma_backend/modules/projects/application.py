"""CreateProject application transaction; no HTTP/SQL imports."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID, uuid4

from forma_backend.modules.identity.sessions import Principal, AuthenticationFailed


class ProjectFailure(Exception):
    def __init__(self, status: int, code: str) -> None:
        super().__init__(code)
        self.status = status
        self.code = code


@dataclass(frozen=True)
class ProjectRecord:
    id: UUID
    owner_id: UUID
    title: str
    description: str
    revision: int
    status: Literal["active", "deleted"]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ProjectUnitOfWork(Protocol):
    def lock_owner(self, actor: Principal) -> bool: ...
    def owned_count(self, identifier: UUID) -> int: ...
    def add(self, identifier: UUID, owner: UUID, title: str, description: str) -> ProjectRecord: ...
    def commit(self) -> None: ...


class CreateProject:
    def __init__(
        self, work: Callable[[], AbstractContextManager[ProjectUnitOfWork]], limit: int = 100
    ) -> None:
        self._work = work
        self._limit = limit

    def execute(
        self, actor: Principal, title: str, description: str, template_id: str | None
    ) -> ProjectRecord:
        if template_id is not None:
            raise ProjectFailure(404, "NOT_FOUND")  # Template registry is BE-021.
        with self._work() as work:
            if not work.lock_owner(actor):
                raise AuthenticationFailed("SESSION_EXPIRED")
            if work.owned_count(actor.user_id) >= self._limit:
                raise ProjectFailure(429, "QUOTA_EXCEEDED")
            result = work.add(uuid4(), actor.user_id, title, description)
            work.commit()
            return result
