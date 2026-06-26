"""app/api/intake.py -- Patient intake CRUD endpoints."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.intake import UrgencyLevel, Department
from app.schemas.intake import IntakeCreate, IntakeOut, IntakeListResponse
from app.repositories import intake_repo

router = APIRouter(prefix="/intake", tags=["intake"])


@router.post(
    "",
    response_model=IntakeOut,
    status_code=201,
    summary="Register a patient with intake record",
)
async def create_intake(
    body: IntakeCreate,
    db: AsyncSession = Depends(get_db),
) -> IntakeOut:
    """Create a patient and their intake record in one atomic transaction.

    Override flags (urgency_overridden, department_overridden) are computed
    server-side - the frontend never sends them.

    Returns 201 with the created IntakeRecord (patient eagerly loaded).
    """
    record = await intake_repo.create_patient_and_intake(db, body)
    return IntakeOut.model_validate(record)


@router.get(
    "",
    response_model=IntakeListResponse,
    summary="List/search intake records",
)
async def list_intake(
    name: str | None = Query(None, description="Case-insensitive partial name match"),
    date_from: date | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: date | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
    urgency: UrgencyLevel | None = Query(None, description="Filter by urgency"),
    department: Department | None = Query(None, description="Filter by department"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db),
) -> IntakeListResponse:
    """Paginated list of intake records with optional filters.

    - Name search is case-insensitive (ILIKE) and uses the GIN trigram index.
    - Date range is inclusive on both ends.
    - Urgency and department filters must match valid enum values or 422 is returned.
    - Returns total count so the frontend can render pagination controls.
    """
    records, total = await intake_repo.list_intake(
        db,
        name=name,
        date_from=date_from,
        date_to=date_to,
        urgency=urgency,
        department=department,
        limit=limit,
        offset=offset,
    )
    page = (offset // limit) + 1 if limit > 0 else 1
    return IntakeListResponse(
        items=[IntakeOut.model_validate(r) for r in records],
        total=total,
        page=page,
        page_size=limit,
    )


@router.get(
    "/{record_id}",
    response_model=IntakeOut,
    summary="Get a single intake record",
)
async def get_intake(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> IntakeOut:
    """Fetch a single intake record by UUID with patient info.

    Returns 404 if the record does not exist.
    """
    record = await intake_repo.get_intake_by_id(db, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Intake record not found")
    return IntakeOut.model_validate(record)
