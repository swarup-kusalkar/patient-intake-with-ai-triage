"""app/repositories/intake_repo.py -- All DB operations for intake + patient."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.utils import day_range
from app.models.intake import IntakeRecord, UrgencyLevel, Department
from app.models.patient import Patient
from app.schemas.intake import IntakeCreate


def _escape_like(s: str) -> str:
    """Escape LIKE special characters to prevent injection into ILIKE patterns."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def create_patient_and_intake(
    db: AsyncSession,
    body: IntakeCreate,
) -> IntakeRecord:
    """Insert Patient row, compute override flags, insert IntakeRecord.

    Atomic: both inserts happen in the same transaction. On any failure
    both roll back - no orphaned patient rows.
    """
    if body.ai_suggested_urgency is None:
        urgency_overridden: bool | None = None
        department_overridden: bool | None = None
    else:
        urgency_overridden = bool(body.final_urgency != body.ai_suggested_urgency)
        department_overridden = bool(body.final_department != body.ai_suggested_department)

    patient = Patient(
        name=body.name,
        age=body.age,
        gender=body.gender,
        contact_number=body.contact_number,
    )
    db.add(patient)
    await db.flush()

    record = IntakeRecord(
        patient_id=patient.id,
        symptoms_text=body.symptoms_text,
        triage_source=body.triage_source,
        ai_suggested_urgency=body.ai_suggested_urgency,
        ai_suggested_department=body.ai_suggested_department,
        ai_confidence=body.ai_confidence,
        ai_reasoning=body.ai_reasoning,
        ai_raw_response=body.ai_raw_response,
        final_urgency=body.final_urgency,
        final_department=body.final_department,
        urgency_overridden=urgency_overridden,
        department_overridden=department_overridden,
    )
    db.add(record)
    await db.flush()

    await db.refresh(record, attribute_names=["patient"])
    return record


async def list_intake(
    db: AsyncSession,
    name: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    urgency: UrgencyLevel | None = None,
    department: Department | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[IntakeRecord], int]:
    """Query intake_records with optional filters.

    Name: case-insensitive ILIKE (uses GIN trigram index when available).
    Date range: inclusive on both ends using created_at TIMESTAMPTZ.
    Returns (items, total_count) for pagination.
    """
    query = select(IntakeRecord).options(selectinload(IntakeRecord.patient))
    count_query = select(func.count(IntakeRecord.id))

    if name:
        escaped = _escape_like(name)
        query = query.join(Patient).where(Patient.name.ilike(f"%{escaped}%"))
        count_query = count_query.join(Patient).where(Patient.name.ilike(f"%{escaped}%"))

    if date_from is not None:
        start, _ = day_range(date_from)
        query = query.where(IntakeRecord.created_at >= start)
        count_query = count_query.where(IntakeRecord.created_at >= start)

    if date_to is not None:
        _, end = day_range(date_to)
        query = query.where(IntakeRecord.created_at < end)
        count_query = count_query.where(IntakeRecord.created_at < end)

    if urgency:
        query = query.where(IntakeRecord.final_urgency == urgency)
        count_query = count_query.where(IntakeRecord.final_urgency == urgency)

    if department:
        query = query.where(IntakeRecord.final_department == department)
        count_query = count_query.where(IntakeRecord.final_department == department)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    query = query.order_by(IntakeRecord.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    records = list(result.unique().scalars().all())

    return records, total


async def get_intake_by_id(
    db: AsyncSession,
    intake_id: uuid.UUID,
) -> IntakeRecord | None:
    """Fetch a single intake record by UUID with patient eagerly loaded."""
    query = (
        select(IntakeRecord)
        .options(selectinload(IntakeRecord.patient))
        .where(IntakeRecord.id == intake_id)
    )
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()