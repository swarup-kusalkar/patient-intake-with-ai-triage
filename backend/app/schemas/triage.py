"""
app/schemas/triage.py — Triage analyze request/response schemas.
STUB: Full implementation in Phase 2/3.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel

from app.models.intake import UrgencyLevel, Department, TriageSource


class TriageAnalyzeRequest(BaseModel):
    """POST /api/v1/triage/analyze request body. Phase 2: min/max length validation."""
    symptoms_text: str


class TriageAnalyzeResponse(BaseModel):
    """POST /api/v1/triage/analyze response body."""
    source: TriageSource
    urgency: UrgencyLevel
    department: Department
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
