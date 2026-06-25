"""
app/api/intake.py — Patient intake CRUD endpoints.
STUB: Returns HTTP 501 Not Implemented. Full implementation in Phase 4.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/intake", tags=["intake"])

_NOT_IMPLEMENTED = JSONResponse(
    status_code=501,
    content={"error": {"code": "NOT_IMPLEMENTED", "message": "Intake endpoint not yet implemented.", "field": None}},
)


@router.post(
    "",
    status_code=501,
    summary="[STUB] Register a patient with intake record",
)
async def create_intake() -> JSONResponse:
    """STUB — Phase 4 will implement patient + intake record creation in one transaction."""
    return _NOT_IMPLEMENTED


@router.get(
    "",
    status_code=501,
    summary="[STUB] List/search intake records",
)
async def list_intake() -> JSONResponse:
    """STUB — Phase 4 will implement paginated search with filters."""
    return _NOT_IMPLEMENTED


@router.get(
    "/{record_id}",
    status_code=501,
    summary="[STUB] Get a single intake record",
)
async def get_intake(record_id: str) -> JSONResponse:
    """STUB — Phase 4 will implement single record fetch with patient join."""
    return _NOT_IMPLEMENTED
