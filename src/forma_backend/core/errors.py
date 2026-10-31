"""Trusted presentation errors. Domain exceptions are translated at the HTTP boundary."""


class ApiError(Exception):
    def __init__(
        self, status: int, code: str, message: str, retry_after: int | None = None
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.retry_after = retry_after
