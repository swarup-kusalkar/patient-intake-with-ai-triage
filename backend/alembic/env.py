"""
Alembic environment — async-compatible.

This file is loaded by Alembic to set up the migration environment.
Key decisions:
- Uses async engine (asyncpg) to match the application's engine
- Imports Base.metadata from all models so autogenerate can diff them
- Reads DATABASE_URL from app.core.config.settings (not hardcoded)
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import the declarative base and ALL models so metadata is populated
from app.models.base import Base
import app.models  # noqa: F401 — populates Base.metadata via imports in __init__.py

from app.core.config import settings

# Alembic Config object — provides access to alembic.ini values
config = context.config

# Set up Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with the value from our Pydantic Settings
# This ensures migrations use the same DB URL as the running application
config.set_main_option("sqlalchemy.url", settings.database_url)

# Metadata for autogenerate support — Alembic diffs this against the DB
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (no DB connection required).
    Emits SQL to stdout for review before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        # Compare server defaults so autogenerate catches DEFAULT changes
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine (matches our asyncpg setup)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # NullPool for migration runs — no connection reuse
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connected to DB)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
