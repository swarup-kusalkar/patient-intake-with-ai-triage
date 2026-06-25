"""app/schemas/triage.py — Triage analyze request/response schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.intake import Department, TriageSource, UrgencyLevel


class TriageAnalyzeRequest(BaseModel):
    symptoms_text: str = Field(..., min_length=10, max_length=2000)


class TriageAnalyzeResponse(BaseModel):
    source: TriageSource
    urgency: UrgencyLevel
    department: Department
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
