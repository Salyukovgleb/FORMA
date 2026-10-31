"""Pure project ACL. Contexts come from trusted repositories in the caller's UoW.

No authentication, I/O, caching or commits occur here. Mutating use cases must read
current ownership/membership under their transaction locks before invoking policy.
"""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from forma_backend.modules.identity.sessions import Principal


class MemberRole(StrEnum):
    EDITOR = "editor"
    VIEWER = "viewer"


class ProjectRole(StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class Permission(StrEnum):
    READER = "reader"
    WRITER = "writer"
    OWNER = "owner"
    RESTORE = "restore"
    OWNER_OR_SELF = "owner_or_self"
    OWNER_OR_REQUESTER = "owner_or_requester"


class AccessDenied(Exception):
    def __init__(self, status: int, code: str) -> None:
        super().__init__(code)
        self.status = status
        self.code = code


@dataclass(frozen=True)
class ProjectMembership:
    project_id: UUID
    user_id: UUID
    role: MemberRole

    def __post_init__(self) -> None:
        if not isinstance(self.role, MemberRole):
            raise ValueError("Invalid member role")


@dataclass(frozen=True)
class ProjectAccessContext:
    project_id: UUID
    owner_id: UUID
    membership: ProjectMembership | None = None
    deleted: bool = False


@dataclass(frozen=True)
class ProjectObjectContext:
    object_id: UUID
    project_id: UUID
    requester_id: UUID | None = None


def _role(actor: Principal, project_id: UUID, context: ProjectAccessContext | None) -> ProjectRole:
    if context is None or context.project_id != project_id:
        raise AccessDenied(404, "NOT_FOUND")
    if actor.user_id == context.owner_id:
        return ProjectRole.OWNER
    membership = context.membership
    if (
        membership is None
        or membership.project_id != project_id
        or membership.user_id != actor.user_id
        or context.deleted
    ):
        raise AccessDenied(404, "NOT_FOUND")
    return ProjectRole(membership.role.value)


def _require_active(context: ProjectAccessContext) -> None:
    if context.deleted:
        raise AccessDenied(404, "NOT_FOUND")


def _authorize(role: ProjectRole, permission: Permission) -> ProjectRole:
    if not isinstance(permission, Permission):
        raise AccessDenied(403, "FORBIDDEN")
    if (
        permission == Permission.READER
        or (permission == Permission.WRITER and role in (ProjectRole.OWNER, ProjectRole.EDITOR))
        or (permission in (Permission.OWNER, Permission.RESTORE) and role == ProjectRole.OWNER)
    ):
        return role
    # Conditional permissions need an explicit member/object scope, even for owners.
    raise AccessDenied(403, "FORBIDDEN")


def require_project_permission(
    actor: Principal,
    project_id: UUID,
    context: ProjectAccessContext | None,
    permission: Permission,
) -> ProjectRole:
    role = _role(actor, project_id, context)
    assert context is not None  # _role rejects absent context.
    if context.deleted and permission not in (Permission.READER, Permission.RESTORE):
        raise AccessDenied(404, "NOT_FOUND")
    return _authorize(role, permission)


def require_object_permission(
    actor: Principal,
    project_id: UUID,
    context: ProjectAccessContext | None,
    object_id: UUID,
    object_context: ProjectObjectContext | None,
    permission: Permission,
) -> ProjectRole:
    role = _role(actor, project_id, context)
    assert context is not None
    _require_active(context)
    if (
        object_context is None
        or object_context.object_id != object_id
        or object_context.project_id != project_id
    ):
        raise AccessDenied(404, "NOT_FOUND")
    # Verify child identity and project before checking the requested operation.
    if isinstance(permission, Permission) and permission == Permission.OWNER_OR_REQUESTER:
        if object_context.requester_id is None:
            raise AccessDenied(404, "NOT_FOUND")
        if role == ProjectRole.OWNER or object_context.requester_id == actor.user_id:
            return role
        raise AccessDenied(403, "FORBIDDEN")
    if permission == Permission.RESTORE:
        raise AccessDenied(403, "FORBIDDEN")  # Project restore is never a child operation.
    return _authorize(role, permission)


def require_member_change(
    actor: Principal,
    project_id: UUID,
    context: ProjectAccessContext | None,
    target_user_id: UUID,
    *,
    remove: bool = False,
) -> ProjectRole:
    """Grant/change is owner-only; removal is owner-or-self, with immutable owner."""
    role = _role(actor, project_id, context)
    assert context is not None
    _require_active(context)
    if type(remove) is not bool or (
        role != ProjectRole.OWNER and not (remove and actor.user_id == target_user_id)
    ):
        raise AccessDenied(403, "FORBIDDEN")
    if target_user_id == context.owner_id:
        raise AccessDenied(409, "OWNER_IMMUTABLE")
    return role
