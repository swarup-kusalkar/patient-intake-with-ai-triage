"""app/api/dashboard.py -- Dashboard summary endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.utils import parse_date_param
from app.schemas.dashboard import DashboardSummary
from app.repositories import dashboard_repo

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get dashboard summary for a given date",
)
async def get_dashboard_summary(
    date: str = Query("today", description="Date to summarize: 'today' or 'YYYY-MM-DD'"),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummary:
    """Return daily dashboard aggregates.

    - total: count of all intake records for the day
    - by_urgency: counts grouped by final_urgency
    - by_department: counts grouped by final_department
    - override_rate: fraction of AI-assisted records that were overridden
      (None when no AI-assisted records exist for the day)

    All four aggregation queries run against indexed columns (created_at,
    final_urgency, final_department) - sub-millisecond at demo scale.
    """
    d = parse_date_param(date)
    result = await dashboard_repo.get_dashboard_summary(db, d)
    return result
