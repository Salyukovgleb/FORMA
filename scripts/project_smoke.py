"""Public API smoke inside the disposable Compose API container, after identity smoke."""

import json
import urllib.request
from typing import Any


BASE = "http://127.0.0.1:8000"


def main() -> None:
    def call(
        method: str, path: str, payload: dict[str, object] | None = None, token: str | None = None
    ) -> tuple[int, Any]:
        headers = {"Origin": "https://forma.example.org", "Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        request = urllib.request.Request(
            BASE + path,
            method=method,
            headers=headers,
            data=json.dumps(payload).encode() if payload is not None else None,
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.load(response) if response.status != 204 else None

    code, auth = call(
        "POST",
        "/api/v1/auth/login",
        {"email": "smoke@example.org", "password": "another strong smoke password"},
    )
    assert code == 200
    token = auth["access_token"]
    code, project = call("POST", "/api/v1/projects", {"title": "Project smoke"}, token)
    assert code == 201 and project["role"] == "owner" and project["revision"] == 1
    path = "/api/v1/projects/" + project["id"]
    code, page = call("GET", "/api/v1/projects?q=Project", token=token)
    assert code == 200 and page["items"][0]["id"] == project["id"]
    code, read = call("GET", path, token=token)
    assert code == 200 and read["revision"] == 1
    code, changed = call(
        "PATCH", path, {"title": "Revised smoke", "description": "", "expected_revision": 1}, token
    )
    assert code == 200 and changed["revision"] == 2
    code, empty = call(
        "DELETE", path, {"confirm_title": "Revised smoke", "expected_revision": 2}, token
    )
    assert code == 204 and empty is None
    code, restored = call("POST", path + "/restore", {"expected_revision": 3}, token)
    assert code == 200 and restored["revision"] == 4 and restored["status"] == "active"


if __name__ == "__main__":
    main()
