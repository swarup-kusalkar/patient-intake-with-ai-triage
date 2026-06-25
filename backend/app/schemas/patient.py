"""
app/schemas/patient.py — Patient Pydantic schemas.
STUB: Full implementation in Phase 2.
"""
from __future__ import annotations

import uuid
import datetime
from pydantic import BaseModel


class PatientCreate(BaseModel):
    """Fields required to create a new patient. Phase 2: full validation."""
    name: str
    age: int
    gender: str
    contact_number: str


class PatientOut(PatientCreate):
    """Patient record as returned from the API."""
    id: uuid.UUID
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
