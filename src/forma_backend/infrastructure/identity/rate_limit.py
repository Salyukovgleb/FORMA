"""PostgreSQL auth limits; callers choose transaction boundaries explicitly."""

import hashlib
import hmac

from sqlalchemy import Connection, Engine, text
from sqlalchemy.orm import Session

BUCKET_SQL = text("""
 INSERT INTO rate_limit_buckets(scope,subject_hash,window_start,count)
 VALUES (:scope,:subject,to_timestamp(floor(extract(epoch FROM statement_timestamp())/:window)*:window),1)
 ON CONFLICT(scope,subject_hash,window_start)
 DO UPDATE SET count=rate_limit_buckets.count+1 RETURNING count
""")


def subject_hash(key: bytes, subject: str) -> str:
    return hmac.new(key, subject.encode("utf-8"), hashlib.sha256).hexdigest()


def consume_bucket(
    connection: Connection | Session, scope: str, subject: str, limit: int, window: int
) -> bool:
    count = connection.scalar(BUCKET_SQL, {"scope": scope, "subject": subject, "window": window})
    return isinstance(count, int) and count <= limit


class AuthRateLimit:
    def __init__(self, engine: Engine, key: str, scope: str = "register") -> None:
        self._scope = scope
        self._engine = engine
        self._key = key.encode()

    def consume(self, subject: str) -> bool:
        with self._engine.begin() as connection:
            return consume_bucket(
                connection, self._scope, subject_hash(self._key, subject), 10, 900
            )
