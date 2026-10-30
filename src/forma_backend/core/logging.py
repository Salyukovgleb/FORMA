"""Allowlisted JSON events; raw message/arguments/exception text are never emitted."""

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from uuid import UUID, uuid4

_request_id: ContextVar[UUID | None] = ContextVar("forma_request_id", default=None)
_EVENTS = frozenset(
    {
        "startup",
        "shutdown",
        "request_completed",
        "request_failed",
        "job_started",
        "job_completed",
        "job_failed",
        "worker_heartbeat",
    }
)
_ERROR_CODES = frozenset(
    {
        "INTERNAL_ERROR",
        "VALIDATION_ERROR",
        "DATABASE_UNAVAILABLE",
        "STORAGE_UNAVAILABLE",
        "TIMEOUT",
        "RESOURCE_LIMIT",
        "WORKER_LOST",
    }
)


@contextmanager
def request_context(incoming: str | None = None) -> Iterator[UUID]:
    try:
        identifier = UUID(incoming) if incoming else uuid4()
    except ValueError:
        identifier = uuid4()
    token = _request_id.set(identifier)
    try:
        yield identifier
    finally:
        _request_id.reset(token)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        request_id = _request_id.get()
        event = getattr(record, "event", None)
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "event": event if isinstance(event, str) and event in _EVENTS else "diagnostic",
            "request_id": str(request_id) if request_id else None,
        }
        for name in ("job_id", "project_id"):
            value = getattr(record, name, None)
            if isinstance(value, UUID):
                payload[name] = str(value)
        for name in ("duration_ms", "attempt"):
            value = getattr(record, name, None)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                payload[name] = value
        code = getattr(record, "error_code", None)
        if isinstance(code, str) and code in _ERROR_CODES:
            payload["error_code"] = code
        # Never format exception messages or arbitrary LogRecord extras: either may contain secrets.
        return json.dumps(payload, ensure_ascii=False, allow_nan=False)


def configure_logging() -> logging.Logger:
    """Configure only the application's logger, leaving third-party loggers untouched."""
    logger = logging.getLogger("forma")
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.handlers[:] = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
