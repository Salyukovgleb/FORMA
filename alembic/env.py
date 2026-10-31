"""Migration connection comes from caller or DATABASE_URL, never committed credentials."""

import os

from alembic import context
from sqlalchemy import Connection

from forma_backend.infrastructure.database.models import Base
from forma_backend.infrastructure.database.session import create_database_engine


def configure(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url="postgresql+psycopg://", target_metadata=Base.metadata, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    connection = context.config.attributes.get("connection")
    if connection is not None:
        configure(connection)
    else:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError("DATABASE_URL must be configured for migrations")
        engine = create_database_engine(url)
        try:
            with engine.connect() as connection:
                configure(connection)
        finally:
            engine.dispose()
