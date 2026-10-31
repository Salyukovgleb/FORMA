from fastapi.testclient import TestClient
from sqlalchemy import text

from test_registration import app


def login(client, email="owner@example.org"):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct horse battery"},
        headers={"Origin": "https://forma.example.org"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def setup_client(database_url, tmp_path):
    application, engine = app(database_url, tmp_path)
    client = TestClient(application, base_url="https://forma.example.org")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.org",
            "password": "correct horse battery",
            "display_name": "Owner",
        },
    )
    assert response.status_code == 201
    return client, engine


def test_rotation_replay_revokes_access(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            token = login(client)
            old_cookie = client.cookies.get("forma_refresh")
            header = {"Origin": "https://forma.example.org", "X-CSRF-Token": token["csrf_token"]}
            renewed = client.post("/api/v1/auth/refresh", headers=header)
            assert (
                renewed.status_code == 200 and renewed.json()["csrf_token"] != token["csrf_token"]
            )
            assert client.cookies.get("forma_refresh") != old_cookie
            assert (
                client.post(
                    "/api/v1/auth/refresh",
                    headers={
                        "Origin": "https://forma.example.org",
                        "X-CSRF-Token": token["csrf_token"],
                    },
                ).status_code
                == 403
            )
            replay = client.post(
                "/api/v1/auth/refresh", headers={**header, "Cookie": f"forma_refresh={old_cookie}"}
            )
            assert replay.status_code == 401 and replay.json()["error"]["code"] == "TOKEN_REPLAY"
            assert (
                client.get(
                    "/api/v1/auth/sessions",
                    headers={"Authorization": "Bearer " + renewed.json()["access_token"]},
                ).status_code
                == 401
            )
    finally:
        engine.dispose()


def test_sessions_logout_and_csrf(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            token = login(client)
            bearer = {"Authorization": "Bearer " + token["access_token"]}
            listed = client.get("/api/v1/auth/sessions", headers=bearer)
            assert listed.status_code == 200 and listed.json()["items"][0]["is_current"]
            assert (
                client.post(
                    "/api/v1/auth/refresh",
                    headers={
                        "Origin": "https://evil.example.org",
                        "X-CSRF-Token": token["csrf_token"],
                    },
                ).status_code
                == 403
            )
            assert (
                client.post(
                    "/api/v1/auth/refresh",
                    headers={"Origin": "https://forma.example.org", "X-CSRF-Token": "x" * 43},
                ).status_code
                == 403
            )
            cookie = client.cookies.get("forma_refresh")
            with engine.connect() as conn:
                before = conn.scalar(text("SELECT rotated_at FROM auth_sessions"))
            logout = client.post(
                "/api/v1/auth/logout",
                headers={
                    "Origin": "https://forma.example.org",
                    "X-CSRF-Token": token["csrf_token"],
                },
            )
            assert logout.status_code == 204 and not logout.content
            assert (
                client.post(
                    "/api/v1/auth/logout",
                    headers={
                        "Origin": "https://forma.example.org",
                        "X-CSRF-Token": token["csrf_token"],
                        "Cookie": f"forma_refresh={cookie}",
                    },
                ).status_code
                == 204
            )
            with engine.connect() as conn:
                assert conn.scalar(text("SELECT rotated_at FROM auth_sessions")) == before

            assert client.get("/api/v1/auth/sessions", headers=bearer).status_code == 401
    finally:
        engine.dispose()


def test_logout_all_and_foreign_session_are_protected(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            first = login(client)
            second = login(client)
            first_headers = {"Authorization": "Bearer " + first["access_token"]}
            assert (
                len(client.get("/api/v1/auth/sessions", headers=first_headers).json()["items"]) == 2
            )
            logout = client.post("/api/v1/auth/logout-all", headers=first_headers)
            assert logout.status_code == 204
            assert (
                client.get(
                    "/api/v1/auth/sessions",
                    headers={"Authorization": "Bearer " + second["access_token"]},
                ).status_code
                == 401
            )
        with engine.connect() as connection:
            assert (
                connection.scalar(
                    text("SELECT count(*) FROM auth_sessions WHERE revoked_at IS NULL")
                )
                == 0
            )
    finally:
        engine.dispose()


def test_concurrent_refresh_revokes_family(database_url, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    from threading import Barrier
    from forma_backend.infrastructure.identity.session_store import SqlSessionStore

    both_resolved = Barrier(2)
    original = SqlSessionStore.lookup_session

    def synchronized_lookup(self, token_hash):
        result = original(self, token_hash)
        both_resolved.wait(timeout=5)
        return result

    monkeypatch.setattr(SqlSessionStore, "lookup_session", synchronized_lookup)
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            initial = login(client)
            cookie = client.cookies.get("forma_refresh")
            headers = {
                "Origin": "https://forma.example.org",
                "X-CSRF-Token": initial["csrf_token"],
                "Cookie": f"forma_refresh={cookie}",
            }
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(
                    pool.map(
                        lambda _: client.post("/api/v1/auth/refresh", headers=headers), range(2)
                    )
                )
            assert sorted(r.status_code for r in results) == [200, 401]
            fresh = next(r.json() for r in results if r.status_code == 200)
            assert (
                client.get(
                    "/api/v1/auth/sessions",
                    headers={"Authorization": "Bearer " + fresh["access_token"]},
                ).status_code
                == 401
            )
    finally:
        engine.dispose()


def test_session_pagination_delete_and_foreign_lookup(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            login(client)
            token = login(client)
            headers = {"Authorization": "Bearer " + token["access_token"]}
            first = client.get("/api/v1/auth/sessions?limit=1", headers=headers).json()
            second = client.get(
                "/api/v1/auth/sessions",
                params={"limit": 1, "cursor": first["next_cursor"]},
                headers=headers,
            ).json()
            assert first["items"][0]["id"] != second["items"][0]["id"]
            assert (
                client.get("/api/v1/auth/sessions?cursor=invalid", headers=headers).status_code
                == 400
            )
            target = second["items"][0]["id"]
            assert (
                client.delete("/api/v1/auth/sessions/" + target, headers=headers).status_code == 204
            )
            assert (
                client.delete("/api/v1/auth/sessions/" + target, headers=headers).status_code == 204
            )
            assert (
                client.delete(
                    "/api/v1/auth/sessions/00000000-0000-4000-8000-000000000001", headers=headers
                ).status_code
                == 404
            )
    finally:
        engine.dispose()


def test_foreign_revocation_and_invalid_credentials(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            owner = login(client)
            owner_header = {"Authorization": "Bearer " + owner["access_token"]}
            assert (
                client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "other@example.org",
                        "password": "correct horse battery",
                        "display_name": "Other",
                    },
                ).status_code
                == 201
            )
            other = login(client, "other@example.org")
            other_id = client.get(
                "/api/v1/auth/sessions",
                headers={"Authorization": "Bearer " + other["access_token"]},
            ).json()["items"][0]["id"]
            assert (
                client.delete("/api/v1/auth/sessions/" + other_id, headers=owner_header).status_code
                == 404
            )
            for email in ["owner@example.org", "missing@example.org"]:
                response = client.post(
                    "/api/v1/auth/login",
                    json={"email": email, "password": "wrong password value"},
                    headers={"Origin": "https://forma.example.org"},
                )
                assert (
                    response.status_code == 401
                    and response.json()["error"]["code"] == "UNAUTHENTICATED"
                )
    finally:
        engine.dispose()


def test_disabled_user_and_expired_session_deny_access(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            token = login(client)
            headers = {"Authorization": "Bearer " + token["access_token"]}
            with engine.begin() as conn:
                conn.execute(text("UPDATE users SET is_active=false"))
            assert client.get("/api/v1/auth/sessions", headers=headers).status_code == 401
            with engine.begin() as conn:
                conn.execute(text("UPDATE users SET is_active=true"))
                conn.execute(
                    text(
                        "UPDATE auth_sessions SET created_at=now()-interval '2 minutes', expires_at=now()-interval '1 minute'"
                    )
                )
            assert client.get("/api/v1/auth/sessions", headers=headers).status_code == 401
    finally:
        engine.dispose()


def test_tokens_are_hashed_and_rotation_preserves_absolute_expiry(database_url, tmp_path, capsys):
    import hashlib

    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            token = login(client)
            cookie = client.cookies.get("forma_refresh")
            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT refresh_token_hash,csrf_token_hash,expires_at FROM auth_sessions")
                ).one()
                assert row[0] == hashlib.sha256(cookie.encode()).hexdigest()
                assert row[1] == hashlib.sha256(token["csrf_token"].encode()).hexdigest()
                expiry = row[2]
            rotated = client.post(
                "/api/v1/auth/refresh",
                headers={
                    "Origin": "https://forma.example.org",
                    "X-CSRF-Token": token["csrf_token"],
                },
            )
            assert rotated.status_code == 200
            with engine.connect() as conn:
                assert conn.scalar(text("SELECT expires_at FROM auth_sessions")) == expiry
                assert conn.scalar(text("SELECT count(*) FROM used_refresh_tokens")) == 1
            output = capsys.readouterr().out
            assert (
                cookie not in output
                and token["access_token"] not in output
                and token["csrf_token"] not in output
            )
    finally:
        engine.dispose()
