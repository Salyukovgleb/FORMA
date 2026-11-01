"""Bounded keyset cursor, bound to actor and exact list filters; SQL always enforces ACL."""

import base64
import hashlib
import hmac
import json
from datetime import datetime
from uuid import UUID

from forma_backend.modules.projects.application import ProjectFailure
from forma_backend.modules.projects.crud import Bookmark, ProjectStatus


def filter_hash(actor: UUID, q: str, status: ProjectStatus) -> str:
    return hashlib.sha256(
        json.dumps([str(actor), q, status], ensure_ascii=True, separators=(",", ":")).encode()
    ).hexdigest()


def encode_cursor(point: Bookmark, actor: UUID, q: str, status: ProjectStatus) -> str:
    value = {
        "v": 1,
        "created_at": point[0].isoformat(),
        "id": str(point[1]),
        "filter": filter_hash(actor, q, status),
    }
    return (
        base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode())
        .decode()
        .rstrip("=")
    )


def decode_cursor(token: str, actor: UUID, q: str, status: ProjectStatus) -> Bookmark:
    try:
        if len(token) > 2048:
            raise ValueError()
        raw = base64.b64decode(token + "=" * (-len(token) % 4), altchars=b"-_", validate=True)
        value = json.loads(raw)
        if (
            not isinstance(value, dict)
            or set(value) != {"v", "created_at", "id", "filter"}
            or type(value["v"]) is not int
            or value["v"] != 1
        ):
            raise ValueError()
        if not all(isinstance(value[k], str) for k in ["created_at", "id", "filter"]):
            raise ValueError()
        if not hmac.compare_digest(value["filter"], filter_hash(actor, q, status)):
            raise ValueError()
        timestamp = datetime.fromisoformat(value["created_at"])
        if timestamp.tzinfo is None:
            raise ValueError()
        return timestamp, UUID(value["id"])
    except (ValueError, TypeError, KeyError, UnicodeError):
        raise ProjectFailure(400, "INVALID_CURSOR") from None
