"""Atomic PostgreSQL fixed-window limit for public registration, without a broker."""

import hashlib
import hmac

from sqlalchemy import Engine, text


class RegistrationRateLimit:
    def __init__(self, engine: Engine, key: str) -> None:
        self._engine = engine
        self._key = key.encode("utf-8")

    def consume(self, subject: str) -> bool:
        digest = hmac.new(self._key, subject.encode("utf-8"), hashlib.sha256).hexdigest()
        with self._engine.begin() as connection:
            count = connection.scalar(
                text("""
                INSERT INTO rate_limit_buckets(scope,subject_hash,window_start,count)
                VALUES ('register',:subject,to_timestamp(floor(extract(epoch FROM now())/900)*900),1)
                ON CONFLICT(scope,subject_hash,window_start)
                DO UPDATE SET count=rate_limit_buckets.count+1 RETURNING count
            """),
                {"subject": digest},
            )
        return isinstance(count, int) and count <= 10
