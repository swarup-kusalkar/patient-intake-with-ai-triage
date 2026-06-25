"""
app/models/intake.py — IntakeRecord ORM model + Python enum classes.

STUB: Full column definitions are here; Phase 1 adds the Alembic migration.
The model is complete per the schema in Design Document Section 4.

Key design decisions:
- All ai_* columns are nullable. NULL means "Analyze was never called or
  failed" — semantically different from "AI agreed with final values".
- urgency_overridden and department_overridden are independent booleans:
  a receptionist may accept the urgency suggestion but override department.
  NULL means no AI suggestion existed to compare against.
- Backend computes override flags at Save time — never trusts the frontend.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


# ---------------------------------------------------------------------------
# Python enums — single source of truth for valid values.
# These are referenced by: the ORM, Pydantic schemas, the triage service,
# and the meta API endpoint. Never hardcode department/urgency strings.
# ---------------------------------------------------------------------------

class UrgencyLevel(str, enum.Enum):
    routine = "routine"
    priority = "priority"
    urgent = "urgent"


class Department(str, enum.Enum):
    general_medicine = "general_medicine"
    cardiology = "cardiology"
    neurology = "neurology"
    orthopedics = "orthopedics"
    dermatology = "dermatology"
    ent = "ent"
    pulmonology = "pulmonology"
    gastroenterology = "gastroenterology"
    emergency = "emergency"


class TriageSource(str, enum.Enum):
    rule_engine = "rule_engine"
    llm = "llm"
    manual = "manual"


# ---------------------------------------------------------------------------
# IntakeRecord model
# ---------------------------------------------------------------------------

class IntakeRecord(Base, TimestampMixin):
    """
    One patient registration / visit record.

    Carries a snapshot of any AI suggestion (frozen at Analyze time)
    alongside the final values the receptionist confirmed at Save.
    The database only ever sees the one record that was confirmed — the
    analyze step is side-effect-free (Design Document Section 5).
    """
    __tablename__ = "intake_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    symptoms_text: Mapped[str] = mapped_column(Text, nullable=False)

    # ------------------------------------------------------------------
    # AI suggestion snapshot — ALL nullable.
    # NULL = no AI suggestion exists for this record at all.
    # ------------------------------------------------------------------
    triage_source: Mapped[TriageSource | None] = mapped_column(
        SAEnum(TriageSource, name="triage_source", create_type=False), nullable=True
    )
    ai_suggested_urgency: Mapped[UrgencyLevel | None] = mapped_column(
        SAEnum(UrgencyLevel, name="urgency_level", create_type=False), nullable=True
    )
    ai_suggested_department: Mapped[Department | None] = mapped_column(
        SAEnum(Department, name="department", create_type=False), nullable=True
    )
    # confidence: real float; clamped to [0, 1] in triage_service, enforced by DB CHECK
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Short rationale for audit/debug only — not shown in the UI by default
    ai_reasoning: Mapped[str | None] = mapped_column(String(220), nullable=True)
    # Full original LLM payload — audit trail
    ai_raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ------------------------------------------------------------------
    # What was actually saved — always required (NOT NULL)
    # ------------------------------------------------------------------
    final_urgency: Mapped[UrgencyLevel] = mapped_column(
        SAEnum(UrgencyLevel, name="urgency_level", create_type=False), nullable=False
    )
    final_department: Mapped[Department] = mapped_column(
        SAEnum(Department, name="department", create_type=False), nullable=False
    )

    # ------------------------------------------------------------------
    # Independent override flags.
    # NULL  → no ai_suggested_* to compare against (Analyze never ran)
    # False → final == ai_suggested (accepted)
    # True  → final != ai_suggested (overridden)
    # These are computed server-side at Save; never trusted from the client.
    # ------------------------------------------------------------------
    urgency_overridden: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    department_overridden: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)",
            name="ck_confidence_range",
        ),
        CheckConstraint(
            "char_length(symptoms_text) <= 2000",
            name="ck_symptoms_length",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<IntakeRecord id={self.id} "
            f"urgency={self.final_urgency} "
            f"dept={self.final_department}>"
        )
