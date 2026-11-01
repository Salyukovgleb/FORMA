"""CreateProject HTTP boundary; ownership comes only from the authenticated principal."""

from collections.abc import Callable
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends
from forma_backend.core.contracts import ErrorEnvelope
from forma_backend.core.errors import ApiError
from forma_backend.modules.identity.sessions import Principal
from forma_backend.modules.projects.application import CreateProject, ProjectFailure
from forma_backend.modules.projects.schemas import Project, ProjectCreate


def project_router(service: CreateProject, principal: Callable[..., Principal]) -> APIRouter:
    router = APIRouter(responses={code: {"model": ErrorEnvelope} for code in (401, 404, 413, 415)})

    @router.post(
        "/api/v1/projects",
        status_code=201,
        response_model=Project,
        operation_id="create_project",
        tags=["projects"],
        openapi_extra={"x-endpoint-id": "API-014", "x-status": "implemented"},
    )
    def create(payload: ProjectCreate, actor: Annotated[Principal, Depends(principal)]) -> Project:
        try:
            record = service.execute(actor, payload.title, payload.description, payload.template_id)
        except ProjectFailure as error:
            raise ApiError(
                error.status,
                error.code,
                "Project request failed",
                86400 if error.status == 429 else None,
            ) from None
        return Project(**asdict(record), role="owner")

    return router
