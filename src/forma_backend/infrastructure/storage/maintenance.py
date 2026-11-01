"""Dedicated session advisory lock; metadata must use this guarded connection (ADR-0009)."""

from types import TracebackType
from typing import Self, Literal
from threading import BoundedSemaphore

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine.interfaces import DBAPIConnection

from forma_backend.modules.project_files.storage import MaintenanceBusy, StorageUnavailable

NAMESPACE = 0x464F524D
LOCK_ID = 1
_CONNECTION_SLOTS = BoundedSemaphore(8)


class MaintenanceGuard:
    def __init__(
        self,
        engine: Engine,
        *,
        exclusive: bool = False,
        isolation: Literal["READ COMMITTED"] | None = None,
    ) -> None:
        self._engine = engine
        self._isolation = isolation
        self._exclusive = exclusive
        self._connection: Connection | None = None
        self._pid: int | None = None
        self._driver: DBAPIConnection | None = None
        self._lost = False
        self._used = False
        self._slot = False

    def __enter__(self) -> Self:
        if self._used:
            raise StorageUnavailable()
        self._used = True
        self._slot = _CONNECTION_SLOTS.acquire(blocking=False)
        if not self._slot:
            raise MaintenanceBusy()
        try:
            self._connection = self._engine.connect()
            if self._isolation is not None:
                self._connection.execution_options(isolation_level=self._isolation)
            # A caller closing this dedicated connection must physically release its session lock.
            self._connection.detach()
            self._driver = self._connection.connection.dbapi_connection
            self._pid = self._connection.scalar(text("SELECT pg_backend_pid()"))
            function = "pg_try_advisory_lock" if self._exclusive else "pg_try_advisory_lock_shared"
            granted = self._connection.scalar(
                text(f"SELECT {function}(:namespace,:identifier)"),
                {"namespace": NAMESPACE, "identifier": LOCK_ID},
            )
            self._connection.commit()
            if not granted:
                self._connection.close()
                self._connection = None
                raise MaintenanceBusy()
            return self
        except BaseException as error:
            try:
                if isinstance(error, SQLAlchemyError):
                    self._invalidate()
                if self._connection is not None:
                    self._connection.close()
            finally:
                self._connection = None
                self._release_slot()
            if isinstance(error, SQLAlchemyError):
                raise StorageUnavailable() from None
            raise

    def _release_slot(self) -> None:
        if self._slot:
            _CONNECTION_SLOTS.release()
            self._slot = False

    def _invalidate(self) -> None:
        self._lost = True
        # SQLAlchemy invalidate on a detached proxy can discard the handle without closing it.
        # Retain and close the original driver directly; never fetch a replacement connection.
        if self._driver is not None:
            try:
                self._driver.close()
            except Exception:
                pass
            finally:
                self._driver = None
        if self._connection is not None and not self._connection.closed:
            self._connection.invalidate()

    def check(self, *, exclusive: bool = False) -> None:
        connection = self._connection
        if (
            self._lost
            or connection is None
            or connection.closed
            or connection.invalidated
            or (exclusive and not self._exclusive)
        ):
            raise StorageUnavailable()
        try:
            valid = connection.scalar(
                text("""
                SELECT pg_backend_pid()=:pid AND EXISTS (
                  SELECT 1 FROM pg_locks WHERE pid=pg_backend_pid() AND locktype='advisory'
                    AND classid=:namespace AND objid=:identifier AND objsubid=2
                    AND mode=:mode AND granted
                )
            """),
                {
                    "pid": self._pid,
                    "namespace": NAMESPACE,
                    "identifier": LOCK_ID,
                    "mode": "ExclusiveLock" if self._exclusive else "ShareLock",
                },
            )
            if not valid:
                self._invalidate()
                raise StorageUnavailable()
        except SQLAlchemyError:
            self._invalidate()
            raise StorageUnavailable() from None

    @property
    def connection(self) -> Connection:
        self.check()
        assert self._connection is not None
        return self._connection

    def commit(self) -> None:
        self.check()
        assert self._connection is not None
        try:
            self._connection.commit()
        except SQLAlchemyError:
            self._invalidate()
            raise StorageUnavailable() from None

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        connection = self._connection
        if connection is None:
            self._release_slot()
            return
        try:
            if not self._lost and not connection.invalidated and not connection.closed:
                connection.rollback()
                # Never reconnect to release a lock belonging to an old backend.
                self.check()
                function = "pg_advisory_unlock" if self._exclusive else "pg_advisory_unlock_shared"
                if not connection.scalar(
                    text(f"SELECT {function}(:namespace,:identifier)"),
                    {"namespace": NAMESPACE, "identifier": LOCK_ID},
                ):
                    self._invalidate()
                else:
                    connection.commit()
        except (SQLAlchemyError, StorageUnavailable):
            self._invalidate()
        finally:
            try:
                connection.close()
            finally:
                self._connection = None
                self._lost = True
                self._driver = None
                self._release_slot()
