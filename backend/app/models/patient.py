"""
app/models/patient.py — Patient ORM model.

STUB: Full column definitions are here; Phase 1 adds the Alembic migration.
The model is complete per the schema in Design Document Section 4.
"""
from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Patient(Base, TimestampMixin):
    """
    Represents a clinic patient.

    One patient can have many intake records (multiple visits over time).
    The schema supports this even though the current UI registers one visit
    per session — avoids a redesign the moment repeat visits matter.
    """
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_number: Mapped[str] = mapped_column(String(20), nullable=False)
    intake_records: Mapped[list["IntakeRecord"]] = relationship(
        "IntakeRecord", back_populates="patient", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("age >= 0 AND age <= 130", name="ck_patient_age"),
    )

    def __repr__(self) -> str:
        return f"<Patient id={self.id} name={self.name!r}>"
