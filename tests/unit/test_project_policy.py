"""Authorization decisions from the approved ACL matrix, including IDOR boundaries."""

from dataclasses import replace
from uuid import uuid4

import pytest

from forma_backend.modules.identity.sessions import Principal
from forma_backend.modules.access.policy import (
    AccessDenied,
    MemberRole,
    ProjectRole,
    Permission,
    ProjectMembership,
    ProjectAccessContext,
    ProjectObjectContext,
    require_project_permission,
    require_object_permission,
    require_member_change,
)

OWNER, EDITOR, VIEWER, STRANGER = (uuid4() for _ in range(4))
PROJECT, OTHER, OBJECT = (uuid4() for _ in range(3))


def actor(user):
    return Principal(user, uuid4())


def context(user, *, deleted=False):
    roles = {EDITOR: MemberRole.EDITOR, VIEWER: MemberRole.VIEWER}
    membership = ProjectMembership(PROJECT, user, roles[user]) if user in roles else None
    return ProjectAccessContext(PROJECT, OWNER, membership, deleted)


def denied(status, code, callback):
    with pytest.raises(AccessDenied) as result:
        callback()
    assert (result.value.status, result.value.code) == (status, code)
    assert str(PROJECT) not in str(result.value)


@pytest.mark.parametrize(
    "user,role,permission,status",
    [
        (OWNER, ProjectRole.OWNER, Permission.READER, 200),
        (EDITOR, ProjectRole.EDITOR, Permission.READER, 200),
        (VIEWER, ProjectRole.VIEWER, Permission.READER, 200),
        (STRANGER, None, Permission.READER, 404),
        (OWNER, ProjectRole.OWNER, Permission.WRITER, 200),
        (EDITOR, ProjectRole.EDITOR, Permission.WRITER, 200),
        (VIEWER, None, Permission.WRITER, 403),
        (STRANGER, None, Permission.WRITER, 404),
        (OWNER, ProjectRole.OWNER, Permission.OWNER, 200),
        (EDITOR, None, Permission.OWNER, 403),
        (VIEWER, None, Permission.OWNER, 403),
        (STRANGER, None, Permission.OWNER, 404),
    ],
)
def test_role_matrix(user, role, permission, status):
    operation = lambda: require_project_permission(actor(user), PROJECT, context(user), permission)
    if status == 200:
        assert operation() == role
    else:
        denied(status, "NOT_FOUND" if status == 404 else "FORBIDDEN", operation)


@pytest.mark.parametrize("user", [OWNER, EDITOR, VIEWER, STRANGER])
def test_missing_and_mismatched_project_are_indistinguishable(user):
    for supplied in [None, replace(context(user), project_id=OTHER)]:
        denied(
            404,
            "NOT_FOUND",
            lambda: require_project_permission(actor(user), PROJECT, supplied, Permission.READER),
        )


@pytest.mark.parametrize(
    "membership",
    [
        ProjectMembership(OTHER, STRANGER, MemberRole.EDITOR),
        ProjectMembership(PROJECT, EDITOR, MemberRole.EDITOR),
    ],
)
def test_foreign_membership_never_grants_access(membership):
    supplied = ProjectAccessContext(PROJECT, OWNER, membership)
    denied(
        404,
        "NOT_FOUND",
        lambda: require_project_permission(actor(STRANGER), PROJECT, supplied, Permission.READER),
    )


def test_owner_is_derived_and_membership_cannot_claim_ownership():
    supplied = ProjectAccessContext(
        PROJECT, OWNER, ProjectMembership(PROJECT, OWNER, MemberRole.VIEWER)
    )
    assert (
        require_project_permission(actor(OWNER), PROJECT, supplied, Permission.OWNER)
        == ProjectRole.OWNER
    )
    for role in ["owner", "editor", None, ProjectRole.OWNER]:
        with pytest.raises(ValueError):
            ProjectMembership(PROJECT, STRANGER, role)


@pytest.mark.parametrize(
    "user,permission,status",
    [
        (OWNER, Permission.READER, 200),
        (OWNER, Permission.RESTORE, 200),
        (OWNER, Permission.WRITER, 404),
        (OWNER, Permission.OWNER, 404),
        (EDITOR, Permission.READER, 404),
        (VIEWER, Permission.READER, 404),
        (STRANGER, Permission.RESTORE, 404),
    ],
)
def test_deleted_visibility(user, permission, status):
    operation = lambda: require_project_permission(
        actor(user), PROJECT, context(user, deleted=True), permission
    )
    if status == 200:
        assert operation() == ProjectRole.OWNER
    else:
        denied(status, "NOT_FOUND", operation)


@pytest.mark.parametrize("user", [EDITOR, VIEWER])
def test_restore_requires_owner_even_on_active_project(user):
    denied(
        403,
        "FORBIDDEN",
        lambda: require_project_permission(actor(user), PROJECT, context(user), Permission.RESTORE),
    )


@pytest.mark.parametrize("user", [OWNER, EDITOR, VIEWER])
@pytest.mark.parametrize(
    "child", [None, ProjectObjectContext(OBJECT, OTHER), ProjectObjectContext(uuid4(), PROJECT)]
)
def test_child_id_and_project_are_checked_before_operation_rights(user, child):
    denied(
        404,
        "NOT_FOUND",
        lambda: require_object_permission(
            actor(user), PROJECT, context(user), OBJECT, child, Permission.WRITER
        ),
    )


def test_valid_child_and_viewer_denied_write():
    child = ProjectObjectContext(OBJECT, PROJECT)
    assert (
        require_object_permission(
            actor(EDITOR), PROJECT, context(EDITOR), OBJECT, child, Permission.WRITER
        )
        == ProjectRole.EDITOR
    )
    denied(
        403,
        "FORBIDDEN",
        lambda: require_object_permission(
            actor(VIEWER), PROJECT, context(VIEWER), OBJECT, child, Permission.WRITER
        ),
    )
    # An owner may read a deleted project's metadata, but its child endpoints stay hidden.
    denied(
        404,
        "NOT_FOUND",
        lambda: require_object_permission(
            actor(OWNER), PROJECT, context(OWNER, deleted=True), OBJECT, child, Permission.READER
        ),
    )


@pytest.mark.parametrize(
    "user,target,remove,status,code",
    [
        (OWNER, EDITOR, False, 200, None),
        (OWNER, VIEWER, True, 200, None),
        (EDITOR, EDITOR, True, 200, None),
        (VIEWER, VIEWER, True, 200, None),
        (EDITOR, VIEWER, True, 403, "FORBIDDEN"),
        (VIEWER, EDITOR, False, 403, "FORBIDDEN"),
        (EDITOR, EDITOR, False, 403, "FORBIDDEN"),
        (OWNER, OWNER, True, 409, "OWNER_IMMUTABLE"),
        (OWNER, OWNER, False, 409, "OWNER_IMMUTABLE"),
        (EDITOR, OWNER, True, 403, "FORBIDDEN"),
        (STRANGER, STRANGER, True, 404, "NOT_FOUND"),
    ],
)
def test_membership_mutations(user, target, remove, status, code):
    operation = lambda: require_member_change(
        actor(user), PROJECT, context(user), target, remove=remove
    )
    if status == 200:
        operation()
    else:
        denied(status, code, operation)


@pytest.mark.parametrize(
    "user,requester,status",
    [
        (OWNER, EDITOR, 200),
        (EDITOR, EDITOR, 200),
        (VIEWER, VIEWER, 200),
        (EDITOR, VIEWER, 403),
        (VIEWER, OWNER, 403),
        (STRANGER, STRANGER, 404),
    ],
)
def test_requester_must_still_be_a_member(user, requester, status):
    child = ProjectObjectContext(OBJECT, PROJECT, requester)
    operation = lambda: require_object_permission(
        actor(user), PROJECT, context(user), OBJECT, child, Permission.OWNER_OR_REQUESTER
    )
    if status == 200:
        operation()
    else:
        denied(status, "NOT_FOUND" if status == 404 else "FORBIDDEN", operation)


def test_missing_requester_and_conditional_project_permission_fail_closed():
    child = ProjectObjectContext(OBJECT, PROJECT)
    denied(
        404,
        "NOT_FOUND",
        lambda: require_object_permission(
            actor(OWNER), PROJECT, context(OWNER), OBJECT, child, Permission.OWNER_OR_REQUESTER
        ),
    )
    for permission in [
        Permission.OWNER_OR_SELF,
        Permission.OWNER_OR_REQUESTER,
        "writer",
        "unrecognized",
        None,
    ]:
        denied(
            403,
            "FORBIDDEN",
            lambda: require_project_permission(actor(OWNER), PROJECT, context(OWNER), permission),
        )
    denied(
        403,
        "FORBIDDEN",
        lambda: require_object_permission(
            actor(OWNER), PROJECT, context(OWNER), OBJECT, child, Permission.OWNER_OR_SELF
        ),
    )


def test_membership_is_reevaluated_per_call_without_cached_grant():
    principal = actor(EDITOR)
    child = ProjectObjectContext(OBJECT, PROJECT, EDITOR)
    granted = context(EDITOR)
    assert (
        require_object_permission(principal, PROJECT, granted, OBJECT, child, Permission.WRITER)
        == ProjectRole.EDITOR
    )
    downgraded = replace(granted, membership=ProjectMembership(PROJECT, EDITOR, MemberRole.VIEWER))
    denied(
        403,
        "FORBIDDEN",
        lambda: require_object_permission(
            principal, PROJECT, downgraded, OBJECT, child, Permission.WRITER
        ),
    )
    removed = replace(granted, membership=None)
    denied(
        404,
        "NOT_FOUND",
        lambda: require_object_permission(
            principal, PROJECT, removed, OBJECT, child, Permission.OWNER_OR_REQUESTER
        ),
    )


def test_deleted_membership_and_requester_operations_stay_hidden():
    deleted = context(OWNER, deleted=True)
    denied(
        404,
        "NOT_FOUND",
        lambda: require_member_change(actor(OWNER), PROJECT, deleted, EDITOR, remove=True),
    )
    child = ProjectObjectContext(OBJECT, PROJECT, OWNER)
    denied(
        404,
        "NOT_FOUND",
        lambda: require_object_permission(
            actor(OWNER), PROJECT, deleted, OBJECT, child, Permission.OWNER_OR_REQUESTER
        ),
    )


def test_invalid_member_operation_never_grants_self_role_change():
    denied(
        403,
        "FORBIDDEN",
        lambda: require_member_change(
            actor(EDITOR), PROJECT, context(EDITOR), EDITOR, remove="false"
        ),
    )
