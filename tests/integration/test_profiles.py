from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

from fastapi.testclient import TestClient
from sqlalchemy import text

from test_sessions import login, setup_client


PATH = "/api/v1/users/me"
NEW = "a different strong password"


def test_own_profile_and_restricted_update(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            token = login(client)
            headers = {"Authorization": "Bearer " + token["access_token"]}
            assert client.get(PATH).status_code == 401
            profile = client.get(PATH, headers=headers)
            assert profile.status_code == 200, profile.text
            original = profile.json()
            assert set(original) == {"id", "email", "display_name", "created_at"}
            for payload in [
                {"email": "other@example.org"},
                {"display_name": "Other", "id": original["id"]},
                {"display_name": ""},
                {"display_name": "bad\x00name"},
            ]:
                assert client.patch(PATH, headers=headers, json=payload).status_code == 422
            with engine.connect() as db:
                before = db.scalar(
                    text("SELECT updated_at FROM users WHERE email = 'owner@example.org'")
                )
            changed = client.patch(PATH, headers=headers, json={"display_name": "Новое имя"})
            assert changed.status_code == 200
            with engine.connect() as db:
                assert (
                    db.scalar(
                        text("SELECT updated_at FROM users WHERE email = 'owner@example.org'")
                    )
                    > before
                )
            assert changed.json() == {**original, "display_name": "Новое имя"}
            assert client.get(PATH + "/" + original["id"], headers=headers).status_code == 404
            client.post(
                "/api/v1/auth/register",
                json={
                    "email": "other@example.org",
                    "password": "correct horse battery",
                    "display_name": "Other",
                },
            )
            other = login(client, "other@example.org")
            own = client.get(
                PATH, headers={"Authorization": "Bearer " + other["access_token"]}
            ).json()
            assert own["email"] == "other@example.org" and own["id"] != original["id"]
    finally:
        engine.dispose()


def test_password_change_revokes_every_session_and_preserves_on_failure(
    database_url, tmp_path, capsys
):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            first = login(client)
            second = login(client)
            cookie = client.cookies.get("forma_refresh")
            headers = {"Authorization": "Bearer " + first["access_token"]}
            with engine.connect() as db:
                old_hash = db.scalar(text("SELECT password_hash FROM users"))
            for payload, status in [
                ({"current_password": "incorrect", "new_password": NEW}, 401),
                ({"current_password": "correct horse battery", "new_password": "short"}, 422),
            ]:
                assert (
                    client.post(
                        PATH + "/change-password", headers=headers, json=payload
                    ).status_code
                    == status
                )
                assert client.get(PATH, headers=headers).status_code == 200
                with engine.connect() as db:
                    assert db.scalar(text("SELECT password_hash FROM users")) == old_hash
            changed = client.post(
                PATH + "/change-password",
                headers=headers,
                json={"current_password": "correct horse battery", "new_password": NEW},
            )
            assert changed.status_code == 204 and not changed.content
            assert "Max-Age=0" in changed.headers["set-cookie"]
            for token in [first, second]:
                assert (
                    client.get(
                        PATH, headers={"Authorization": "Bearer " + token["access_token"]}
                    ).status_code
                    == 401
                )
            assert (
                client.post(
                    "/api/v1/auth/refresh",
                    headers={
                        "Origin": "https://forma.example.org",
                        "X-CSRF-Token": second["csrf_token"],
                        "Cookie": f"forma_refresh={cookie}",
                    },
                ).status_code
                == 401
            )
            assert (
                client.post(
                    "/api/v1/auth/login",
                    headers={"Origin": "https://forma.example.org"},
                    json={"email": "owner@example.org", "password": "correct horse battery"},
                ).status_code
                == 401
            )
            assert (
                client.post(
                    "/api/v1/auth/login",
                    headers={"Origin": "https://forma.example.org"},
                    json={"email": "owner@example.org", "password": NEW},
                ).status_code
                == 200
            )
            with engine.connect() as db:
                hashed = db.scalar(text("SELECT password_hash FROM users"))
                assert hashed != old_hash and NEW not in hashed and hashed.startswith("scrypt$v1$")
                assert (
                    db.scalar(
                        text("SELECT count(*) FROM auth_sessions WHERE revoked_at IS NOT NULL")
                    )
                    == 2
                )
            output = capsys.readouterr().out
            assert (
                NEW not in output and first["access_token"] not in output and old_hash not in output
            )
    finally:
        engine.dispose()


def test_concurrent_password_changes_check_latest_hash(database_url, tmp_path, monkeypatch):
    from forma_backend.infrastructure.identity.profile_store import SqlProfileStore

    client, engine = setup_client(database_url, tmp_path)
    barrier = Barrier(2)
    original = SqlProfileStore.account

    def concurrent(self, identifier, lock=False):
        if lock:
            barrier.wait(timeout=10)
        return original(self, identifier, lock)

    monkeypatch.setattr(SqlProfileStore, "account", concurrent)
    try:
        with client:
            token = login(client)

            def change(password):
                with TestClient(client.app, base_url="https://forma.example.org") as browser:
                    return browser.post(
                        PATH + "/change-password",
                        headers={"Authorization": "Bearer " + token["access_token"]},
                        json={
                            "current_password": "correct horse battery",
                            "new_password": password,
                        },
                    ).status_code

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(change, [NEW, NEW + " two"]))
            assert sorted(results) == [204, 401]
    finally:
        engine.dispose()


def test_login_cannot_create_session_using_old_password_during_change(
    database_url, tmp_path, monkeypatch
):
    from forma_backend.infrastructure.identity.passwords import ScryptPasswordHasher
    from forma_backend.infrastructure.identity.session_store import SqlSessionStore

    client, engine = setup_client(database_url, tmp_path)
    locked, attempted, release = Event(), Event(), Event()
    verify, find = ScryptPasswordHasher.verify, SqlSessionStore.user_by_email
    try:
        with client:
            token = login(client)

            def paused(self, password, encoded):
                locked.set()
                assert release.wait(10)
                return verify(self, password, encoded)

            def tracked(self, email):
                attempted.set()
                return find(self, email)

            monkeypatch.setattr(ScryptPasswordHasher, "verify", paused)
            monkeypatch.setattr(SqlSessionStore, "user_by_email", tracked)

            def change():
                with TestClient(client.app) as browser:
                    return browser.post(
                        PATH + "/change-password",
                        headers={"Authorization": "Bearer " + token["access_token"]},
                        json={"current_password": "correct horse battery", "new_password": NEW},
                    ).status_code

            def old_login():
                with TestClient(client.app) as browser:
                    return browser.post(
                        "/api/v1/auth/login",
                        headers={"Origin": "https://forma.example.org"},
                        json={"email": "owner@example.org", "password": "correct horse battery"},
                    ).status_code

            with ThreadPoolExecutor(max_workers=2) as executor:
                changing = executor.submit(change)
                try:
                    assert locked.wait(10)
                    logging_in = executor.submit(old_login)
                    assert attempted.wait(10)
                finally:
                    release.set()
                assert changing.result(timeout=10) == 204
                assert logging_in.result(timeout=10) == 401
            with engine.connect() as db:
                assert (
                    db.scalar(text("SELECT count(*) FROM auth_sessions WHERE revoked_at IS NULL"))
                    == 0
                )
    finally:
        release.set()
        engine.dispose()


def test_password_change_rolls_back_hash_if_revocation_fails(database_url, tmp_path, monkeypatch):
    from forma_backend.infrastructure.identity.profile_store import SqlProfileStore

    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            token = login(client)

            def failed(self, user_id, now):
                raise RuntimeError("revocation fault")

            monkeypatch.setattr(SqlProfileStore, "revoke_all", failed)
            with engine.connect() as db:
                old_hash = db.scalar(text("SELECT password_hash FROM users"))
            response = client.post(
                PATH + "/change-password",
                headers={"Authorization": "Bearer " + token["access_token"]},
                json={"current_password": "correct horse battery", "new_password": NEW},
            )
            assert response.status_code == 500
            with engine.connect() as db:
                assert db.scalar(text("SELECT password_hash FROM users")) == old_hash
                assert (
                    db.scalar(text("SELECT count(*) FROM auth_sessions WHERE revoked_at IS NULL"))
                    == 1
                )
            assert (
                client.get(
                    PATH, headers={"Authorization": "Bearer " + token["access_token"]}
                ).status_code
                == 200
            )
    finally:
        engine.dispose()


def test_password_change_quota_is_per_authenticated_user(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            token = login(client)
            headers = {"Authorization": "Bearer " + token["access_token"]}
            for _ in range(10):
                assert (
                    client.post(
                        PATH + "/change-password",
                        headers=headers,
                        json={"current_password": "incorrect", "new_password": NEW},
                    ).status_code
                    == 401
                )
            limited = client.post(
                PATH + "/change-password",
                headers=headers,
                json={"current_password": "correct horse battery", "new_password": NEW},
            )
            assert limited.status_code == 429 and limited.headers["Retry-After"] == "900"
            assert client.get(PATH, headers=headers).status_code == 200
    finally:
        engine.dispose()
