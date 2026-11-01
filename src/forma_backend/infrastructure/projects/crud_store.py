"""Project ACL projection, keyset query and ordered row locks, sharing the guarded UoW."""

from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, or_, tuple_, update, func

from forma_backend.infrastructure.database.models import (
    ProjectRow,
    ProjectMember,
    User,
    AuthSession,
)
from forma_backend.infrastructure.projects.persistence import SqlProjectUnitOfWork, project_record
from forma_backend.modules.access.policy import ProjectAccessContext, ProjectMembership, MemberRole
from forma_backend.modules.identity.sessions import Principal
from forma_backend.modules.projects.application import ProjectRecord, ProjectFailure
from forma_backend.modules.projects.crud import ProjectState, ProjectStatus, Bookmark


def state(project: ProjectRow, member: ProjectMember | None) -> ProjectState:
    membership = (
        ProjectMembership(member.project_id, member.user_id, MemberRole(member.role))
        if member
        else None
    )
    return ProjectState(
        project_record(project),
        ProjectAccessContext(project.id, project.owner_id, membership, project.status == "deleted"),
    )


class SqlProjectCrudStore(SqlProjectUnitOfWork):
    def authenticate(
        self, actor: Principal, owner: UUID | None = None, *, lock: bool = False
    ) -> bool:
        if lock:
            identifiers = sorted({actor.user_id, owner or actor.user_id})
            # All user locks precede session/project locks, including cross-owned editor operations.
            list(
                self.db.scalars(
                    select(User.id)
                    .where(User.id.in_(identifiers))
                    .order_by(User.id)
                    .with_for_update()
                )
            )
        query = (
            select(AuthSession.id)
            .join(User, User.id == AuthSession.user_id)
            .where(
                AuthSession.id == actor.session_id,
                AuthSession.user_id == actor.user_id,
                User.is_active.is_(True),
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > func.clock_timestamp(),
            )
        )
        if lock:
            query = query.with_for_update(of=AuthSession)
        return self.db.scalar(query) is not None

    def access_context(self, identifier: UUID, actor_id: UUID) -> ProjectAccessContext | None:
        # Scalar projection: early denial never locks a foreign owner's User row or caches a Project.
        row = self.db.execute(
            select(
                ProjectRow.id,
                ProjectRow.owner_id,
                ProjectRow.status,
                ProjectMember.project_id,
                ProjectMember.user_id,
                ProjectMember.role,
            )
            .outerjoin(
                ProjectMember,
                and_(ProjectMember.project_id == ProjectRow.id, ProjectMember.user_id == actor_id),
            )
            .where(ProjectRow.id == identifier)
        ).first()
        if row is None:
            return None
        project, owner, status, member_project, member_user, member_role = row
        membership = (
            ProjectMembership(member_project, member_user, MemberRole(member_role))
            if member_project is not None
            else None
        )
        return ProjectAccessContext(project, owner, membership, status == "deleted")

    def load(self, identifier: UUID, actor_id: UUID, *, lock: bool = False) -> ProjectState | None:
        if not lock:
            row = self.db.execute(
                select(ProjectRow, ProjectMember)
                .outerjoin(
                    ProjectMember,
                    and_(
                        ProjectMember.project_id == ProjectRow.id, ProjectMember.user_id == actor_id
                    ),
                )
                .where(ProjectRow.id == identifier)
            ).first()
            return state(row[0], row[1]) if row else None
        query = (
            select(ProjectRow)
            .where(ProjectRow.id == identifier)
            .execution_options(populate_existing=True)
        )
        if lock:
            query = query.with_for_update()
        project = self.db.scalar(query)
        if project is None:
            return None
        member = self.db.scalar(
            select(ProjectMember)
            .where(ProjectMember.project_id == identifier, ProjectMember.user_id == actor_id)
            .execution_options(populate_existing=True)
        )
        return state(project, member)

    def list_visible(
        self, actor_id: UUID, q: str, status: ProjectStatus, before: Bookmark | None, limit: int
    ) -> list[ProjectState]:
        query = (
            select(ProjectRow, ProjectMember)
            .outerjoin(
                ProjectMember,
                and_(ProjectMember.project_id == ProjectRow.id, ProjectMember.user_id == actor_id),
            )
            .where(ProjectRow.status == status)
        )
        if status == "deleted":
            query = query.where(ProjectRow.owner_id == actor_id)
        else:
            query = query.where(
                or_(ProjectRow.owner_id == actor_id, ProjectMember.user_id == actor_id)
            )
        if q:
            query = query.where(
                or_(
                    ProjectRow.title.icontains(q, autoescape=True),
                    ProjectRow.description.icontains(q, autoescape=True),
                )
            )
        if before:
            query = query.where(tuple_(ProjectRow.created_at, ProjectRow.id) < before)
        query = query.order_by(ProjectRow.created_at.desc(), ProjectRow.id.desc()).limit(limit)
        return [state(project, member) for project, member in self.db.execute(query)]

    def now(self) -> datetime:
        value = self.db.scalar(select(func.clock_timestamp()))
        if not isinstance(value, datetime):
            raise RuntimeError("Invalid DB clock")
        return value

    def save(self, record: ProjectRecord) -> None:
        identifier = self.db.scalar(
            update(ProjectRow)
            .where(ProjectRow.id == record.id, ProjectRow.revision == record.revision - 1)
            .values(
                title=record.title,
                description=record.description,
                status=record.status,
                revision=record.revision,
                updated_at=record.updated_at,
                deleted_at=record.deleted_at,
            )
            .returning(ProjectRow.id)
        )
        if identifier is None:
            raise ProjectFailure(409, "REVISION_CONFLICT")
