"""Bound implemented JSON bodies before JSON parsing, including chunked requests."""

from uuid import UUID
import re

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from forma_backend.core.contracts import Error, ErrorDetail, ErrorEnvelope


class JsonBodyLimit:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        dynamic_project = (
            (
                scope["method"] == "POST"
                and re.fullmatch(r"/api/v1/projects/[^/]+/members", scope["path"]) is not None
            )
            or (
                scope["method"] == "PATCH"
                and re.fullmatch(r"/api/v1/projects/[^/]+/members/[^/]+", scope["path"]) is not None
            )
            or (
                scope["method"] in {"PATCH", "DELETE"}
                and re.fullmatch(r"/api/v1/projects/[^/]+", scope["path"]) is not None
            )
            or (
                scope["method"] == "POST"
                and re.fullmatch(r"/api/v1/projects/[^/]+/restore", scope["path"]) is not None
            )
        )
        if not dynamic_project and (scope["method"], scope["path"]) not in {
            ("POST", "/api/v1/projects"),
            ("POST", "/api/v1/auth/register"),
            ("POST", "/api/v1/auth/login"),
            ("PATCH", "/api/v1/users/me"),
            ("POST", "/api/v1/users/me/change-password"),
        }:
            await self.app(scope, receive, send)
            return

        async def reject(status: int, code: str) -> None:
            identifier = UUID(str(scope["state"]["request_id"]))
            error = ErrorEnvelope(
                error=Error(
                    code=code,
                    message="Invalid request body",
                    details=ErrorDetail(),
                    request_id=identifier,
                )
            )
            await JSONResponse(error.model_dump(mode="json"), status_code=status)(
                scope, receive, send
            )

        if (
            Headers(scope=scope).get("content-type", "").split(";")[0].strip().lower()
            != "application/json"
        ):
            await reject(415, "UNSUPPORTED_MEDIA_TYPE")
            return
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > 2 * 1024 * 1024:
                await reject(413, "PAYLOAD_TOO_LARGE")
                return
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        body = b"".join(chunks)
        delivered = False

        async def replay() -> Message:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
