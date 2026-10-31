from fastapi.testclient import TestClient

from forma_backend.core.config import load_settings
from forma_backend.main import create_app


def test_readiness_with_real_postgres_and_persistent_storage(database_url, tmp_path):
    settings = load_settings(
        {
            "APP_ENV": "test",
            "DATABASE_URL": database_url.render_as_string(hide_password=False),
            "JWT_SECRET": "a" * 64,
            "STORAGE_ROOT": str(tmp_path),
        }
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/ready")
        assert response.status_code == 200 and response.json() == {"status": "ok"}
        assert list(tmp_path.iterdir()) == []


def test_readiness_rejects_unavailable_storage(database_url, tmp_path):
    settings = load_settings(
        {
            "APP_ENV": "test",
            "DATABASE_URL": database_url.render_as_string(hide_password=False),
            "JWT_SECRET": "a" * 64,
            "STORAGE_ROOT": str(tmp_path / "absent"),
        }
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "STORAGE_UNAVAILABLE"
        assert "absent" not in response.text
