import json
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from forma_backend.core.config import load_settings
from forma_backend.main import create_app


def settings(tmp_path, production=False):
    return load_settings(
        {
            "APP_ENV": "production" if production else "test",
            "DATABASE_URL": "postgresql+psycopg://unused:secret-sentinel@127.0.0.1:1/unused",
            "JWT_SECRET": "a" * 64,
            "STORAGE_ROOT": str(tmp_path),
            "ALLOWED_ORIGINS": "https://forma.example.org",
            "COOKIE_SECURE": "true",
        }
    )


def test_live_without_database_and_safe_ready_failure(tmp_path):
    with TestClient(create_app(settings(tmp_path))) as client:
        live = client.get(
            "/health/live", headers={"X-Request-ID": "11111111-1111-4111-8111-111111111111"}
        )
        assert live.status_code == 200 and live.json() == {"status": "ok"}
        assert live.headers["x-request-id"] == "11111111-1111-4111-8111-111111111111"
        ready = client.get("/health/ready", headers={"X-Request-ID": "invalid"})
        assert ready.status_code == 503
        assert ready.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert str(UUID(ready.headers["x-request-id"])) == ready.json()["error"]["request_id"]
        assert "secret-sentinel" not in ready.text
        assert ready.headers["cache-control"] == "no-store"
        assert ready.headers["x-content-type-options"] == "nosniff"


def schema_without_null_defaults(value):
    # FastAPI omits default:null annotations. They do not alter JSON Schema validation.
    if isinstance(value, dict):
        return {
            k: schema_without_null_defaults(v)
            for k, v in value.items()
            if not (k == "default" and v is None)
        }
    if isinstance(value, list):
        return [schema_without_null_defaults(v) for v in value]
    return value


def test_errors_and_runtime_openapi(tmp_path):
    app = create_app(settings(tmp_path))

    class Input(BaseModel):
        count: int

    # These diagnostic routes exist only in the test app, not in runtime.
    @app.post("/_validation", include_in_schema=False)
    def validate_input(value: Input):
        return value

    @app.get("/_failure", include_in_schema=False)
    def fail():
        raise RuntimeError("secret-sentinel")

    @app.get("/_forbidden", include_in_schema=False)
    def forbidden():
        raise HTTPException(403, detail="secret-sentinel")

    with TestClient(app) as client:
        for path, code, status in [
            ("/missing", "NOT_FOUND", 404),
            ("/_failure", "INTERNAL_ERROR", 500),
            ("/_forbidden", "FORBIDDEN", 403),
        ]:
            response = client.get(path)
            assert response.status_code == status and response.json()["error"]["code"] == code
            assert "secret-sentinel" not in response.text
        response = client.post("/_validation", json={"count": "secret-sentinel"})
        assert (
            response.status_code == 422 and response.json()["error"]["code"] == "VALIDATION_ERROR"
        )
        assert "secret-sentinel" not in response.text
        spec = client.get("/openapi.json").json()
        assert set(spec["paths"]) == {"/health/live", "/health/ready", "/api/v1/auth/register"}
        assert spec["paths"]["/health/ready"]["get"]["operationId"] == "readiness"
        assert client.get("/docs").status_code == 200
        canonical = json.loads(
            (Path(__file__).resolve().parents[2] / "docs/contracts/openapi.json").read_text()
        )
        for name in ["Health", "ErrorEnvelope", "Error", "ErrorDetail"]:
            assert schema_without_null_defaults(
                spec["components"]["schemas"][name]
            ) == schema_without_null_defaults(canonical["components"]["schemas"][name])
        for path in ["/health/live", "/health/ready"]:
            assert spec["paths"][path]["get"]["x-status"] == "implemented"
        assert client.post("/health/live").status_code == 405


def test_production_docs_disabled_and_explicit_cors(tmp_path):
    with TestClient(create_app(settings(tmp_path, True))) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        allowed = client.get("/health/live", headers={"Origin": "https://forma.example.org"})
        denied = client.get("/health/live", headers={"Origin": "https://evil.example.org"})
        assert allowed.headers["access-control-allow-origin"] == "https://forma.example.org"
        assert "access-control-allow-origin" not in denied.headers
        assert "secret-sentinel" not in json.dumps(dict(denied.headers))


def test_readiness_deadline_is_enforced(tmp_path, monkeypatch):
    from threading import Event
    from forma_backend import main

    release = Event()

    def blocked_probe(engine):
        release.wait(timeout=1)
        return True

    monkeypatch.setattr(main, "database_ready", blocked_probe)
    monkeypatch.setattr(main, "READINESS_TIMEOUT_SECONDS", 0.02)
    try:
        with TestClient(create_app(settings(tmp_path))) as client:
            response = client.get("/health/ready")
            assert response.status_code == 503
            assert response.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
            release.set()
    finally:
        release.set()


def test_request_secrets_are_not_logged(tmp_path, capsys):
    with TestClient(create_app(settings(tmp_path))) as client:
        response = client.get(
            "/health/live?token=secret-sentinel",
            headers={"Authorization": "Bearer secret-sentinel"},
        )
        assert response.status_code == 200
    output = capsys.readouterr().out
    assert "secret-sentinel" not in output
    assert response.headers["x-request-id"] in output
    for line in output.splitlines():
        assert isinstance(json.loads(line), dict)
