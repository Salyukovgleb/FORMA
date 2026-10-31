"""Implemented identity transport models, shared with the design registry."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BeforeValidator, Field, field_validator
from forma_backend.core.contracts import DTO


def normalize_email(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


Email = Annotated[
    str,
    Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$"),
    BeforeValidator(normalize_email),
]
Password = Annotated[str, Field(min_length=12, max_length=128)]


class Register(DTO):
    email: Email
    password: Password = Field(repr=False)
    display_name: Annotated[str, Field(min_length=1, max_length=100)]

    @field_validator("email", "password", "display_name")
    @classmethod
    def valid_text(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("NUL is not allowed")
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("Invalid Unicode") from None
        return value


class Profile(DTO):
    id: UUID
    email: Email
    display_name: str
    created_at: datetime
