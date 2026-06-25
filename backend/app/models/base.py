"""
app/models/base.py — SQLAlchemy declarative base and shared mixins.
"""
from __future__ import annotations

import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


class TimestampMixin:
    """
    Adds created_at column to any model.

    TIMESTAMPTZ (timezone-aware) with server-side DEFAULT now() — the DB
    clock sets the value, not the application clock, so it's consistent
    regardless of where the app is deployed.
    """
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
