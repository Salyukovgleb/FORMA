import base64
import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from forma_backend.modules.projects.cursor import encode_cursor, decode_cursor
from forma_backend.modules.projects.application import ProjectFailure


def test_cursor_roundtrip_and_filter_identity():
    owner = uuid4()
    point = (datetime(2026, 11, 1, tzinfo=UTC), uuid4())
    token = encode_cursor(point, owner, "paper", "active")
    assert decode_cursor(token, owner, "paper", "active") == point
    for user, q, status in [
        (uuid4(), "paper", "active"),
        (owner, "other", "active"),
        (owner, "paper", "deleted"),
    ]:
        with pytest.raises(ProjectFailure):
            decode_cursor(token, user, q, status)


@pytest.mark.parametrize(
    "value",
    [None, [], 1, {"v": True}, {"v": 1, "created_at": "2026-11-01", "id": "bad", "filter": "x"}],
)
def test_untrusted_cursor_shapes_rejected(value):
    token = base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")
    with pytest.raises(ProjectFailure) as error:
        decode_cursor(token, uuid4(), "", "active")
    assert error.value.code == "INVALID_CURSOR" and error.value.status == 400
