"""HTTP transport calls application use cases, never SQL."""

from typing import Annotated
from fastapi import APIRouter, Request, Depends

from forma_backend.core.errors import ApiError
from forma_backend.core.contracts import ErrorEnvelope
from forma_backend.modules.identity.application import (
    EmailAlreadyRegistered,
    RegisterUser,
    RateLimiter,
)
from forma_backend.modules.identity.application import PasswordCapacityExceeded
from forma_backend.modules.identity.schemas import Profile, Register


def registration_router(service: RegisterUser, limiter: RateLimiter) -> APIRouter:
    router = APIRouter()

    def get_service() -> RegisterUser:
        return service

    @router.post(
        "/api/v1/auth/register",
        status_code=201,
        response_model=Profile,
        operation_id="register_user",
        tags=["identity"],
        responses={code: {"model": ErrorEnvelope} for code in (409, 413, 415)},
        openapi_extra={"x-endpoint-id": "API-003", "x-status": "implemented"},
    )
    def register(
        payload: Register, request: Request, use_case: Annotated[RegisterUser, Depends(get_service)]
    ) -> Profile:
        # Never trust forwarded headers until an explicit trusted-proxy policy exists.
        if not limiter.consume(request.client.host if request.client else "unknown"):
            raise ApiError(429, "RATE_LIMITED", "Registration rate limit exceeded", 900)
        try:
            result = use_case.execute(payload.email, payload.password, payload.display_name)
        except EmailAlreadyRegistered:
            raise ApiError(409, "EMAIL_TAKEN", "Email already registered") from None
        except PasswordCapacityExceeded:
            raise ApiError(
                503, "RESOURCE_LIMIT", "Password hashing capacity exhausted", 1
            ) from None
        return Profile(
            id=result.id,
            email=result.email,
            display_name=result.display_name,
            created_at=result.created_at,
        )

    return router
