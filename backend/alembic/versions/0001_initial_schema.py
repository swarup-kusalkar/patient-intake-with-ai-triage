"""0001_initial_schema.py

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2024-01-01 00:00:00.000000

Phase 1: Initial schema.
Creates PostgreSQL extensions, three ENUM types, both tables
(patients, intake_records) with all constraints and indexes.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extensions (must be first -- pg_trgm required for gin index)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    # 2. ENUM types (must exist before tables that reference them)
    sa.Enum("routine", "priority", "urgent", name="urgency_level").create(op.get_bind(), checkfirst=False)
    sa.Enum(
        "general_medicine", "cardiology", "neurology", "orthopedics",
        "dermatology", "ent", "pulmonology", "gastroenterology", "emergency",
        name="department",
    ).create(op.get_bind(), checkfirst=False)
    sa.Enum("rule_engine", "llm", "manual", name="triage_source").create(op.get_bind(), checkfirst=False)

    # 3. patients table
    op.create_table(
        "patients",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("age", sa.SmallInteger(), nullable=False),
        sa.Column("gender", sa.String(20), nullable=False),
        sa.Column("contact_number", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("age >= 0 AND age <= 130", name="ck_patient_age"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. intake_records table
    op.create_table(
        "intake_records",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("symptoms_text", sa.Text(), nullable=False),
        sa.Column(
            "triage_source",
            sa.Enum("rule_engine", "llm", "manual", name="triage_source", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "ai_suggested_urgency",
            sa.Enum("routine", "priority", "urgent", name="urgency_level", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "ai_suggested_department",
            sa.Enum(
                "general_medicine", "cardiology", "neurology", "orthopedics",
                "dermatology", "ent", "pulmonology", "gastroenterology", "emergency",
                name="department",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("ai_reasoning", sa.String(220), nullable=True),
        sa.Column("ai_raw_response", JSONB(), nullable=True),
        sa.Column(
            "final_urgency",
            sa.Enum("routine", "priority", "urgent", name="urgency_level", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "final_department",
            sa.Enum(
                "general_medicine", "cardiology", "neurology", "orthopedics",
                "dermatology", "ent", "pulmonology", "gastroenterology", "emergency",
                name="department",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("urgency_overridden", sa.Boolean(), nullable=True),
        sa.Column("department_overridden", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)",
            name="ck_confidence_range",
        ),
        sa.CheckConstraint("char_length(symptoms_text) <= 2000", name="ck_symptoms_length"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 5. Indexes
    op.create_index("idx_intake_created_at", "intake_records", ["created_at"])
    op.create_index("idx_intake_urgency", "intake_records", ["final_urgency"])
    op.create_index("idx_intake_department", "intake_records", ["final_department"])
    op.create_index(
        "idx_patients_name_trgm",
        "patients",
        ["name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_index("idx_patients_name_trgm", table_name="patients")
    op.drop_index("idx_intake_department", table_name="intake_records")
    op.drop_index("idx_intake_urgency", table_name="intake_records")
    op.drop_index("idx_intake_created_at", table_name="intake_records")
    op.drop_table("intake_records")
    op.drop_table("patients")
    op.execute("DROP TYPE IF EXISTS triage_source")
    op.execute("DROP TYPE IF EXISTS department")
    op.execute("DROP TYPE IF EXISTS urgency_level")
