"""Explicit environment mapping; never expose secret input in startup errors."""

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, model_validator


class ConfigurationError(ValueError):
    """Safe configuration failure suitable for startup diagnostics."""


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    app_env: Literal["development", "test", "production"] = "development"
    database_url: SecretStr
    jwt_secret: SecretStr
    jwt_key_id: str = Field(default="v1", pattern=r"^[A-Za-z0-9_-]{1,32}$")
    jwt_previous_key_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,32}$")
    jwt_previous_secret: SecretStr | None = None
    jwt_issuer: str = Field(default="forma", min_length=1)
    jwt_audience: str = Field(default="forma-web", min_length=1)
    storage_root: Path = Path("/var/lib/forma")
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    cookie_secure: bool = True
    worker_slots: int = Field(default=1, ge=1, le=16)
    job_lease_seconds: int = Field(default=30, ge=3, le=300)
    job_heartbeat_seconds: int = Field(default=10, ge=1, le=100)
    project_quota_bytes: int = Field(default=524288000, ge=1)
    owner_quota_bytes: int = Field(default=2147483648, ge=1)

    @model_validator(mode="after")
    def validate_security(self) -> Self:
        secret = self.jwt_secret.get_secret_value()
        if len(secret.encode("utf-8")) < 32 or "CHANGE_ME" in secret:
            raise ValueError("JWT_SECRET must contain at least 32 secret bytes")
        if (self.jwt_previous_key_id is None) != (self.jwt_previous_secret is None):
            raise ValueError("Previous key ID and secret must be configured together")
        if self.jwt_previous_secret is not None:
            old = self.jwt_previous_secret.get_secret_value()
            if (
                self.jwt_previous_key_id == self.jwt_key_id
                or len(old.encode()) < 32
                or "CHANGE_ME" in old
            ):
                raise ValueError("Invalid previous signing key")
        database = urlsplit(self.database_url.get_secret_value())
        if (
            database.scheme != "postgresql+psycopg"
            or not database.hostname
            or not database.path.strip("/")
        ):
            raise ValueError("DATABASE_URL requires PostgreSQL host and database")
        if not database.username or not database.password or "CHANGE_ME" in database.password:
            raise ValueError("DATABASE_URL requires configured credentials")
        if not self.storage_root.is_absolute():
            raise ValueError("STORAGE_ROOT must be absolute")
        if self.job_heartbeat_seconds * 2 >= self.job_lease_seconds:
            raise ValueError("Heartbeat interval must be less than half of lease")
        if self.project_quota_bytes > self.owner_quota_bytes:
            raise ValueError("Project quota cannot exceed owner quota")
        if not self.allowed_origins:
            raise ValueError("An explicit origin allowlist is required")
        for origin in self.allowed_origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in ("http", "https")
                or not parsed.hostname
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username
            ):
                raise ValueError("Origins must be exact HTTP origins without paths or credentials")
            if self.app_env == "production" and parsed.scheme != "https":
                raise ValueError("Production origins require HTTPS")
        if self.app_env == "production" and not self.cookie_secure:
            raise ValueError("Production cookies require Secure")
        return self


def load_settings(environment: Mapping[str, str] | None = None) -> Settings:
    source = os.environ if environment is None else environment
    values: dict[str, object] = {}
    for name in Settings.model_fields:
        value = source.get(name.upper())
        if value is not None:
            if name in {"jwt_previous_key_id", "jwt_previous_secret"} and value == "":
                continue
            values[name] = (
                tuple(part.strip() for part in value.split(","))
                if name == "allowed_origins"
                else value
            )
    try:
        return Settings.model_validate(values)
    except ValidationError as error:
        fields = sorted(
            {
                str(item["loc"][0]) if item["loc"] else "security_policy"
                for item in error.errors(include_input=False, include_context=False)
            }
        )
        raise ConfigurationError("Invalid configuration: " + ", ".join(fields)) from None
