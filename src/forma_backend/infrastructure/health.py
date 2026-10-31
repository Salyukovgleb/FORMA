"""Bounded database probe and a private, temporary local-volume write probe."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError


def database_ready(engine: Engine) -> bool:
    try:
        with engine.begin() as connection:
            connection.execute(text("SET LOCAL statement_timeout = '2s'"))
            return bool(connection.scalar(text("SELECT 1")) == 1)
    except SQLAlchemyError:
        return False


def storage_ready(root: Path) -> bool:
    try:
        with NamedTemporaryFile(dir=root, prefix=".forma-health-", mode="wb") as probe:
            probe.write(b"forma-health")
            probe.flush()
            os.fsync(probe.fileno())
        return True
    except OSError:
        return False
