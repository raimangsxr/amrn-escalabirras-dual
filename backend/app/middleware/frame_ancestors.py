"""Frame-ancestors middleware.

Adds ``Content-Security-Policy: frame-ancestors <value>`` and
``X-Frame-Options: ALLOW-FROM <value>`` to every response so the
backend can be iframe'd from the configured origins.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class FrameAncestorsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, frame_ancestors: str) -> None:
        super().__init__(app)
        self.frame_ancestors = frame_ancestors

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault(
            "Content-Security-Policy", f"frame-ancestors {self.frame_ancestors}"
        )
        response.headers.setdefault("X-Frame-Options", f"ALLOW-FROM {self.frame_ancestors}")
        return response