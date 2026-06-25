"""
tests/test_api.py - Phase 2 API-level tests.

Uses client (HTTP) and db_session (clean DB) fixtures.
Dashboard and full-flow tests go through the HTTP stack (response.json() dict access).
Create/List/Get tests use repo + Pydantic validation (model attribute access).
"""
from __future__ import annotations

import datetime
import uuid

import pytest

from app.models.intake import Department, IntakeRecord, Patient, TriageSource, UrgencyLevel
from app.repositories import dashboard_repo, intake_repo
from app.schemas.intake import IntakeCreate, IntakeOut


def _make_create(
    name: str = "Alice Smith",
    age: int = 30,
    gender: str = "F",
    contact: str = "555-0100",
    symptoms: str = "Fever and chills",
    final_urgency: UrgencyLevel = UrgencyLevel.priority,
    final_department: Department = Department.general_medicine,
    triage_source: TriageSource | None = None,
    ai_urgency: UrgencyLevel | None = None,
    ai_department: Department | None = None,
    ai_confidence: float | None = None,
) -> dict:
    return {
        "name": name,
        "age": age,
        "gender": gender,
        "contact_number": contact,
        "symptoms_text": symptoms,
        "triage_source": triage_source.value if triage_source else None,
        "ai_suggested_urgency": ai_urgency.value if ai_urgency else None,
        "ai_suggested_department": ai_department.value if ai_department else None,
        "ai_confidence": ai_confidence,
        "final_urgency": final_urgency.value,
        "final_department": final_department.value,
    }


# ---------------------------------------------------------------------------
# CREATE — repo + Pydantic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_no_ai(db_session):
    body = IntakeCreate(**_make_create())
    record = await intake_repo.create_patient_and_intake(db_session, body)
    await db_session.commit()

    assert record.patient.name == "Alice Smith"
    assert record.patient.age == 30
    assert record.urgency_overridden is None
    assert record.department_overridden is None
    assert record.triage_source is None

    out = IntakeOut.model_validate(record)
    assert out.patient.name == "Alice Smith"
    assert out.final_urgency == UrgencyLevel.priority


@pytest.mark.asyncio
async def test_create_ai_accepted(db_session):
    body = IntakeCreate(**_make_create(
        triage_source=TriageSource.llm,
        ai_urgency=UrgencyLevel.priority,
        ai_department=Department.general_medicine,
        ai_confidence=0.87,
        final_urgency=UrgencyLevel.priority,
        final_department=Department.general_medicine,
    ))
    record = await intake_repo.create_patient_and_intake(db_session, body)
    await db_session.commit()

    assert record.urgency_overridden is False
    assert record.department_overridden is False

    out = IntakeOut.model_validate(record)
    assert out.ai_suggested_urgency == UrgencyLevel.priority
    assert out.ai_confidence == 0.87
    assert out.urgency_overridden is False
    assert out.department_overridden is False


@pytest.mark.asyncio
async def test_create_fully_overridden(db_session):
    body = IntakeCreate(**_make_create(
        triage_source=TriageSource.llm,
        ai_urgency=UrgencyLevel.routine,
        ai_department=Department.dermatology,
        ai_confidence=0.55,
        final_urgency=UrgencyLevel.urgent,
        final_department=Department.emergency,
    ))
    record = await intake_repo.create_patient_and_intake(db_session, body)
    await db_session.commit()

    assert record.urgency_overridden is True
    assert record.department_overridden is True

    out = IntakeOut.model_validate(record)
    assert out.urgency_overridden is True
    assert out.department_overridden is True


@pytest.mark.asyncio
async def test_create_partial_override(db_session):
    body = IntakeCreate(**_make_create(
        triage_source=TriageSource.rule_engine,
        ai_urgency=UrgencyLevel.routine,
        ai_department=Department.general_medicine,
        final_urgency=UrgencyLevel.priority,
        final_department=Department.general_medicine,
    ))
    record = await intake_repo.create_patient_and_intake(db_session, body)
    await db_session.commit()

    assert record.urgency_overridden is True
    assert record.department_overridden is False

    out = IntakeOut.model_validate(record)
    assert out.urgency_overridden is True
    assert out.department_overridden is False


@pytest.mark.asyncio
async def test_create_minimal_valid(db_session):
    body = IntakeCreate(
        name="Bob",
        age=25,
        gender="M",
        contact_number="555-0199",
        symptoms_text="Headache",
        final_urgency=UrgencyLevel.routine,
        final_department=Department.neurology,
    )
    record = await intake_repo.create_patient_and_intake(db_session, body)
    await db_session.commit()

    assert record.patient.name == "Bob"
    out = IntakeOut.model_validate(record)
    assert out.patient.name == "Bob"


# ---------------------------------------------------------------------------
# LIST — repo + Pydantic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_empty(db_session):
    records, total = await intake_repo.list_intake(db_session)
    assert records == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_filtered_by_name(db_session):
    p1 = Patient(name="Charlie Davis", age=40, gender="M", contact_number="111")
    p2 = Patient(name="Alice Wonder", age=35, gender="F", contact_number="222")
    db_session.add_all([p1, p2])
    await db_session.flush()

    r1 = IntakeRecord(patient_id=p1.id, symptoms_text="Cough", final_urgency=UrgencyLevel.routine, final_department=Department.pulmonology)
    r2 = IntakeRecord(patient_id=p2.id, symptoms_text="Fever", final_urgency=UrgencyLevel.priority, final_department=Department.general_medicine)
    db_session.add_all([r1, r2])
    await db_session.commit()

    records, total = await intake_repo.list_intake(db_session, name="alice")
    assert total == 1
    assert records[0].patient.name == "Alice Wonder"

    records, total = await intake_repo.list_intake(db_session, name="davis")
    assert total == 1
    assert records[0].patient.name == "Charlie Davis"


@pytest.mark.asyncio
async def test_list_filtered_by_urgency(db_session):
    p = Patient(name="Dave", age=22, gender="M", contact_number="333")
    db_session.add(p)
    await db_session.flush()

    r_urgent = IntakeRecord(patient_id=p.id, symptoms_text="Chest pain", final_urgency=UrgencyLevel.urgent, final_department=Department.emergency)
    r_routine = IntakeRecord(patient_id=p.id, symptoms_text="Checkup", final_urgency=UrgencyLevel.routine, final_department=Department.general_medicine)
    db_session.add_all([r_urgent, r_routine])
    await db_session.commit()

    records, total = await intake_repo.list_intake(db_session, urgency=UrgencyLevel.urgent)
    assert total == 1
    assert records[0].final_urgency == UrgencyLevel.urgent

    records, total = await intake_repo.list_intake(db_session, urgency=UrgencyLevel.routine)
    assert total == 1
    assert records[0].final_urgency == UrgencyLevel.routine


@pytest.mark.asyncio
async def test_list_filtered_by_department(db_session):
    p = Patient(name="Eve", age=28, gender="F", contact_number="444")
    db_session.add(p)
    await db_session.flush()

    r_cardio = IntakeRecord(patient_id=p.id, symptoms_text="Palpitations", final_urgency=UrgencyLevel.urgent, final_department=Department.cardiology)
    r_neuro = IntakeRecord(patient_id=p.id, symptoms_text="Migraine", final_urgency=UrgencyLevel.priority, final_department=Department.neurology)
    db_session.add_all([r_cardio, r_neuro])
    await db_session.commit()

    records, total = await intake_repo.list_intake(db_session, department=Department.cardiology)
    assert total == 1
    assert records[0].final_department == Department.cardiology


@pytest.mark.asyncio
async def test_list_paginated(db_session):
    patients = []
    for i in range(7):
        p = Patient(name=f"Patient{i}", age=20 + i, gender="M", contact_number=f"555{i:04d}")
        db_session.add(p)
        patients.append(p)
    await db_session.flush()

    for i in range(7):
        r = IntakeRecord(patient_id=patients[i].id, symptoms_text=f"Sx{i}", final_urgency=UrgencyLevel.routine, final_department=Department.general_medicine)
        db_session.add(r)
    await db_session.commit()

    page1, total = await intake_repo.list_intake(db_session, limit=3, offset=0)
    assert len(page1) == 3
    assert total == 7

    page2, total = await intake_repo.list_intake(db_session, limit=3, offset=3)
    assert len(page2) == 3
    assert total == 7

    page3, total = await intake_repo.list_intake(db_session, limit=3, offset=6)
    assert len(page3) == 1
    assert total == 7


# ---------------------------------------------------------------------------
# GET BY ID — repo + Pydantic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_by_id_found(db_session):
    p = Patient(name="Frank", age=50, gender="M", contact_number="666")
    db_session.add(p)
    await db_session.flush()
    r = IntakeRecord(patient_id=p.id, symptoms_text="Back pain", final_urgency=UrgencyLevel.priority, final_department=Department.orthopedics)
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r, attribute_names=["patient"])

    record = await intake_repo.get_intake_by_id(db_session, r.id)
    assert record is not None
    out = IntakeOut.model_validate(record)
    assert out.patient.name == "Frank"
    assert out.symptoms_text == "Back pain"


@pytest.mark.asyncio
async def test_get_by_id_not_found(db_session):
    fake_id = uuid.uuid4()
    record = await intake_repo.get_intake_by_id(db_session, fake_id)
    assert record is None


# ---------------------------------------------------------------------------
# DASHBOARD — HTTP client + response.json() dict access
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dashboard_empty(client, db_session):
    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["by_urgency"]["routine"] == 0
    assert data["by_urgency"]["priority"] == 0
    assert data["by_urgency"]["urgent"] == 0
    assert data["by_department"]["general_medicine"] == 0
    assert data["override_rate"] is None


@pytest.mark.asyncio
async def test_dashboard_counts(client, db_session):
    p = Patient(name="Grace", age=33, gender="F", contact_number="777")
    db_session.add(p)
    await db_session.flush()
    db_session.add_all([
        IntakeRecord(patient_id=p.id, symptoms_text="Fever", final_urgency=UrgencyLevel.urgent, final_department=Department.emergency),
        IntakeRecord(patient_id=p.id, symptoms_text="Cough", final_urgency=UrgencyLevel.priority, final_department=Department.pulmonology),
        IntakeRecord(patient_id=p.id, symptoms_text="Rash", final_urgency=UrgencyLevel.routine, final_department=Department.dermatology),
    ])
    await db_session.commit()

    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["by_urgency"]["urgent"] == 1
    assert data["by_urgency"]["priority"] == 1
    assert data["by_urgency"]["routine"] == 1
    assert data["by_department"]["emergency"] == 1
    assert data["by_department"]["pulmonology"] == 1
    assert data["by_department"]["dermatology"] == 1


@pytest.mark.asyncio
async def test_dashboard_override_rate_zero(client, db_session):
    p = Patient(name="Hans", age=45, gender="M", contact_number="888")
    db_session.add(p)
    await db_session.flush()
    db_session.add(IntakeRecord(
        patient_id=p.id,
        symptoms_text="Sprain",
        triage_source=TriageSource.llm,
        ai_suggested_urgency=UrgencyLevel.routine,
        ai_suggested_department=Department.orthopedics,
        urgency_overridden=False,
        department_overridden=False,
        final_urgency=UrgencyLevel.routine,
        final_department=Department.orthopedics,
    ))
    await db_session.commit()

    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["override_rate"] == 0.0


@pytest.mark.asyncio
async def test_dashboard_override_rate_full(client, db_session):
    p = Patient(name="Ivy", age=29, gender="F", contact_number="999")
    db_session.add(p)
    await db_session.flush()
    db_session.add(IntakeRecord(
        patient_id=p.id,
        symptoms_text="Joint pain",
        triage_source=TriageSource.rule_engine,
        ai_suggested_urgency=UrgencyLevel.routine,
        ai_suggested_department=Department.orthopedics,
        urgency_overridden=True,
        department_overridden=True,
        final_urgency=UrgencyLevel.priority,
        final_department=Department.emergency,
    ))
    await db_session.commit()

    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["override_rate"] == 1.0


# ---------------------------------------------------------------------------
# FULL FLOW — HTTP client (create, then list, then get, then dashboard)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_flow_http(client, db_session):
    body = _make_create(
        name="Zara Kim",
        age=26,
        gender="F",
        contact="555-9000",
        symptoms="Severe migraine for 2 days",
        final_urgency=UrgencyLevel.priority,
        final_department=Department.neurology,
    )

    # Create
    response = await client.post("/api/v1/intake", json=body)
    assert response.status_code == 201
    created = response.json()
    record_id = created["id"]
    assert created["patient"]["name"] == "Zara Kim"
    assert created["final_urgency"] == "priority"
    assert created["final_department"] == "neurology"

    # List — find by name
    response = await client.get("/api/v1/intake", params={"name": "zara"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["patient"]["name"] == "Zara Kim"

    # Get by ID
    response = await client.get(f"/api/v1/intake/{record_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["patient"]["name"] == "Zara Kim"
    assert data["symptoms_text"] == "Severe migraine for 2 days"

    # Dashboard — new record shows up
    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["by_urgency"]["priority"] >= 1
    assert data["by_department"]["neurology"] >= 1