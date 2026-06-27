"""Production security headers middleware.

Adds the headers that a serious reverse-proxy setup expects the
application itself to set, in case the proxy does not (or for direct
exposure during canary / staging).

Headers added on every response:

- ``X-Content-Type-Options: nosniff`` — block MIME sniffing.
- ``Referrer-Policy: no-referrer`` — never leak the URL in the
  Referer header.
- ``Strict-Transport-Security: max-age=63072000; includeSubDomains``
  — only when the request arrived over HTTPS (or a TLS-terminating
  proxy forwarded ``X-Forwarded-Proto: https``). We never promise
  HSTS over plain HTTP.

The ``frame-ancestors`` / ``X-Frame-Options`` headers are owned by
``app.middleware.frame_ancestors`` and remain unchanged.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

HSTS_VALUE = "max-age=63072000; includeSubDomains"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")

        if _is_https(request):
            response.headers.setdefault("Strict-Transport-Security", HSTS_VALUE)

        return response


def _is_https(request: Request) -> bool:
    if request.url.scheme == "https":
        return True
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    return forwarded_proto.lower().split(",")[0].strip() == "https"