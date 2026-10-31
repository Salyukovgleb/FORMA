"""Implemented profile request models; reject extra fields and invalid Unicode."""

from typing import Annotated

from pydantic import Field, field_validator

from forma_backend.core.contracts import DTO
from forma_backend.modules.identity.schemas import Password, Register


class ProfilePatch(DTO):
    display_name: Annotated[str, Field(min_length=1, max_length=100)]

    @field_validator("display_name")
    @classmethod
    def valid_text(cls, value: str) -> str:
        return Register.valid_text(value)


class PasswordChange(DTO):
    current_password: Annotated[str, Field(min_length=1, max_length=128, repr=False)]
    new_password: Password = Field(repr=False)

    @field_validator("current_password", "new_password")
    @classmethod
    def valid_text(cls, value: str) -> str:
        return Register.valid_text(value)
