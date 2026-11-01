"""Implemented project wire models, shared with the canonical contract."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, field_validator
from forma_backend.core.contracts import DTO
from forma_backend.core.text import valid_text


class ProjectCreate(DTO):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(max_length=2000)] = ""
    template_id: Annotated[str, Field(min_length=1, max_length=128)] | None = None

    @field_validator("title", "description", "template_id")
    @classmethod
    def text_fields(cls, value: str | None) -> str | None:
        return valid_text(value) if value is not None else None

    @field_validator("title")
    @classmethod
    def meaningful_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title must contain non-whitespace text")
        return value


class Project(DTO):
    id: UUID
    owner_id: UUID
    title: str
    description: str
    role: Literal["owner", "editor", "viewer"]
    status: Literal["active", "deleted"]
    revision: Annotated[int, Field(ge=1)]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ProjectPatch(DTO):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(max_length=2000)]
    expected_revision: Annotated[int, Field(ge=1)]

    @field_validator("title")
    @classmethod
    def title_text(cls, value: str) -> str:
        return ProjectCreate.meaningful_title(valid_text(value))

    @field_validator("description")
    @classmethod
    def description_text(cls, value: str) -> str:
        return valid_text(value)


class DeleteProject(DTO):
    confirm_title: Annotated[str, Field(min_length=1, max_length=200)]
    expected_revision: Annotated[int, Field(ge=1)]

    @field_validator("confirm_title")
    @classmethod
    def title_text(cls, value: str) -> str:
        return valid_text(value)


class RestoreProject(DTO):
    expected_revision: Annotated[int, Field(ge=1)]
