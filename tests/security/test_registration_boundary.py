from fastapi.testclient import TestClient
from forma_backend.core.config import load_settings
from forma_backend.main import create_app


def test_registration_bounds_precede_database_access(tmp_path):
    settings = load_settings(
        {
            "APP_ENV": "test",
            "DATABASE_URL": "postgresql+psycopg://unused:secret@127.0.0.1:1/unused",
            "JWT_SECRET": "a" * 64,
            "STORAGE_ROOT": str(tmp_path),
        }
    )
    with TestClient(create_app(settings)) as client:
        unsupported = client.post("/api/v1/auth/register", content="text")
        assert unsupported.status_code == 415
        large = client.post(
            "/api/v1/auth/register",
            content=iter([b"x" * 1048576, b"x" * 1048577]),
            headers={"Content-Type": "application/json"},
        )
        assert large.status_code == 413
        assert large.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_password_is_not_in_request_representation():
    from forma_backend.modules.identity.schemas import Register

    payload = Register(
        email="owner@example.org", password="secret-sentinel-long", display_name="Owner"
    )
    assert "secret-sentinel-long" not in repr(payload)


def test_invalid_unicode_is_rejected_before_database(tmp_path):
    import json

    settings = load_settings(
        {
            "APP_ENV": "test",
            "DATABASE_URL": "postgresql+psycopg://unused:secret@127.0.0.1:1/unused",
            "JWT_SECRET": "a" * 64,
            "STORAGE_ROOT": str(tmp_path),
        }
    )
    with TestClient(create_app(settings)) as client:
        for name in ["bad\x00name", "bad\ud800name"]:
            response = client.post(
                "/api/v1/auth/register",
                content=json.dumps(
                    {
                        "email": "owner@example.org",
                        "password": "correct horse battery",
                        "display_name": name,
                    }
                ),
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == 422
