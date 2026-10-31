"""Real PostgreSQL rate windows/concurrency; only boundary clock is controlled in tests."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, text

from forma_backend.infrastructure.identity.rate_limit import (
    AuthRateLimit,
    consume_bucket,
    subject_hash,
)
from test_registration import app
from test_sessions import login, setup_client


@contextmanager
def clock(engine, epoch):
    # Keep the real PostgreSQL UPSERT/locks; freeze only its DB clock expression.
    def statement(conn, cursor, query, parameters, context, many):
        if "INSERT INTO rate_limit_buckets" in query:
            assert "now()" in query or "statement_timestamp()" in query
            query = query.replace("now()", f"to_timestamp({float(epoch)})").replace(
                "statement_timestamp()", f"to_timestamp({float(epoch)})"
            )
        return query, parameters

    event.listen(engine, "before_cursor_execute", statement, retval=True)
    try:
        yield
    finally:
        event.remove(engine, "before_cursor_execute", statement)


def burst(limiter, subject):
    ready = Barrier(24)

    def attempt(_):
        ready.wait(timeout=15)
        return limiter.consume(subject)

    with ThreadPoolExecutor(max_workers=24) as pool:
        return list(pool.map(attempt, range(24)))


def test_atomic_bursts_on_both_sides_of_window_boundary(database_url, tmp_path):
    _, engine = app(database_url, tmp_path)
    limiter = AuthRateLimit(engine, "a" * 64)
    try:
        with clock(engine, 1793416499.999):
            assert sum(burst(limiter, "peer")) == 10
        with clock(engine, 1793416500.0):
            assert sum(burst(limiter, "peer")) == 10
            assert not limiter.consume("peer")
        with engine.connect() as db:
            counts = (
                db.execute(text("SELECT count FROM rate_limit_buckets ORDER BY window_start"))
                .scalars()
                .all()
            )
            assert counts == [24, 25]
            assert (
                db.scalar(text("SELECT count(DISTINCT subject_hash) FROM rate_limit_buckets")) == 1
            )
            assert db.scalar(
                text("SELECT subject_hash FROM rate_limit_buckets LIMIT 1")
            ) == subject_hash(b"a" * 64, "peer")
    finally:
        engine.dispose()


def test_current_statement_clock_is_used_in_long_transaction(database_url, tmp_path):
    _, engine = app(database_url, tmp_path)
    try:
        with engine.begin() as db:
            started = db.scalar(text("SELECT floor(extract(epoch FROM now()))"))
            db.execute(text("SELECT pg_sleep(1.1)"))
            assert consume_bucket(db, "clock-test", "a" * 64, 1, 1)
            window = db.scalar(
                text(
                    "SELECT extract(epoch FROM window_start) FROM rate_limit_buckets WHERE scope='clock-test'"
                )
            )
            assert window > started
    finally:
        engine.dispose()


@pytest.mark.parametrize("mode", ["ip", "email"])
def test_login_limits_apply_to_socket_ip_and_normalized_email(database_url, tmp_path, mode):
    application, engine = app(database_url, tmp_path)
    try:
        # No accounts are needed: unknown-account attempts pay the dummy KDF cost too.
        with clock(engine, 1793416600):
            for attempt in range(11):
                peer = f"10.0.0.{attempt + 1}" if mode == "email" else "10.0.0.1"
                email = (
                    "  Owner@Example.org  " if mode == "email" else f"missing{attempt}@example.org"
                )
                with TestClient(application, client=(peer, 50000)) as client:
                    response = client.post(
                        "/api/v1/auth/login",
                        headers={
                            "Origin": "https://forma.example.org",
                            "X-Forwarded-For": f"172.16.0.{attempt + 1}",
                        },
                        json={"email": email, "password": "wrong sentinel password"},
                    )
                assert response.status_code == (401 if attempt < 10 else 429)
            assert response.headers["Retry-After"] == "900"
        with engine.connect() as db:
            assert db.scalar(text("SELECT count(*) FROM auth_sessions")) == 0
            assert (
                db.scalar(
                    text("SELECT count(*) FROM rate_limit_buckets WHERE subject_hash LIKE '%@%'")
                )
                == 0
            )
    finally:
        engine.dispose()


def test_refresh_limit_commits_rejection_without_rotating_or_revoking(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client, clock(engine, 1793416600):
            token = login(client)
            with engine.connect() as db:
                expiry = db.scalar(text("SELECT expires_at FROM auth_sessions"))
            for _ in range(30):
                response = client.post(
                    "/api/v1/auth/refresh",
                    headers={
                        "Origin": "https://forma.example.org",
                        "X-CSRF-Token": token["csrf_token"],
                    },
                )
                assert response.status_code == 200
                token = response.json()
            cookie = client.cookies.get("forma_refresh")
            for expected in [31, 32]:
                response = client.post(
                    "/api/v1/auth/refresh",
                    headers={
                        "Origin": "https://forma.example.org",
                        "X-CSRF-Token": token["csrf_token"],
                    },
                )
                assert response.status_code == 429 and response.headers["Retry-After"] == "60"
                assert "set-cookie" not in response.headers
                assert client.cookies.get("forma_refresh") == cookie
                with engine.connect() as db:
                    assert (
                        db.scalar(
                            text(
                                "SELECT count FROM rate_limit_buckets WHERE scope='refresh-session'"
                            )
                        )
                        == expected
                    )
            assert (
                client.get(
                    "/api/v1/users/me", headers={"Authorization": "Bearer " + token["access_token"]}
                ).status_code
                == 200
            )
            with engine.connect() as db:
                assert db.scalar(text("SELECT expires_at FROM auth_sessions")) == expiry
                assert db.scalar(text("SELECT count(*) FROM used_refresh_tokens")) == 30
                assert (
                    db.scalar(text("SELECT count(*) FROM auth_sessions WHERE revoked_at IS NULL"))
                    == 1
                )
    finally:
        engine.dispose()


def test_expired_bucket_cleanup_is_bounded_skips_locks_and_preserves_current(
    database_url, tmp_path
):
    from forma_backend.infrastructure.identity.cleanup_limits import purge_expired_buckets

    _, engine = app(database_url, tmp_path)
    try:
        with engine.begin() as db:
            db.execute(
                text(
                    "INSERT INTO rate_limit_buckets(scope,subject_hash,window_start,count) SELECT 'old',lpad(n::text,64,'0'),now()-interval '25 hours',1 FROM generate_series(1,5) n"
                )
            )
            db.execute(
                text(
                    "INSERT INTO rate_limit_buckets(scope,subject_hash,window_start,count) VALUES ('current',:hash,now(),10)"
                ),
                {"hash": "b" * 64},
            )
        with engine.begin() as locked:
            locked.execute(
                text(
                    "SELECT 1 FROM rate_limit_buckets WHERE scope='old' AND subject_hash=:hash FOR UPDATE"
                ),
                {"hash": "0" * 63 + "1"},
            )
            with engine.begin() as db:
                db.execute(text("SET LOCAL lock_timeout='500ms'"))
                assert purge_expired_buckets(db, 2) == 2
            with engine.connect() as db:
                assert purge_expired_buckets(db, 10) == 2
                # Rollback must preserve these rows.
            with engine.begin() as db:
                assert purge_expired_buckets(db, 10) == 2
        with engine.begin() as db:
            assert purge_expired_buckets(db, 10) == 1
        with engine.connect() as db:
            assert db.execute(text("SELECT scope,count FROM rate_limit_buckets")).all() == [
                ("current", 10)
            ]
            for invalid in [0, -1, 10001]:
                with pytest.raises(ValueError):
                    purge_expired_buckets(db, invalid)
    finally:
        engine.dispose()


def test_operator_cleanup_command_commits_and_hides_configuration_errors(database_url, tmp_path):
    import subprocess
    import sys

    _, engine = app(database_url, tmp_path)
    try:
        with engine.begin() as db:
            db.execute(
                text(
                    "INSERT INTO rate_limit_buckets(scope,subject_hash,window_start,count) VALUES ('old',:hash,now()-interval '25 hours',1)"
                ),
                {"hash": "a" * 64},
            )
        env = {
            "APP_ENV": "test",
            "DATABASE_URL": database_url.render_as_string(hide_password=False),
            "JWT_SECRET": "secret-sentinel" * 4,
            "STORAGE_ROOT": str(tmp_path),
        }
        command = [sys.executable, "-m", "forma_backend.infrastructure.identity.cleanup_limits"]
        result = subprocess.run(
            command + ["--max-rows", "1"], env=env, capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0 and result.stdout.strip() == "removed=1"
        with engine.connect() as db:
            assert db.scalar(text("SELECT count(*) FROM rate_limit_buckets")) == 0
        bad_env = {
            **env,
            "DATABASE_URL": "postgresql+psycopg://user:secret-sentinel@127.0.0.1:1/unused",
        }
        failed = subprocess.run(command, env=bad_env, capture_output=True, text=True, timeout=10)
        assert failed.returncode == 1
        assert failed.stderr.strip() == "Auth rate bucket cleanup failed"
        assert "secret-sentinel" not in failed.stdout + failed.stderr
        invalid = subprocess.run(
            command + ["--max-rows", "0"], env={}, capture_output=True, text=True, timeout=10
        )
        assert invalid.returncode == 2 and "between 1 and 10000" in invalid.stderr
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "invalidate",
    [
        "UPDATE users SET is_active=false",
        "UPDATE auth_sessions SET created_at=now()-interval '2 minutes', expires_at=now()-interval '1 minute'",
        "UPDATE auth_sessions SET revoked_at=now()",
    ],
)
def test_refresh_cannot_revive_disabled_expired_or_revoked_session(
    database_url, tmp_path, invalidate
):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            token = login(client)
            cookie = client.cookies.get("forma_refresh")
            with engine.begin() as db:
                db.execute(text(invalidate))
                old_hash = db.scalar(text("SELECT refresh_token_hash FROM auth_sessions"))
            response = client.post(
                "/api/v1/auth/refresh",
                headers={
                    "Origin": "https://forma.example.org",
                    "X-CSRF-Token": token["csrf_token"],
                    "Cookie": f"forma_refresh={cookie}",
                },
            )
            assert response.status_code == 401 and "set-cookie" not in response.headers
            assert (
                client.get(
                    "/api/v1/users/me", headers={"Authorization": "Bearer " + token["access_token"]}
                ).status_code
                == 401
            )
            with engine.connect() as db:
                assert db.scalar(text("SELECT refresh_token_hash FROM auth_sessions")) == old_hash
                assert db.scalar(text("SELECT count(*) FROM used_refresh_tokens")) == 0
    finally:
        engine.dispose()
