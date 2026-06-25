"""
app/schemas/intake.py — Intake record Pydantic schemas.
STUB: Full implementation in Phase 2.
"""
from __future__ import annotations

import uuid
import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.models.intake import UrgencyLevel, Department, TriageSource


class IntakeCreate(BaseModel):
    """Request body for POST /api/v1/intake. Phase 2: full validation."""
    # Patient fields
    name: str
    age: int
    gender: str
    contact_number: str
    symptoms_text: str

    # AI snapshot — all optional (null when Analyze was never clicked)
    triage_source: Optional[TriageSource] = None
    ai_suggested_urgency: Optional[UrgencyLevel] = None
    ai_suggested_department: Optional[Department] = None
    ai_confidence: Optional[float] = None
    ai_reasoning: Optional[str] = None
    ai_raw_response: Optional[dict] = None

    # Final confirmed values — required
    final_urgency: UrgencyLevel
    final_department: Department


class IntakeOut(BaseModel):
    """Full intake record as returned from the API."""
    id: uuid.UUID
    patient_id: uuid.UUID
    symptoms_text: str
    triage_source: Optional[TriageSource] = None
    ai_suggested_urgency: Optional[UrgencyLevel] = None
    ai_suggested_department: Optional[Department] = None
    ai_confidence: Optional[float] = None
    ai_reasoning: Optional[str] = None
    final_urgency: UrgencyLevel
    final_department: Department
    urgency_overridden: Optional[bool] = None
    department_overridden: Optional[bool] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class IntakeListResponse(BaseModel):
    """Paginated list response for GET /api/v1/intake."""
    items: List[IntakeOut]
    total: int
    page: int
    page_size: int
