"""HTTP boundary for the authenticated user's own profile."""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from forma_backend.core.contracts import ErrorEnvelope
from forma_backend.core.errors import ApiError
from forma_backend.modules.identity.application import RateLimiter
from forma_backend.modules.identity.profiles import ProfileUseCases
from forma_backend.modules.identity.profile_schemas import ProfilePatch, PasswordChange
from forma_backend.modules.identity.schemas import Profile
from forma_backend.modules.identity.sessions import Principal
from forma_backend.modules.identity.session_router import clear_refresh_cookie


def profile_router(
    service: ProfileUseCases,
    principal: Callable[..., Principal],
    secure: bool,
    password_limit: RateLimiter,
) -> APIRouter:
    router = APIRouter(responses={401: {"model": ErrorEnvelope}})

    @router.get(
        "/api/v1/users/me",
        response_model=Profile,
        operation_id="read_profile",
        tags=["identity"],
        openapi_extra={"x-endpoint-id": "API-008", "x-status": "implemented"},
    )
    def read(actor: Annotated[Principal, Depends(principal)]) -> Profile:
        return Profile(**vars(service.read(actor)))

    @router.patch(
        "/api/v1/users/me",
        response_model=Profile,
        operation_id="update_profile",
        tags=["identity"],
        openapi_extra={"x-endpoint-id": "API-009", "x-status": "implemented"},
    )
    def update(payload: ProfilePatch, actor: Annotated[Principal, Depends(principal)]) -> Profile:
        return Profile(**vars(service.update(actor, payload.display_name)))

    @router.post(
        "/api/v1/users/me/change-password",
        status_code=204,
        operation_id="change_password",
        tags=["identity"],
        openapi_extra={"x-endpoint-id": "API-010", "x-status": "implemented"},
    )
    def change_password(
        payload: PasswordChange, actor: Annotated[Principal, Depends(principal)]
    ) -> Response:
        if not password_limit.consume(str(actor.user_id)):
            raise ApiError(429, "RATE_LIMITED", "Password change rate limit exceeded", 900)
        service.change_password(actor, payload.current_password, payload.new_password)
        response = Response(status_code=204)
        clear_refresh_cookie(response, secure)
        return response

    return router
