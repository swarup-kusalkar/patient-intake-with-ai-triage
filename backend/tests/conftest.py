"""
tests/conftest.py — Shared pytest fixtures.

Phase 0: Provides a synchronous TestClient for smoke tests.
Phase 1: Adds async db_session fixture for DB-level schema tests.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.main import app
from app.models.base import Base


# ---------------------------------------------------------------------------
# Test database engine — TEST_DATABASE_URL overrides the default.
# ---------------------------------------------------------------------------
_TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", settings.database_url)
_db_engine = create_async_engine(_TEST_DB_URL, pool_pre_ping=True, echo=False)
_AsyncTestSession = async_sessionmaker(
    bind=_db_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Phase 0: Synchronous TestClient — for API/endpoint tests
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    FastAPI TestClient — synchronous, uses ASGI transport.
    scope="module" so the app is created once per test module.
    """
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Phase 1: Async session for direct schema tests.
# Creates all tables before each test; drops them after — clean slate.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
async def db_session() -> AsyncSession:
    """
    Async SQLAlchemy session with a fresh schema per test.
    Use this for any test that talks directly to Postgres (constraints,
    indexes, cascade, enum values, etc.).
    """
    async with _db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = _AsyncTestSession()
    yield session
    await session.close()

    async with _db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
