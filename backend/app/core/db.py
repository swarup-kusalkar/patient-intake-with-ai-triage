"""
app/core/db.py — Async SQLAlchemy engine and session factory.

Design decisions:
- asyncpg driver for full async I/O (no thread pool overhead)
- pool_pre_ping=True: detects stale connections before use (avoids
  "server closed the connection unexpectedly" errors after idle periods)
- get_db() dependency: yields a session, commits on success,
  rolls back on any exception — routes never manage transactions manually
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine — created once at module load time
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.database_url,
    # Emit a lightweight SELECT 1 before each connection is checked out.
    # Prevents errors when a pooled connection has gone stale.
    pool_pre_ping=True,
    # Echo SQL in debug mode only — never in production (leaks query structure)
    echo=settings.debug,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep ORM objects usable after commit
)


# ---------------------------------------------------------------------------
# FastAPI dependency — yields one session per request
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.

    Commits the transaction on success, rolls back on any exception.
    Ensures the session is always closed, even if an exception is raised.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
