"""Project membership policy and serialized mutations."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID
from forma_backend.modules.access.policy import (
    Permission,
    require_project_permission,
    require_member_change,
)
from forma_backend.modules.identity.sessions import Principal, AuthenticationFailed
from forma_backend.modules.projects.application import ProjectFailure
from forma_backend.modules.projects.crud import ProjectCrudStore

Role = Literal["editor", "viewer"]


@dataclass(frozen=True)
class MemberInfo:
    user_id: UUID
    display_name: str
    role: Literal["owner", "editor", "viewer"]
    created_at: datetime


class MemberStore(ProjectCrudStore, Protocol):
    def members(self, project: UUID) -> list[MemberInfo]: ...
    def find_user(self, email: str) -> UUID | None: ...
    def grant(self, project: UUID, target: UUID, role: Role, actor: UUID) -> None: ...
    def change(self, project: UUID, target: UUID, role: Role | None) -> bool: ...


class ProjectMembers:
    def __init__(self, work: Callable[[], AbstractContextManager[MemberStore]]) -> None:
        self.work = work

    def execute(
        self,
        actor: Principal,
        project: UUID,
        operation: Literal["list", "grant", "change", "remove"],
        *,
        target: UUID | None = None,
        email: str = "",
        role: Role = "viewer",
    ) -> list[MemberInfo]:
        with self.work() as work:
            context = work.access_context(project, actor.user_id)
            require_project_permission(actor, project, context, Permission.READER)
            assert context is not None
            if context.deleted:
                raise ProjectFailure(404, "NOT_FOUND")
            if operation == "grant":
                require_project_permission(actor, project, context, Permission.OWNER)
            elif operation != "list":
                assert target is not None
                require_member_change(actor, project, context, target, remove=operation == "remove")
            if not work.authenticate(actor, context.owner_id, lock=operation != "list"):
                raise AuthenticationFailed("SESSION_EXPIRED")
            state = work.load(project, actor.user_id, lock=operation != "list")
            require_project_permission(
                actor, project, state.context if state else None, Permission.READER
            )
            assert state is not None
            if state.context.deleted:
                raise ProjectFailure(404, "NOT_FOUND")
            if operation == "list":
                return work.members(project)
            if operation == "grant":
                target = work.find_user(email)
                if target is None:
                    raise ProjectFailure(404, "USER_NOT_FOUND")
            assert target is not None
            require_member_change(
                actor, project, state.context, target, remove=operation == "remove"
            )
            members = work.members(project)
            if operation == "grant":
                if any(m.user_id == target for m in members):
                    raise ProjectFailure(409, "MEMBER_EXISTS")
                if len(members) >= 50:
                    raise ProjectFailure(429, "MEMBER_LIMIT_EXCEEDED")
                work.grant(project, target, role, actor.user_id)
            elif not work.change(project, target, role if operation == "change" else None):
                raise ProjectFailure(404, "NOT_FOUND")
            result = work.members(project) if operation != "remove" else []
            work.commit()
            return [m for m in result if m.user_id == target]
