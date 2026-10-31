"""Profile transaction adapter; shares session revocation with the session store."""

from uuid import UUID

from sqlalchemy import select, update, func

from forma_backend.infrastructure.database.models import User
from forma_backend.infrastructure.identity.session_store import SqlSessionStore
from forma_backend.modules.identity.application import AccountProfile
from forma_backend.modules.identity.profiles import ProfileAccount


class SqlProfileStore(SqlSessionStore):
    def account(self, identifier: UUID, lock: bool = False) -> ProfileAccount | None:
        query = select(User).where(User.id == identifier)
        if lock:
            query = query.with_for_update()
        user = self._db.scalar(query)
        if not user:
            return None
        return ProfileAccount(
            AccountProfile(user.id, user.email, user.display_name, user.created_at),
            user.password_hash,
            user.is_active,
        )

    def save_name(self, identifier: UUID, display_name: str) -> None:
        self._db.execute(
            update(User)
            .where(User.id == identifier)
            .values(display_name=display_name, updated_at=func.now())
        )

    def save_password(self, identifier: UUID, encoded: str) -> None:
        self._db.execute(
            update(User)
            .where(User.id == identifier)
            .values(password_hash=encoded, updated_at=func.now())
        )
