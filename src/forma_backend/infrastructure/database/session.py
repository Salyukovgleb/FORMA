"""Synchronous database lifecycle. Use cases explicitly commit their unit of work."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


def create_database_engine(url: str | URL) -> Engine:
    parsed = make_url(url)
    if parsed.drivername != "postgresql+psycopg":
        raise ValueError("Expected postgresql+psycopg database URL")
    return create_engine(parsed, pool_pre_ping=True, hide_parameters=True, echo=False)


@contextmanager
def unit_of_work(engine: Engine) -> Iterator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        try:
            yield session
        finally:
            # Uncommitted work is rolled back on normal exit as well as exceptions.
            session.rollback()
