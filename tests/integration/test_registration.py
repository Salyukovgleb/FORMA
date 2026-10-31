from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from forma_backend.core.config import load_settings
from forma_backend.infrastructure.database.session import create_database_engine
from forma_backend.main import create_app
from forma_backend.infrastructure.identity.passwords import ScryptPasswordHasher


def app(database_url, tmp_path):
    engine = create_database_engine(database_url)
    with engine.begin() as conn:
        config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
        config.attributes["connection"] = conn
        command.upgrade(config, "head")
    settings = load_settings(
        {
            "APP_ENV": "test",
            "DATABASE_URL": database_url.render_as_string(hide_password=False),
            "JWT_SECRET": "a" * 64,
            "STORAGE_ROOT": str(tmp_path),
        }
    )
    return create_app(settings, engine=engine), engine


def test_register_duplicate_and_no_session(database_url, tmp_path, capsys):
    application, engine = app(database_url, tmp_path)
    try:
        with TestClient(application) as client:
            payload = {
                "email": "  Owner@Example.org  ",
                "password": "secret-sentinel-long",
                "display_name": "Владелец",
            }
            response = client.post("/api/v1/auth/register", json=payload)
            assert response.status_code == 201, response.text
            profile = response.json()
            UUID(profile["id"])
            assert profile["email"] == "owner@example.org"
            assert set(profile) == {"id", "email", "display_name", "created_at"}
            assert "set-cookie" not in response.headers
            duplicate = client.post(
                "/api/v1/auth/register", json={**payload, "email": "OWNER@example.org"}
            )
            assert (
                duplicate.status_code == 409 and duplicate.json()["error"]["code"] == "EMAIL_TAKEN"
            )
            for bad in [{**payload, "email": "invalid"}, {**payload, "password": "short"}]:
                assert client.post("/api/v1/auth/register", json=bad).status_code == 422
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT password_hash FROM users")).scalars().all()
            assert len(rows) == 1 and ScryptPasswordHasher().verify(payload["password"], rows[0])
            assert conn.scalar(text("SELECT count(*) FROM auth_sessions")) == 0
        assert payload["password"] not in capsys.readouterr().out
    finally:
        engine.dispose()


def test_concurrent_registration_has_single_winner(database_url, tmp_path):
    application, engine = app(database_url, tmp_path)
    payload = {
        "email": "race@example.org",
        "password": "correct horse battery",
        "display_name": "Race",
    }
    try:
        with TestClient(application) as client:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(
                    pool.map(
                        lambda _: client.post("/api/v1/auth/register", json=payload).status_code,
                        range(2),
                    )
                )
            assert sorted(results) == [201, 409]
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT count(*) FROM users")) == 1
    finally:
        engine.dispose()


def test_registration_ip_limit_cannot_be_bypassed_with_forwarded_header(database_url, tmp_path):
    from forma_backend.infrastructure.identity.rate_limit import RegistrationRateLimit

    application, engine = app(database_url, tmp_path)
    try:
        limiter = RegistrationRateLimit(engine, "a" * 64)
        for _ in range(10):
            assert limiter.consume("testclient")
        with TestClient(application) as client:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "limit@example.org",
                    "password": "correct horse battery",
                    "display_name": "Limited",
                },
                headers={"X-Forwarded-For": "1.2.3.4"},
            )
            assert response.status_code == 429 and response.headers["retry-after"] == "900"
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT count(*) FROM users")) == 0
            assert conn.scalar(text("SELECT subject_hash FROM rate_limit_buckets")) != "testclient"
    finally:
        engine.dispose()
