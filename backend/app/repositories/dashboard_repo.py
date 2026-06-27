"""app/repositories/dashboard_repo.py -- Dashboard aggregation queries."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import day_range
from app.models.intake import IntakeRecord
from app.schemas.dashboard import DashboardSummary


async def get_dashboard_summary(
    db: AsyncSession,
    target_date,
) -> DashboardSummary:
    """Return dashboard aggregates for a single day."""
    start, end = day_range(target_date)

    total_result = await db.execute(
        select(func.count(IntakeRecord.id)).where(
            IntakeRecord.created_at >= start,
            IntakeRecord.created_at < end,
        )
    )
    total = total_result.scalar() or 0

    urgency_result = await db.execute(
        select(IntakeRecord.final_urgency, func.count(IntakeRecord.id))
        .where(IntakeRecord.created_at >= start, IntakeRecord.created_at < end)
        .group_by(IntakeRecord.final_urgency)
    )
    by_urgency = {u: c for u, c in urgency_result.all()}

    dept_result = await db.execute(
        select(IntakeRecord.final_department, func.count(IntakeRecord.id))
        .where(IntakeRecord.created_at >= start, IntakeRecord.created_at < end)
        .group_by(IntakeRecord.final_department)
    )
    by_department = {d: c for d, c in dept_result.all()}

    ai_used_result = await db.execute(
        select(func.count(IntakeRecord.id)).where(
            IntakeRecord.created_at >= start,
            IntakeRecord.created_at < end,
            IntakeRecord.triage_source.isnot(None),
        )
    )
    ai_used_count = ai_used_result.scalar() or 0

    overridden_result = await db.execute(
        select(func.count(IntakeRecord.id)).where(
            IntakeRecord.created_at >= start,
            IntakeRecord.created_at < end,
            IntakeRecord.triage_source.isnot(None),
            (
                (IntakeRecord.urgency_overridden == True)
                | (IntakeRecord.department_overridden == True)
            ),
        )
    )
    overridden_count = overridden_result.scalar() or 0

    override_rate = round(overridden_count / ai_used_count, 4) if ai_used_count > 0 else None

    return DashboardSummary(
        date=target_date.isoformat(),
        total=total,
        by_urgency=by_urgency,
        by_department=by_department,
        override_rate=override_rate,
    )