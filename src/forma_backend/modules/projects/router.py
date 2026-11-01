"""Project metadata HTTP boundary; authorization uses the authenticated principal."""

from collections.abc import Callable
from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from forma_backend.core.contracts import ErrorEnvelope, Page
from forma_backend.core.text import valid_text
from forma_backend.core.errors import ApiError
from forma_backend.modules.identity.sessions import Principal
from forma_backend.modules.projects.application import CreateProject
from forma_backend.modules.projects.crud import ProjectCrud, ProjectView, ProjectStatus
from forma_backend.modules.projects.cursor import encode_cursor, decode_cursor
from forma_backend.modules.projects.schemas import (
    Project,
    ProjectCreate,
    ProjectPatch,
    DeleteProject,
    RestoreProject,
)


def project_router(
    service: CreateProject, principal: Callable[..., Principal], crud: ProjectCrud
) -> APIRouter:
    router = APIRouter(
        responses={code: {"model": ErrorEnvelope} for code in (401, 403, 404, 409, 410, 413, 415)}
    )

    @router.post(
        "/api/v1/projects",
        status_code=201,
        response_model=Project,
        operation_id="create_project",
        tags=["projects"],
        openapi_extra={"x-endpoint-id": "API-014", "x-status": "implemented"},
    )
    def create(payload: ProjectCreate, actor: Annotated[Principal, Depends(principal)]) -> Project:
        record = service.execute(actor, payload.title, payload.description, payload.template_id)
        return Project(**asdict(record), role="owner")

    def view(result: ProjectView) -> Project:
        return Project(**asdict(result.record), role=result.role.value)

    @router.get(
        "/api/v1/projects",
        response_model=Page[Project],
        operation_id="list_projects",
        tags=["projects"],
        openapi_extra={"x-endpoint-id": "API-013", "x-status": "implemented"},
    )
    def listing(
        actor: Annotated[Principal, Depends(principal)],
        q: Annotated[str | None, Query(max_length=200)] = None,
        status: ProjectStatus = "active",
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        cursor: Annotated[str | None, Query(max_length=2048)] = None,
    ) -> Page[Project]:
        try:
            search = valid_text(q or "")
        except ValueError:
            raise ApiError(422, "VALIDATION_ERROR", "Invalid query") from None
        before = decode_cursor(cursor, actor.user_id, search, status) if cursor else None
        rows = crud.listing(actor, search, status, before, limit + 1)
        selected = rows[:limit]
        next_cursor = None
        if len(rows) > limit:
            last = selected[-1].record
            next_cursor = encode_cursor((last.created_at, last.id), actor.user_id, search, status)
        return Page[Project](items=[view(row) for row in selected], next_cursor=next_cursor)

    @router.get(
        "/api/v1/projects/{project_id}",
        response_model=Project,
        operation_id="read_project",
        tags=["projects"],
        openapi_extra={"x-endpoint-id": "API-015", "x-status": "implemented"},
    )
    def read(project_id: UUID, actor: Annotated[Principal, Depends(principal)]) -> Project:
        return view(crud.read(actor, project_id))

    @router.patch(
        "/api/v1/projects/{project_id}",
        response_model=Project,
        operation_id="update_project",
        tags=["projects"],
        openapi_extra={"x-endpoint-id": "API-016", "x-status": "implemented"},
    )
    def update(
        project_id: UUID, payload: ProjectPatch, actor: Annotated[Principal, Depends(principal)]
    ) -> Project:
        return view(
            crud.update(
                actor, project_id, payload.expected_revision, payload.title, payload.description
            )
        )

    @router.delete(
        "/api/v1/projects/{project_id}",
        status_code=204,
        operation_id="delete_project",
        tags=["projects"],
        openapi_extra={"x-endpoint-id": "API-017", "x-status": "implemented"},
    )
    def delete(
        project_id: UUID, payload: DeleteProject, actor: Annotated[Principal, Depends(principal)]
    ) -> Response:
        crud.delete(actor, project_id, payload.expected_revision, payload.confirm_title)
        return Response(status_code=204)

    @router.post(
        "/api/v1/projects/{project_id}/restore",
        response_model=Project,
        operation_id="restore_project",
        tags=["projects"],
        openapi_extra={"x-endpoint-id": "API-018", "x-status": "implemented"},
    )
    def restore(
        project_id: UUID, payload: RestoreProject, actor: Annotated[Principal, Depends(principal)]
    ) -> Project:
        return view(crud.restore(actor, project_id, payload.expected_revision))

    return router
