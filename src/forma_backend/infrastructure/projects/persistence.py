"""ORM transaction joins the maintenance connection; only the guard commits metadata."""

from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from sqlalchemy import Engine, select, func, text
from sqlalchemy.exc import OperationalError, InterfaceError, TimeoutError as DatabaseTimeout
from sqlalchemy.orm import Session

from forma_backend.infrastructure.database.models import User, AuthSession, ProjectRow
from forma_backend.infrastructure.storage.maintenance import MaintenanceGuard
from forma_backend.modules.identity.sessions import Principal
from forma_backend.modules.projects.application import ProjectRecord
from forma_backend.modules.project_files.storage import StorageUnavailable


class SqlProjectUnitOfWork:
    def __init__(self, engine: Engine) -> None:
        # Count after a waited row lock must see the preceding commit, not an old RR snapshot.
        self._guard = MaintenanceGuard(engine, isolation="READ COMMITTED")
        self._session: Session | None = None

    def __enter__(self) -> Self:
        self._guard.__enter__()
        try:
            connection = self._guard.connection
            connection.execute(text("SET LOCAL lock_timeout='2s'"))
            connection.execute(text("SET LOCAL statement_timeout='5s'"))
            self._session = Session(
                bind=connection,
                join_transaction_mode="rollback_only",
                expire_on_commit=False,
            )
        except BaseException as error:
            self._guard.__exit__(None, None, None)
            if isinstance(error, (OperationalError, InterfaceError, DatabaseTimeout)):
                raise StorageUnavailable() from None
            raise
        return self

    @property
    def db(self) -> Session:
        if self._session is None:
            raise RuntimeError("Unit of work not entered")
        return self._session

    def lock_owner(self, actor: Principal) -> bool:
        user = self.db.scalar(select(User).where(User.id == actor.user_id).with_for_update())
        if not user or not user.is_active:
            return False
        session = self.db.scalar(
            select(AuthSession).where(AuthSession.id == actor.session_id).with_for_update()
        )
        return bool(
            session
            and session.user_id == actor.user_id
            and session.revoked_at is None
            and session.expires_at > datetime.now(UTC)
        )

    def owned_count(self, identifier: UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(ProjectRow)
                .where(ProjectRow.owner_id == identifier)
            )
            or 0
        )

    def add(self, identifier: UUID, owner: UUID, title: str, description: str) -> ProjectRecord:
        project = ProjectRow(id=identifier, owner_id=owner, title=title, description=description)
        self.db.add(project)
        self.db.flush()
        self.db.refresh(project)
        return ProjectRecord(
            project.id,
            project.owner_id,
            project.title,
            project.description,
            project.revision,
            "active",
            project.created_at,
            project.updated_at,
            project.deleted_at,
        )

    def commit(self) -> None:
        self.db.commit()  # Flush only: rollback_only forbids a commit of the outer connection.
        self._guard.commit()

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if self._session is not None:
                self._session.close()
        finally:
            self._session = None
            self._guard.__exit__(kind, error, traceback)
        if isinstance(error, (OperationalError, InterfaceError, DatabaseTimeout)):
            raise StorageUnavailable() from None
