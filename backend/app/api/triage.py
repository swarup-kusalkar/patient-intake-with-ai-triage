"""
app/api/triage.py — Triage analyze endpoint.
STUB: Returns HTTP 501 Not Implemented. Full implementation in Phase 3/4.

The stub exists so router wiring is verified at boot, not discovered
broken in Phase 4. A 501 is intentional — it signals "this route exists
but is not yet implemented," which is different from a 404 (not found)
or a 500 (unexpected error).
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/triage", tags=["triage"])


@router.post(
    "/analyze",
    status_code=501,
    summary="[STUB] Analyze symptoms and return AI triage suggestion",
    description="Not yet implemented. Returns 501 until Phase 3/4.",
)
async def analyze_symptoms() -> JSONResponse:
    """STUB — Phase 3/4 will implement the full rule engine + LLM pipeline."""
    return JSONResponse(
        status_code=501,
        content={"error": {"code": "NOT_IMPLEMENTED", "message": "Triage analyze endpoint not yet implemented.", "field": None}},
    )
