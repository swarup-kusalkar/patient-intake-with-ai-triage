import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    age: int = Field(..., ge=0, le=130)
    gender: str = Field(..., min_length=1, max_length=20)
    contact_number: str = Field(..., min_length=1, max_length=20)

    @field_validator("name", "gender", "contact_number", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class PatientOut(PatientCreate):
    id: uuid.UUID
    name: str
    age: int
    gender: str
    contact_number: str
    created_at: datetime

    model_config = {"from_attributes": True}