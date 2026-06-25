"""
app/api/meta.py — Reference list endpoints. FULLY IMPLEMENTED in Phase 0.

These endpoints are the single source of truth for frontend dropdowns.
The frontend never hardcodes department or urgency strings — it always
fetches them from here. This means adding a new department requires
only one change: the Python enum in app/models/intake.py.

No database dependency — these are derived from the Python enum classes
at import time, so they're available even before the DB is ready.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter

from app.models.intake import Department, UrgencyLevel

router = APIRouter(prefix="/meta", tags=["meta"])

# Pre-compute the lists once at startup — these never change at runtime
_DEPARTMENTS: List[str] = [d.value for d in Department]
_URGENCY_LEVELS: List[str] = [u.value for u in UrgencyLevel]


@router.get(
    "/departments",
    response_model=List[str],
    summary="List all valid departments",
    description=(
        "Returns the canonical list of departments used throughout the system. "
        "Frontend dropdowns must use this list — never hardcode department strings."
    ),
)
async def get_departments() -> List[str]:
    """Return all valid department enum values."""
    return _DEPARTMENTS


@router.get(
    "/urgency-levels",
    response_model=List[str],
    summary="List all valid urgency levels",
    description=(
        "Returns the canonical list of urgency levels. "
        "Order: routine → priority → urgent (ascending severity)."
    ),
)
async def get_urgency_levels() -> List[str]:
    """Return all valid urgency level enum values."""
    return _URGENCY_LEVELS
