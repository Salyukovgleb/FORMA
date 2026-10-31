"""Bounded operator cleanup of expired rate buckets; no implicit transaction commits."""

import argparse
import sys

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import SQLAlchemyError

from forma_backend.core.config import load_settings
from forma_backend.infrastructure.database.session import create_database_engine


PURGE_SQL = text("""
 WITH expired AS (
   SELECT scope,subject_hash,window_start FROM rate_limit_buckets
   WHERE window_start < statement_timestamp() - interval '24 hours'
   ORDER BY window_start,scope,subject_hash
   LIMIT :max_rows FOR UPDATE SKIP LOCKED
 ), removed AS (
   DELETE FROM rate_limit_buckets AS bucket USING expired
   WHERE bucket.scope=expired.scope AND bucket.subject_hash=expired.subject_hash
     AND bucket.window_start=expired.window_start
   RETURNING 1
 ) SELECT count(*) FROM removed
""")


def purge_expired_buckets(connection: Connection, max_rows: int = 1000) -> int:
    if type(max_rows) is not int or not 1 <= max_rows <= 10000:
        raise ValueError("max_rows must be between 1 and 10000")
    count = connection.scalar(PURGE_SQL, {"max_rows": max_rows})
    if not isinstance(count, int):
        raise RuntimeError("Invalid cleanup result")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Delete a bounded batch of auth buckets older than24h"
    )
    parser.add_argument("--max-rows", type=int, default=1000)
    args = parser.parse_args()
    if not 1 <= args.max_rows <= 10000:
        parser.error("--max-rows must be between 1 and 10000")
    engine: Engine | None = None
    try:
        settings = load_settings()
        engine = create_database_engine(settings.database_url.get_secret_value())
        with engine.begin() as connection:
            connection.execute(text("SET LOCAL statement_timeout='2s'"))
            connection.execute(text("SET LOCAL lock_timeout='1s'"))
            count = purge_expired_buckets(connection, args.max_rows)
    except (ValueError, SQLAlchemyError):
        # Configuration and driver exception text can contain sensitive environment values.
        print("Auth rate bucket cleanup failed", file=sys.stderr)
        return 1
    finally:
        if engine is not None:
            engine.dispose()
    print(f"removed={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
