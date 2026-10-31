"""Shared implemented wire models, also imported by the design contract generator."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorDetail(DTO):
    field: str | None = None
    current_revision: int | None = None
    retry_after: int | None = None
    reason: str | None = None


class Error(DTO):
    code: str
    message: str
    details: ErrorDetail
    request_id: UUID


class ErrorEnvelope(DTO):
    error: Error


class Health(DTO):
    status: Literal["ok", "unavailable"]
