"""app/core/logging_middleware.py — Request access logging.

Phase 10 item 10: Log request metadata, never full symptoms_text verbatim.

This middleware logs every HTTP request's method, path, status, client IP,
and processing duration. The request body (which may contain symptoms_text or
patient PII) is never read or logged.
"""
from __future__ import annotations

import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.access")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that logs every HTTP transaction.

    Log fields: method, path, status, client_ip, duration_ms

    The request body is NEVER read or logged. This protects sensitive patient
    data (symptoms_text, name, age, etc.) from appearing in logs even if
    the caller accidentally sends it in a way that would otherwise be captured.
    """

    async def dispatch(self, request: Request, call_next):
        client_ip = self._client_ip(request)
        method = request.method
        path = request.url.path
        query = request.url.query
        full_path = f"{path}?{query}" if query else path

        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "method=%s path=%s status=%d client_ip=%s duration_ms=%.2f",
                method,
                full_path,
                status_code,
                client_ip,
                duration_ms,
            )

    def _client_ip(self, request: Request) -> str:
        """Extract client IP, checking X-Forwarded-For first (reverse proxy)."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"
