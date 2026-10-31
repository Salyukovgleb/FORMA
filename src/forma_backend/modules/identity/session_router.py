"""HTTP session boundary; credentials never appear in logs, URLs or errors."""

from collections.abc import Callable

import base64
import hashlib
import json
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.security import APIKeyCookie, HTTPBearer, HTTPAuthorizationCredentials
from forma_backend.core.contracts import ErrorEnvelope
from forma_backend.core.errors import ApiError
from forma_backend.modules.identity.application import PasswordCapacityExceeded, RateLimiter
from forma_backend.modules.identity.session_schemas import Login, Token, Session, SessionPage
from forma_backend.modules.identity.sessions import (
    AuthenticationFailed,
    Principal,
    SessionUseCases,
    TokenBundle,
)

COOKIE = "forma_refresh"
COOKIE_PATH = "/api/v1/auth"


def clear_refresh_cookie(response: Response, secure: bool) -> None:
    response.delete_cookie(
        COOKIE, path=COOKIE_PATH, secure=secure, httponly=True, samesite="strict"
    )


def principal_dependency(service: SessionUseCases) -> Callable[..., Principal]:
    bearer = HTTPBearer(auto_error=False, scheme_name="bearerAuth", bearerFormat="JWT")

    def principal(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ) -> Principal:
        if credentials is None:
            raise AuthenticationFailed()
        return service.authenticate(credentials.credentials)

    return principal


def session_router(
    service: SessionUseCases,
    origins: tuple[str, ...],
    secure: bool,
    ip_limit: RateLimiter,
    email_limit: RateLimiter,
) -> APIRouter:
    router = APIRouter(responses={code: {"model": ErrorEnvelope} for code in (401, 403, 404, 409)})

    def check_origin(request: Request) -> None:
        if request.headers.get("origin") not in origins:
            raise ApiError(403, "CSRF_FAILED", "Origin rejected")

    principal = principal_dependency(service)
    cookie = APIKeyCookie(name=COOKIE, auto_error=False, scheme_name="refreshCookie")

    def refresh_credentials(
        request: Request,
        refresh: Annotated[str | None, Depends(cookie)],
        csrf: Annotated[str, Header(alias="X-CSRF-Token", min_length=32, max_length=128)],
        origin: Annotated[str, Header(alias="Origin", max_length=2048)],
    ) -> tuple[str, str]:
        check_origin(request)
        if not 32 <= len(csrf) <= 128:
            raise ApiError(403, "CSRF_FAILED", "Invalid CSRF token")
        return refresh or "", csrf

    def issue(bundle: TokenBundle, response: Response) -> Token:
        response.set_cookie(
            COOKIE,
            bundle.refresh_token,
            max_age=max(0, int((bundle.expires_at - datetime.now(UTC)).total_seconds())),
            httponly=True,
            secure=secure,
            samesite="strict",
            path=COOKIE_PATH,
        )
        return Token(access_token=bundle.access_token, csrf_token=bundle.csrf_token)

    @router.post(
        "/api/v1/auth/login",
        response_model=Token,
        operation_id="login",
        tags=["identity"],
        openapi_extra={"x-endpoint-id": "API-004", "x-status": "implemented"},
    )
    def login(
        payload: Login,
        request: Request,
        response: Response,
        origin: Annotated[str, Header(alias="Origin", max_length=2048)],
    ) -> Token:
        check_origin(request)
        if not ip_limit.consume(
            request.client.host if request.client else "unknown"
        ) or not email_limit.consume(payload.email):
            raise ApiError(429, "RATE_LIMITED", "Login rate limit exceeded", 900)
        try:
            return issue(service.login(payload.email, payload.password), response)
        except PasswordCapacityExceeded:
            raise ApiError(
                503, "RESOURCE_LIMIT", "Password hashing capacity exhausted", 1
            ) from None

    @router.post(
        "/api/v1/auth/refresh",
        response_model=Token,
        operation_id="rotate_session",
        tags=["identity"],
        openapi_extra={"x-endpoint-id": "API-005", "x-status": "implemented"},
    )
    def refresh(
        response: Response, credentials: Annotated[tuple[str, str], Depends(refresh_credentials)]
    ) -> Token:
        refresh, csrf = credentials
        return issue(service.refresh(refresh, csrf), response)

    @router.post(
        "/api/v1/auth/logout",
        status_code=204,
        operation_id="logout",
        tags=["identity"],
        openapi_extra={"x-endpoint-id": "API-006", "x-status": "implemented"},
    )
    def logout(credentials: Annotated[tuple[str, str], Depends(refresh_credentials)]) -> Response:
        refresh, csrf = credentials
        service.logout(refresh, csrf)
        response = Response(status_code=204)
        clear_refresh_cookie(response, secure)
        return response

    @router.post(
        "/api/v1/auth/logout-all",
        status_code=204,
        operation_id="logout_all",
        tags=["identity"],
        openapi_extra={"x-endpoint-id": "API-007", "x-status": "implemented"},
    )
    def logout_all(actor: Annotated[Principal, Depends(principal)]) -> Response:
        service.logout_all(actor)
        response = Response(status_code=204)
        clear_refresh_cookie(response, secure)
        return response

    @router.get(
        "/api/v1/auth/sessions",
        response_model=SessionPage,
        operation_id="list_sessions",
        tags=["identity"],
        openapi_extra={"x-endpoint-id": "API-011", "x-status": "implemented"},
    )
    def list_sessions(
        actor: Annotated[Principal, Depends(principal)],
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        cursor: Annotated[str | None, Query(max_length=2048)] = None,
    ) -> SessionPage:
        before = None
        filter_hash = hashlib.sha256(str(actor.user_id).encode()).hexdigest()
        if cursor:
            try:
                value = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
                if value["v"] != 1 or value["filter"] != filter_hash:
                    raise ValueError()
                timestamp = datetime.fromisoformat(value["created_at"])
                if timestamp.tzinfo is None:
                    raise ValueError()
                before = (timestamp, UUID(value["id"]))
            except (ValueError, KeyError, TypeError, UnicodeError):
                raise ApiError(400, "INVALID_CURSOR", "Invalid cursor") from None
        rows = service.list_sessions(actor, limit + 1, before)
        page = rows[:limit]
        next_cursor = None
        if len(rows) > limit:
            last = page[-1]
            next_cursor = (
                base64.urlsafe_b64encode(
                    json.dumps(
                        {
                            "v": 1,
                            "created_at": last.created_at.isoformat(),
                            "id": str(last.id),
                            "filter": filter_hash,
                        }
                    ).encode()
                )
                .decode()
                .rstrip("=")
            )
        return SessionPage(
            items=[
                Session(
                    id=s.id,
                    created_at=s.created_at,
                    expires_at=s.expires_at,
                    is_current=s.id == actor.session_id,
                )
                for s in page
            ],
            next_cursor=next_cursor,
        )

    @router.delete(
        "/api/v1/auth/sessions/{session_id}",
        status_code=204,
        operation_id="revoke_session",
        tags=["identity"],
        openapi_extra={"x-endpoint-id": "API-012", "x-status": "implemented"},
    )
    def revoke_session(
        session_id: UUID, actor: Annotated[Principal, Depends(principal)]
    ) -> Response:
        service.revoke(actor, session_id)
        response = Response(status_code=204)
        if actor.session_id == session_id:
            clear_refresh_cookie(response, secure)
        return response

    return router
