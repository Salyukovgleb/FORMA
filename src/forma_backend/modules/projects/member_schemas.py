"""Implemented membership DTOs shared with canonical contracts."""

from pydantic import field_validator
from forma_backend.core.text import valid_text
from datetime import datetime
from typing import Literal
from uuid import UUID
from forma_backend.core.contracts import DTO
from forma_backend.modules.identity.schemas import Email


class MemberAdd(DTO):
    email: Email
    role: Literal["editor", "viewer"]

    @field_validator("email")
    @classmethod
    def text_email(cls, value: str) -> str:
        return valid_text(value)


class MemberPatch(DTO):
    role: Literal["editor", "viewer"]


class Member(DTO):
    user_id: UUID
    display_name: str
    role: Literal["owner", "editor", "viewer"]
    created_at: datetime


class Members(DTO):
    items: list[Member]
