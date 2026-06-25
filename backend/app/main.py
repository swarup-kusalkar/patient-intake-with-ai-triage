"""
app/main.py — FastAPI application entry point.

Responsibilities:
- Create the FastAPI app with lifespan (startup/shutdown hooks)
- Register CORSMiddleware with explicit allow-list (never *)
- Register centralized exception handlers (Section 5 of Design Document)
- Mount all four routers under /api/v1/
- Expose GET /health for Docker healthcheck and smoke tests
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.db import engine
from app.models.base import Base

# Routers
from app.api import meta, triage, intake, dashboard


# ---------------------------------------------------------------------------
# Lifespan — startup and shutdown hooks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Startup: create DB tables if they don't exist (dev convenience).
    In production, Alembic handles migrations — this is a safety net only.

    Shutdown: dispose the connection pool cleanly.
    """
    # Dev convenience: create tables from ORM metadata.
    # Alembic runs first (see Dockerfile CMD), so this is a no-op in prod
    # when all tables already exist.
    try:
        async with engine.begin() as conn:
            # Import models so Base.metadata is populated before create_all
            import app.models  # noqa: F401 — side effect: populates Base.metadata
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"[WARNING] Could not connect to database during startup: {e}")
        print("[WARNING] Continuing without database connection (OK for tests).")

    yield  # Application is running

    # Shutdown: close connection pool gracefully
    await engine.dispose()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Patient Intake System API",
    description=(
        "RESTful API for the clinic patient intake system with AI-assisted triage. "
        "See /docs for interactive API documentation."
    ),
    version="0.1.0",
    lifespan=lifespan,
    # Don't redirect trailing slashes — avoids accidental method changes (POST → GET)
    redirect_slashes=False,
)


# ---------------------------------------------------------------------------
# CORS — explicit allow-list, NEVER wildcard *
# Section 10, item 5: CORS with explicit allow-list from Settings
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Centralized exception handlers — unified error envelope
#
# Problem this solves (Section 5 of Design Document):
# FastAPI/Pydantic validation errors return:
#   {"detail": [{"loc": [...], "msg": "...", "type": "..."}]}  ← list of objects
# HTTPException returns:
#   {"detail": "some string"}                                   ← bare string
#
# Same key, two incompatible shapes. A frontend handler written for one
# breaks on the other. Fix: normalize both to:
#   {"error": {"code": "...", "message": "...", "field": "..."}}
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handles Pydantic/FastAPI validation errors (422).
    Reports the first validation error's field and message.
    """
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(p) for p in first.get("loc", [])) if first else None
    message = first.get("msg", "Validation error") if first else "Validation error"
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "field": field,
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """
    Handles all HTTPException raises (404, 400, 503, etc.).
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "field": None,
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all for unexpected exceptions.
    NEVER leaks stack traces or internal details to the client (Section 10, item 9).
    """
    # Log the actual error server-side (in production, use structured logging)
    import traceback
    print(f"[ERROR] Unhandled exception: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred.",
                "field": None,
            }
        },
    )


# ---------------------------------------------------------------------------
# Routers — all mounted under /api/v1/
# ---------------------------------------------------------------------------
API_PREFIX = "/api/v1"

app.include_router(meta.router, prefix=API_PREFIX)
app.include_router(triage.router, prefix=API_PREFIX)
app.include_router(intake.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Health endpoint — outside /api/v1/ for simplicity
# Used by Docker healthcheck and Phase 0 smoke tests.
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Returns 200 OK when the application is running.",
)
async def health_check() -> dict:
    """Simple liveness probe — no DB check needed for Phase 0."""
    return {"status": "ok"}
