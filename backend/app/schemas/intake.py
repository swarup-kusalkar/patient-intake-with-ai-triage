import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.intake import Department, TriageSource, UrgencyLevel
from app.schemas.patient import PatientOut


class IntakeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    age: int = Field(..., ge=0, le=130)
    gender: str = Field(..., min_length=1, max_length=20)
    contact_number: str = Field(..., min_length=1, max_length=20)

    symptoms_text: str = Field(..., min_length=1, max_length=2000)

    triage_source: TriageSource | None = None
    ai_suggested_urgency: UrgencyLevel | None = None
    ai_suggested_department: Department | None = None
    ai_confidence: float | None = Field(None, ge=0.0, le=1.0)
    ai_reasoning: str | None = Field(None, max_length=220)
    ai_raw_response: dict[str, Any] | None = None

    final_urgency: UrgencyLevel
    final_department: Department


class IntakeOut(BaseModel):
    id: uuid.UUID
    patient: PatientOut
    symptoms_text: str
    triage_source: TriageSource | None
    ai_suggested_urgency: UrgencyLevel | None
    ai_suggested_department: Department | None
    ai_confidence: float | None
    ai_reasoning: str | None
    final_urgency: UrgencyLevel
    final_department: Department
    urgency_overridden: bool | None
    department_overridden: bool | None
    created_at: datetime

    model_config = {"from_attributes": True}


class IntakeListResponse(BaseModel):
    items: list[IntakeOut]
    total: int
    page: int
    page_size: int