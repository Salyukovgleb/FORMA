"""SQLAlchemy implementations of identity ports, sharing one explicit transaction."""

from types import TracebackType
from typing import Self
from uuid import UUID

from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from forma_backend.infrastructure.database.models import User
from forma_backend.modules.identity.application import AccountProfile, EmailAlreadyRegistered


class SqlUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self, identifier: UUID, email: str, password_hash: str, display_name: str
    ) -> AccountProfile:
        user = User(
            id=identifier, email=email, password_hash=password_hash, display_name=display_name
        )
        self._session.add(user)
        try:
            self._session.flush()
        except IntegrityError as error:
            original = error.orig
            if (
                getattr(original, "sqlstate", None) == "23505"
                and getattr(getattr(original, "diag", None), "constraint_name", None)
                == "users_email_key"
            ):
                raise EmailAlreadyRegistered() from None
            raise
        self._session.refresh(user)
        return AccountProfile(user.id, user.email, user.display_name, user.created_at)


class SqlIdentityUnitOfWork:
    def __init__(self, engine: Engine) -> None:
        self._session = Session(engine, expire_on_commit=False)
        self.users = SqlUserRepository(self._session)

    def __enter__(self) -> Self:
        return self

    def commit(self) -> None:
        self._session.commit()

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._session.close()
