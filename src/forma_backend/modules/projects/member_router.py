"""Member HTTP boundary without SQL."""

from collections.abc import Callable
from dataclasses import asdict
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Response
from forma_backend.core.contracts import ErrorEnvelope
from forma_backend.modules.identity.sessions import Principal
from forma_backend.modules.projects.member_application import ProjectMembers
from forma_backend.modules.projects.member_schemas import Member, Members, MemberAdd, MemberPatch


def member_router(service: ProjectMembers, principal: Callable[..., Principal]) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/projects/{project_id}/members",
        tags=["access"],
        responses={
            code: {"model": ErrorEnvelope} for code in (401, 403, 404, 409, 413, 415, 422, 429)
        },
    )

    @router.get(
        "",
        response_model=Members,
        operation_id="list_members",
        openapi_extra={"x-endpoint-id": "API-034", "x-status": "implemented"},
    )
    def listing(project_id: UUID, actor: Annotated[Principal, Depends(principal)]) -> Members:
        return Members(
            items=[Member(**asdict(m)) for m in service.execute(actor, project_id, "list")]
        )

    @router.post(
        "",
        response_model=Member,
        status_code=201,
        operation_id="grant_project_access",
        openapi_extra={"x-endpoint-id": "API-035", "x-status": "implemented"},
    )
    def grant(
        project_id: UUID, payload: MemberAdd, actor: Annotated[Principal, Depends(principal)]
    ) -> Member:
        return Member(
            **asdict(
                service.execute(actor, project_id, "grant", email=payload.email, role=payload.role)[
                    0
                ]
            )
        )

    @router.patch(
        "/{user_id}",
        response_model=Member,
        operation_id="change_member_role",
        openapi_extra={"x-endpoint-id": "API-036", "x-status": "implemented"},
    )
    def change(
        project_id: UUID,
        user_id: UUID,
        payload: MemberPatch,
        actor: Annotated[Principal, Depends(principal)],
    ) -> Member:
        return Member(
            **asdict(
                service.execute(actor, project_id, "change", target=user_id, role=payload.role)[0]
            )
        )

    @router.delete(
        "/{user_id}",
        status_code=204,
        operation_id="remove_member",
        openapi_extra={"x-endpoint-id": "API-037", "x-status": "implemented"},
    )
    def remove(
        project_id: UUID, user_id: UUID, actor: Annotated[Principal, Depends(principal)]
    ) -> Response:
        service.execute(actor, project_id, "remove", target=user_id)
        return Response(status_code=204)

    return router
