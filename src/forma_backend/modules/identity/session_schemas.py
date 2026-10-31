"""Implemented session wire contracts."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, field_validator
from forma_backend.core.contracts import DTO, Page
from forma_backend.modules.identity.schemas import Email, Register


class Login(DTO):
    email: Email
    password: Annotated[str, Field(min_length=1, max_length=128, repr=False)]

    @field_validator("password")
    @classmethod
    def valid_text(cls, value: str) -> str:
        return Register.valid_text(value)


class Token(DTO):
    access_token: str = Field(repr=False)
    token_type: Literal["bearer"] = "bearer"
    expires_in: Literal[600] = 600
    csrf_token: str = Field(repr=False)


class Session(DTO):
    id: UUID
    created_at: datetime
    expires_at: datetime
    is_current: bool


SessionPage = Page[Session]
