"""Application factory; domain endpoints are added only by their own tasks."""

import asyncio
from threading import BoundedSemaphore

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import UUID

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import Engine
from starlette.exceptions import HTTPException

from forma_backend import __version__
from forma_backend.modules.identity.sessions import SessionUseCases, AuthenticationFailed
from forma_backend.modules.identity.session_router import session_router
from forma_backend.infrastructure.identity.session_store import SqlSessionStore
from forma_backend.infrastructure.identity.access_tokens import JwtAccessTokens
from forma_backend.core.errors import ApiError
from forma_backend.modules.identity.body_limit import AuthBodyLimit
from forma_backend.modules.identity.router import registration_router
from forma_backend.modules.identity.application import RegisterUser
from forma_backend.infrastructure.identity.persistence import SqlIdentityUnitOfWork
from forma_backend.infrastructure.identity.passwords import ScryptPasswordHasher
from forma_backend.infrastructure.identity.rate_limit import AuthRateLimit
from forma_backend.core.config import Settings, load_settings
from forma_backend.core.contracts import Error, ErrorDetail, ErrorEnvelope, Health
from forma_backend.core.logging import configure_logging, request_context
from forma_backend.infrastructure.database.session import create_database_engine
from forma_backend.infrastructure.health import database_ready, storage_ready


READINESS_TIMEOUT_SECONDS = 2.0


def error_response(status: int, code: str, message: str, request_id: UUID) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=Error(code=code, message=message, details=ErrorDetail(), request_id=request_id)
    )
    return JSONResponse(status_code=status, content=envelope.model_dump(mode="json"))


def create_app(settings: Settings | None = None, *, engine: Engine | None = None) -> FastAPI:
    settings = settings or load_settings()
    database = engine or create_database_engine(settings.database_url.get_secret_value())
    owned_engine = engine is None
    logger = configure_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("", extra={"event": "startup"})
        try:
            yield
        finally:
            if owned_engine:
                database.dispose()
            logger.info("", extra={"event": "shutdown"})

    docs = settings.app_env != "production"
    app = FastAPI(
        title="FORMA backend",
        version=__version__,
        lifespan=lifespan,
        responses={code: {"model": ErrorEnvelope} for code in (400, 404, 405, 422, 429, 500, 503)},
        docs_url="/docs" if docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.add_middleware(AuthBodyLimit)

    @app.middleware("http")
    async def correlate(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        with request_context(request.headers.get("x-request-id")) as identifier:
            request.state.request_id = identifier
            start = perf_counter()
            try:
                response = await call_next(request)
            except Exception:
                # Do not serialize exception text, request body or authentication headers.
                logger.error("", extra={"event": "request_failed", "error_code": "INTERNAL_ERROR"})
                response = error_response(
                    500, "INTERNAL_ERROR", "Internal server error", identifier
                )
            response.headers["X-Request-ID"] = str(identifier)
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            logger.info(
                "",
                extra={
                    "event": "request_completed",
                    "duration_ms": int((perf_counter() - start) * 1000),
                },
            )
            return response

    app.include_router(
        registration_router(
            RegisterUser(lambda: SqlIdentityUnitOfWork(database), ScryptPasswordHasher()),
            AuthRateLimit(database, settings.jwt_secret.get_secret_value()),
        )
    )

    auth = SessionUseCases(
        lambda: SqlSessionStore(database, settings.jwt_secret.get_secret_value()),
        ScryptPasswordHasher(),
        JwtAccessTokens(
            settings.jwt_secret.get_secret_value(),
            settings.jwt_issuer,
            settings.jwt_audience,
            settings.jwt_key_id,
            (settings.jwt_previous_key_id, settings.jwt_previous_secret.get_secret_value())
            if settings.jwt_previous_key_id and settings.jwt_previous_secret
            else None,
        ),
    )
    app.include_router(
        session_router(
            auth,
            settings.allowed_origins,
            settings.cookie_secure,
            AuthRateLimit(database, settings.jwt_secret.get_secret_value(), "login-ip"),
            AuthRateLimit(database, settings.jwt_secret.get_secret_value(), "login-email"),
        )
    )

    @app.exception_handler(AuthenticationFailed)
    async def authentication_error(request: Request, exc: AuthenticationFailed) -> JSONResponse:
        response = error_response(
            exc.status, exc.code, "Authentication failed", request.state.request_id
        )
        if exc.status == 401:
            response.headers["WWW-Authenticate"] = "Bearer"
        if exc.status == 429:
            response.headers["Retry-After"] = "60"
        return response

    @app.exception_handler(ApiError)
    async def application_error(request: Request, exc: ApiError) -> JSONResponse:
        response = error_response(exc.status, exc.code, exc.message, request.state.request_id)
        if exc.retry_after is not None:
            response.headers["Retry-After"] = str(exc.retry_after)
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        codes = {
            400: "INVALID_REQUEST",
            401: "UNAUTHENTICATED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
        }
        response = error_response(
            exc.status_code,
            codes.get(exc.status_code, "INVALID_REQUEST"),
            "Request failed",
            request.state.request_id,
        )
        if exc.headers:
            for name, value in exc.headers.items():
                if name.lower() in {"allow", "www-authenticate", "retry-after"}:
                    response.headers[name] = value
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(422, "VALIDATION_ERROR", "Invalid request", request.state.request_id)

    @app.get(
        "/health/live",
        response_model=Health,
        operation_id="liveness",
        tags=["system"],
        openapi_extra={"x-endpoint-id": "API-001", "x-status": "implemented"},
    )
    async def live() -> Health:
        return Health(status="ok")

    probe_slots = BoundedSemaphore(4)

    def probe_dependencies() -> str | None:
        # Cancelling an awaiting coroutine cannot stop synchronous I/O. Bound abandoned probes.
        if not probe_slots.acquire(blocking=False):
            return "DEPENDENCY_UNAVAILABLE"
        try:
            if not database_ready(database):
                return "DATABASE_UNAVAILABLE"
            if not storage_ready(settings.storage_root):
                return "STORAGE_UNAVAILABLE"
            return None
        finally:
            probe_slots.release()

    @app.get(
        "/health/ready",
        response_model=Health,
        operation_id="readiness",
        tags=["system"],
        responses={503: {"model": ErrorEnvelope}},
        openapi_extra={"x-endpoint-id": "API-002", "x-status": "implemented"},
    )
    async def ready(request: Request) -> Health | JSONResponse:
        try:
            error = await asyncio.wait_for(
                asyncio.to_thread(probe_dependencies), timeout=READINESS_TIMEOUT_SECONDS
            )
        except TimeoutError:
            error = "DEPENDENCY_UNAVAILABLE"
        if error:
            return error_response(503, error, "Dependency unavailable", request.state.request_id)
        return Health(status="ok")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-CSRF-Token",
            "X-Request-ID",
            "Idempotency-Key",
        ],
        expose_headers=["X-Request-ID", "Content-Disposition", "Retry-After"],
    )

    return app
