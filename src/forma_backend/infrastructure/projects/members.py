"""Membership SQL; caller holds project lock before any write."""

from typing import cast
from uuid import UUID
from sqlalchemy import select, update, delete
from forma_backend.infrastructure.database.models import User, ProjectMember, ProjectRow
from forma_backend.infrastructure.projects.crud_store import SqlProjectCrudStore
from forma_backend.modules.projects.member_application import MemberInfo, Role


class SqlMemberStore(SqlProjectCrudStore):
    def members(self, project: UUID) -> list[MemberInfo]:
        owner = self.db.execute(
            select(User.id, User.display_name, ProjectRow.created_at)
            .join(ProjectRow, ProjectRow.owner_id == User.id)
            .where(ProjectRow.id == project)
        ).one()
        result = [MemberInfo(owner[0], owner[1], "owner", owner[2])]
        for uid, name, role, created in self.db.execute(
            select(User.id, User.display_name, ProjectMember.role, ProjectMember.created_at)
            .join(ProjectMember, ProjectMember.user_id == User.id)
            .where(ProjectMember.project_id == project)
            .order_by(ProjectMember.created_at, User.id)
        ):
            result.append(MemberInfo(uid, name, cast(Role, role), created))
        return result

    def find_user(self, email: str) -> UUID | None:
        return self.db.scalar(select(User.id).where(User.email == email, User.is_active.is_(True)))

    def grant(self, project: UUID, target: UUID, role: Role, actor: UUID) -> None:
        self.db.add(ProjectMember(project_id=project, user_id=target, role=role, invited_by=actor))
        self.db.flush()

    def change(self, project: UUID, target: UUID, role: Role | None) -> bool:
        if role is None:
            statement = (
                delete(ProjectMember)
                .where(ProjectMember.project_id == project, ProjectMember.user_id == target)
                .returning(ProjectMember.user_id)
            )
        else:
            changed = (
                update(ProjectMember)
                .where(ProjectMember.project_id == project, ProjectMember.user_id == target)
                .values(role=role)
                .returning(ProjectMember.user_id)
            )
        if role is None:
            return self.db.scalar(statement) is not None
        return self.db.scalar(changed) is not None
