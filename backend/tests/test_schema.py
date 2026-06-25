"""
tests/test_schema.py - Phase 1 database-level schema tests.

Uses the shared db_session fixture from conftest.py (no local engine setup).
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.intake import Department, IntakeRecord, Patient, TriageSource, UrgencyLevel


def _intake(**kw):
    d = dict(patient_id=uuid.uuid4(), symptoms_text="Chest pain", final_urgency=UrgencyLevel.urgent, final_department=Department.emergency)
    d.update(kw)
    return IntakeRecord(**d)

@pytest.mark.asyncio
async def test_patients_table_exists(db_session):
    r = await db_session.execute(text("SELECT 1 FROM information_schema.tables WHERE table_name = 'patients'"))
    assert r.scalar() == 1

@pytest.mark.asyncio
async def test_intake_records_table_exists(db_session):
    r = await db_session.execute(text("SELECT 1 FROM information_schema.tables WHERE table_name = 'intake_records'"))
    assert r.scalar() == 1

@pytest.mark.asyncio
async def test_urgency_level_enum(db_session):
    r = await db_session.execute(text("SELECT unnest(enum_range(NULL::urgency_level))"))
    assert set(r.scalars().all()) == {"routine", "priority", "urgent"}

@pytest.mark.asyncio
async def test_department_enum(db_session):
    r = await db_session.execute(text("SELECT unnest(enum_range(NULL::department))"))
    assert set(r.scalars().all()) == {"general_medicine", "cardiology", "neurology", "orthopedics", "dermatology", "ent", "pulmonology", "gastroenterology", "emergency"}

@pytest.mark.asyncio
async def test_triage_source_enum(db_session):
    r = await db_session.execute(text("SELECT unnest(enum_range(NULL::triage_source))"))
    assert set(r.scalars().all()) == {"rule_engine", "llm", "manual"}

@pytest.mark.asyncio
async def test_age_131_rejected(db_session):
    db_session.add(Patient(name="T", age=131, gender="M", contact_number="123"))
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

@pytest.mark.asyncio
async def test_age_0_accepted(db_session):
    db_session.add(Patient(name="Baby", age=0, gender="F", contact_number="123"))
    await db_session.commit()

@pytest.mark.asyncio
async def test_age_130_accepted(db_session):
    db_session.add(Patient(name="Old", age=130, gender="M", contact_number="123"))
    await db_session.commit()

@pytest.mark.asyncio
async def test_symptoms_2001_chars_rejected(db_session):
    p = Patient(name="T", age=30, gender="M", contact_number="123")
    db_session.add(p)
    await db_session.flush()
    r = _intake(patient_id=p.id, symptoms_text="x" * 2001)
    db_session.add(r)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

@pytest.mark.asyncio
async def test_confidence_1_5_rejected(db_session):
    p = Patient(name="T", age=30, gender="M", contact_number="123")
    db_session.add(p)
    await db_session.flush()
    r = _intake(patient_id=p.id, ai_confidence=1.5)
    db_session.add(r)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

@pytest.mark.asyncio
async def test_confidence_null_accepted(db_session):
    p = Patient(name="T", age=30, gender="M", contact_number="123")
    db_session.add(p)
    await db_session.flush()
    r = _intake(patient_id=p.id, ai_confidence=None)
    db_session.add(r)
    await db_session.commit()

@pytest.mark.asyncio
async def test_final_urgency_not_null(db_session):
    p = Patient(name="T", age=30, gender="M", contact_number="123")
    db_session.add(p)
    await db_session.flush()
    r = IntakeRecord(patient_id=p.id, symptoms_text="Fever", final_urgency=None, final_department=Department.emergency)
    db_session.add(r)
    with pytest.raises((IntegrityError, TypeError)):
        await db_session.commit()
    await db_session.rollback()

@pytest.mark.asyncio
async def test_final_department_not_null(db_session):
    p = Patient(name="T", age=30, gender="M", contact_number="123")
    db_session.add(p)
    await db_session.flush()
    r = IntakeRecord(patient_id=p.id, symptoms_text="Fever", final_urgency=UrgencyLevel.urgent, final_department=None)
    db_session.add(r)
    with pytest.raises((IntegrityError, TypeError)):
        await db_session.commit()
    await db_session.rollback()

@pytest.mark.asyncio
async def test_cascade_delete(db_session):
    p = Patient(name="T", age=30, gender="M", contact_number="123")
    db_session.add(p)
    await db_session.flush()
    r = _intake(patient_id=p.id)
    db_session.add(r)
    await db_session.commit()
    rid = r.id
    await db_session.delete(p)
    await db_session.commit()
    assert await db_session.get(IntakeRecord, rid) is None

@pytest.mark.asyncio
async def test_override_case_no_ai(db_session):
    p = Patient(name="T", age=30, gender="M", contact_number="123")
    db_session.add(p)
    await db_session.flush()
    r = IntakeRecord(patient_id=p.id, symptoms_text="Headache", triage_source=None, ai_suggested_urgency=None, ai_suggested_department=None, urgency_overridden=None, department_overridden=None, final_urgency=UrgencyLevel.priority, final_department=Department.general_medicine)
    db_session.add(r)
    await db_session.commit()
    assert r.urgency_overridden is None

@pytest.mark.asyncio
async def test_override_case_accepted(db_session):
    p = Patient(name="T", age=30, gender="M", contact_number="123")
    db_session.add(p)
    await db_session.flush()
    r = IntakeRecord(patient_id=p.id, symptoms_text="Chest pain", triage_source=TriageSource.llm, ai_suggested_urgency=UrgencyLevel.urgent, ai_suggested_department=Department.emergency, urgency_overridden=False, department_overridden=False, final_urgency=UrgencyLevel.urgent, final_department=Department.emergency)
    db_session.add(r)
    await db_session.commit()
    assert r.urgency_overridden is False
    assert r.department_overridden is False

@pytest.mark.asyncio
async def test_override_case_overridden(db_session):
    p = Patient(name="T", age=30, gender="M", contact_number="123")
    db_session.add(p)
    await db_session.flush()
    r = IntakeRecord(patient_id=p.id, symptoms_text="Headache", triage_source=TriageSource.llm, ai_suggested_urgency=UrgencyLevel.routine, ai_suggested_department=Department.general_medicine, urgency_overridden=True, department_overridden=True, final_urgency=UrgencyLevel.urgent, final_department=Department.emergency)
    db_session.add(r)
    await db_session.commit()
    assert r.urgency_overridden is True
    assert r.department_overridden is True

@pytest.mark.asyncio
async def test_override_case_partial(db_session):
    p = Patient(name="T", age=30, gender="M", contact_number="123")
    db_session.add(p)
    await db_session.flush()
    r = IntakeRecord(patient_id=p.id, symptoms_text="Fever", triage_source=TriageSource.llm, ai_suggested_urgency=UrgencyLevel.routine, ai_suggested_department=Department.general_medicine, urgency_overridden=True, department_overridden=False, final_urgency=UrgencyLevel.priority, final_department=Department.general_medicine)
    db_session.add(r)
    await db_session.commit()
    assert r.urgency_overridden is True
    assert r.department_overridden is False

@pytest.mark.asyncio
async def test_ai_fields_all_null_valid(db_session):
    p = Patient(name="T", age=30, gender="M", contact_number="123")
    db_session.add(p)
    await db_session.flush()
    r = IntakeRecord(patient_id=p.id, symptoms_text="Vague symptoms", triage_source=None, ai_suggested_urgency=None, ai_suggested_department=None, urgency_overridden=None, department_overridden=None, final_urgency=UrgencyLevel.priority, final_department=Department.general_medicine)
    db_session.add(r)
    await db_session.commit()
    assert r.ai_suggested_urgency is None

@pytest.mark.asyncio
async def test_indexes_exist(db_session):
    r = await db_session.execute(text("SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND indexname IN ('idx_intake_created_at', 'idx_intake_urgency', 'idx_intake_department', 'idx_patients_name_trgm')"))
    found = {row[0] for row in r.all()}
    assert found == {"idx_intake_created_at", "idx_intake_urgency", "idx_intake_department", "idx_patients_name_trgm"}, f"Missing: {found}"
