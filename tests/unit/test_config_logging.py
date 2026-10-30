import asyncio
import json
import logging
from uuid import UUID

import pytest

from forma_backend.core.config import ConfigurationError, load_settings
from forma_backend.core.logging import JsonFormatter, request_context


def environment():
    return {
        "APP_ENV": "production",
        "DATABASE_URL": "postgresql+psycopg://forma:secret@db/forma",
        "JWT_SECRET": "a" * 64,
        "STORAGE_ROOT": "/var/lib/forma",
        "ALLOWED_ORIGINS": "https://forma.example.org",
        "COOKIE_SECURE": "true",
    }


def test_valid_production_config():
    settings = load_settings(environment())
    assert settings.cookie_secure
    assert settings.worker_slots == 1
    assert settings.allowed_origins == ("https://forma.example.org",)
    assert "a" * 64 not in repr(settings)


@pytest.mark.parametrize(
    "key,value",
    [
        ("JWT_SECRET", ""),
        ("COOKIE_SECURE", "false"),
        ("ALLOWED_ORIGINS", "*"),
        ("ALLOWED_ORIGINS", "http://forma.example.org"),
        ("STORAGE_ROOT", "relative"),
        ("JOB_HEARTBEAT_SECONDS", "30"),
        ("DATABASE_URL", "sqlite:///db"),
        ("APP_ENV", "prodution"),
        ("WORKER_SLOTS", "0"),
    ],
)
def test_invalid_production_configuration(key, value):
    env = environment()
    env[key] = value
    with pytest.raises(ConfigurationError):
        load_settings(env)


def test_invalid_input_error_does_not_expose_secrets():
    env = environment()
    env["DATABASE_URL"] = "secret-sentinel-invalid-url"
    with pytest.raises(ConfigurationError) as error:
        load_settings(env)
    assert "secret-sentinel" not in str(error.value)


def test_safe_json_logging_and_context_reset():
    record = logging.LogRecord(
        "forma", logging.ERROR, __file__, 1, "password secret-sentinel", (), None
    )
    record.event = "request_completed"
    record.authorization = "Bearer secret-sentinel"
    formatter = JsonFormatter()
    with request_context("11111111-1111-4111-8111-111111111111") as request_id:
        data = json.loads(formatter.format(record))
        assert data["request_id"] == str(request_id)
        assert data["event"] == "request_completed"
        assert "secret-sentinel" not in formatter.format(record)
    assert json.loads(formatter.format(record))["request_id"] is None


def test_concurrent_contexts_are_isolated():
    async def worker():
        with request_context("invalid") as identifier:
            await asyncio.sleep(0)
            record = logging.LogRecord("forma", logging.INFO, __file__, 1, "ignored", (), None)
            assert json.loads(JsonFormatter().format(record))["request_id"] == str(identifier)
            return identifier

    async def run():
        return await asyncio.gather(worker(), worker())

    first, second = asyncio.run(run())
    assert isinstance(first, UUID) and first != second
