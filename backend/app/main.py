"""app/main.py — FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.db import engine
from app.core.limiter import limiter
from app.core.logging_middleware import AccessLogMiddleware
from app.models.base import Base
from app.api import meta, triage, intake, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        async with engine.begin() as conn:
            import app.models
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"[WARNING] Could not connect to database during startup: {e}")
        print("[WARNING] Continuing without database connection (OK for tests).")
    yield
    await engine.dispose()


app = FastAPI(
    title="Patient Intake System API",
    description=(
        "RESTful API for the clinic patient intake system with AI-assisted triage. "
        "See /docs for interactive API documentation."
    ),
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
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
    import traceback
    import logging as _log
    _log.getLogger("app.access").error(
        "method=%s path=%s status=%d error=%s",
        request.method,
        request.url.path,
        500,
        type(exc).__name__,
    )
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


API_PREFIX = "/api/v1"

app.include_router(meta.router, prefix=API_PREFIX)
app.include_router(triage.router, prefix=API_PREFIX)
app.include_router(intake.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)

app.add_middleware(AccessLogMiddleware)


@app.get("/health", tags=["health"], summary="Health check")
async def health_check() -> dict:
    return {"status": "ok"}
