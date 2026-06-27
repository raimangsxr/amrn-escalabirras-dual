"""API error type used by route handlers and the global exception handler.

Lives in its own module to avoid a circular import between
``app.main`` (which mounts the handlers) and ``app.routers.*`` (which
raises the errors).
"""

from __future__ import annotations

from fastapi import HTTPException


class ApiError(HTTPException):
    """An HTTPException that carries an explicit machine-readable code.

    Use this when raising from a route handler so the global exception
    handler in ``app.main`` can pass the code through without falling
    back to substring matching on the human-readable detail string.
    """

    def __init__(self, status_code: int, code: str, detail: str) -> None:
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": detail},
        )
        self.code = code