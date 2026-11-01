"""Project metadata operations; authorization/state/revision stay in application layer."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Literal, Protocol
from uuid import UUID

from forma_backend.modules.access.policy import (
    Permission,
    ProjectAccessContext,
    ProjectRole,
    require_project_permission,
)
from forma_backend.modules.identity.sessions import Principal, AuthenticationFailed
from forma_backend.modules.projects.application import ProjectRecord, ProjectFailure

ProjectStatus = Literal["active", "deleted"]
Bookmark = tuple[datetime, UUID]


@dataclass(frozen=True)
class ProjectState:
    record: ProjectRecord
    context: ProjectAccessContext


@dataclass(frozen=True)
class ProjectView:
    record: ProjectRecord
    role: ProjectRole


class ProjectCrudStore(Protocol):
    def authenticate(
        self, actor: Principal, owner: UUID | None = None, *, lock: bool = False
    ) -> bool: ...
    def access_context(self, identifier: UUID, actor_id: UUID) -> ProjectAccessContext | None: ...
    def load(
        self, identifier: UUID, actor_id: UUID, *, lock: bool = False
    ) -> ProjectState | None: ...
    def list_visible(
        self, actor_id: UUID, q: str, status: ProjectStatus, before: Bookmark | None, limit: int
    ) -> list[ProjectState]: ...
    def now(self) -> datetime: ...
    def save(self, record: ProjectRecord) -> None: ...
    def commit(self) -> None: ...


class ProjectCrud:
    def __init__(self, work: Callable[[], AbstractContextManager[ProjectCrudStore]]) -> None:
        self._work = work

    def _auth(
        self,
        work: ProjectCrudStore,
        actor: Principal,
        owner: UUID | None = None,
        *,
        lock: bool = False,
    ) -> None:
        if not work.authenticate(actor, owner, lock=lock):
            raise AuthenticationFailed("SESSION_EXPIRED")

    def read(self, actor: Principal, identifier: UUID) -> ProjectView:
        with self._work() as work:
            self._auth(work, actor)
            state = work.load(identifier, actor.user_id)
            role = require_project_permission(
                actor, identifier, state.context if state else None, Permission.READER
            )
            assert state is not None
            return ProjectView(state.record, role)

    def listing(
        self, actor: Principal, q: str, status: ProjectStatus, before: Bookmark | None, limit: int
    ) -> list[ProjectView]:
        with self._work() as work:
            self._auth(work, actor)
            return [
                ProjectView(
                    s.record,
                    require_project_permission(actor, s.record.id, s.context, Permission.READER),
                )
                for s in work.list_visible(actor.user_id, q, status, before, limit)
            ]

    def _mutate(
        self,
        actor: Principal,
        identifier: UUID,
        expected_revision: int,
        operation: Literal["update", "delete", "restore"],
        *,
        title: str = "",
        description: str = "",
    ) -> ProjectView:
        with self._work() as work:
            permission = {
                "update": Permission.WRITER,
                "delete": Permission.OWNER,
                "restore": Permission.RESTORE,
            }[operation]
            initial = work.access_context(identifier, actor.user_id)
            require_project_permission(actor, identifier, initial, permission)
            assert initial is not None
            self._auth(work, actor, initial.owner_id, lock=True)
            state = work.load(identifier, actor.user_id, lock=True)
            role = require_project_permission(
                actor, identifier, state.context if state else None, permission
            )
            assert state is not None
            record = state.record
            if record.revision != expected_revision:
                raise ProjectFailure(409, "REVISION_CONFLICT", record.revision)
            now = work.now()
            if operation == "update":
                updated = replace(
                    record,
                    title=title,
                    description=description,
                    revision=record.revision + 1,
                    updated_at=now,
                )
            elif operation == "delete":
                if title != record.title:
                    raise ProjectFailure(409, "INVALID_STATE")
                updated = replace(
                    record,
                    status="deleted",
                    deleted_at=now,
                    updated_at=now,
                    revision=record.revision + 1,
                )
            else:
                if record.status != "deleted" or record.deleted_at is None:
                    raise ProjectFailure(409, "INVALID_STATE")
                if now - record.deleted_at > timedelta(days=7):
                    raise ProjectFailure(410, "RETENTION_EXPIRED")
                updated = replace(
                    record,
                    status="active",
                    deleted_at=None,
                    updated_at=now,
                    revision=record.revision + 1,
                )
            work.save(updated)
            work.commit()
            return ProjectView(updated, role)

    def update(
        self, actor: Principal, identifier: UUID, revision: int, title: str, description: str
    ) -> ProjectView:
        return self._mutate(
            actor, identifier, revision, "update", title=title, description=description
        )

    def delete(self, actor: Principal, identifier: UUID, revision: int, confirm_title: str) -> None:
        self._mutate(actor, identifier, revision, "delete", title=confirm_title)

    def restore(self, actor: Principal, identifier: UUID, revision: int) -> ProjectView:
        return self._mutate(actor, identifier, revision, "restore")
