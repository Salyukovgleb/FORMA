import pytest
from fastapi.testclient import TestClient
from forma_backend.core.config import load_settings
from forma_backend.main import create_app


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/api/v1/projects"),
        ("POST", "/api/v1/auth/register"),
        ("POST", "/api/v1/auth/login"),
        ("PATCH", "/api/v1/users/me"),
        ("POST", "/api/v1/users/me/change-password"),
    ],
)
def test_registration_bounds_precede_database_access(tmp_path, method, path):
    settings = load_settings(
        {
            "APP_ENV": "test",
            "DATABASE_URL": "postgresql+psycopg://unused:secret@127.0.0.1:1/unused",
            "JWT_SECRET": "a" * 64,
            "STORAGE_ROOT": str(tmp_path),
        }
    )
    with TestClient(create_app(settings)) as client:
        unsupported = client.request(method, path, content="text")
        assert unsupported.status_code == 415
        large = client.request(
            method,
            path,
            content=iter([b"x" * 1048576, b"x" * 1048577]),
            headers={"Content-Type": "application/json", "Origin": "http://localhost:3000"},
        )
        assert large.status_code == 413
        assert large.headers["access-control-allow-origin"] == "http://localhost:3000"
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


def test_password_change_secrets_are_not_in_dto_repr():
    from forma_backend.modules.identity.profile_schemas import PasswordChange

    request = PasswordChange(
        current_password="old-password-sentinel", new_password="new-password-sentinel"
    )
    assert "old-password-sentinel" not in repr(request)
    assert "new-password-sentinel" not in repr(request)
