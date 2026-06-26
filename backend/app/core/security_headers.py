"""app/core/security_headers.py — Security header injection middleware.

Phase 10 items: Hardens responses against common web attacks by injecting
standard security headers on every response.

Headers:
  X-Content-Type-Options: nosniff — prevents MIME-type sniffing
  X-Frame-Options: DENY — prevents clickjacking via iframe embedding
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject security-related HTTP headers on every response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers.update(_SECURITY_HEADERS)
        return response