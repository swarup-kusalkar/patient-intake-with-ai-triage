"""
app/api/dashboard.py — Dashboard summary endpoint.
STUB: Returns HTTP 501 Not Implemented. Full implementation in Phase 4.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    status_code=501,
    summary="[STUB] Get dashboard summary for a given date",
)
async def get_dashboard_summary() -> JSONResponse:
    """STUB — Phase 4 will implement aggregated counts by urgency and department."""
    return JSONResponse(
        status_code=501,
        content={"error": {"code": "NOT_IMPLEMENTED", "message": "Dashboard summary endpoint not yet implemented.", "field": None}},
    )
