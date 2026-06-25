"""tests/test_intake_api.py — Phase 11.3 + 11.4 HTTP-level intake API tests.

Tests POST /intake, GET /intake, GET /intake/{id}, GET /dashboard/summary
via HTTP (client fixture) with full validation of request/response.

Covers Phase 11.3 items:
  - POST /intake: full valid body -> 201; missing required fields -> 422;
    invalid enum -> 422
  - Override flag computation via HTTP
  - GET /intake: pagination, name filter, date filter, urgency filter
  - GET /intake/{id}: found -> 200; not found -> 404
  - GET /dashboard/summary: correct counts and breakdown
  - Full flow: create -> appears in search -> appears in dashboard counts

Covers Phase 11.4 edge cases:
  - Symptoms at exactly 2000 chars -> accepted
  - Symptoms 2001 chars -> 422
  - Age 131 -> 422; age -1 -> 422
  - Save without Analyze -> all ai_* null, both override flags null
  - Partial override via HTTP
"""
from __future__ import annotations

import pytest

from app.models.intake import Department, TriageSource, UrgencyLevel


def _intake_body(overrides=None):
    base = {
        "name": "Test Patient",
        "age": 30,
        "gender": "M",
        "contact_number": "555-0100",
        "symptoms_text": "Mild fever and headache for 2 days",
        "triage_source": None,
        "ai_suggested_urgency": None,
        "ai_suggested_department": None,
        "ai_confidence": None,
        "final_urgency": "priority",
        "final_department": "general_medicine",
    }
    if overrides:
        base.update(overrides)
    return base


class TestCreateIntake:
    @pytest.mark.asyncio
    async def test_create_intake_full_valid_201(self, client, db_session):
        body = _intake_body()
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 201
        data = response.json()
        assert data["patient"]["name"] == "Test Patient"
        assert data["final_urgency"] == "priority"
        assert data["final_department"] == "general_medicine"
        assert data["urgency_overridden"] is None
        assert data["department_overridden"] is None

    @pytest.mark.asyncio
    async def test_create_intake_missing_name_422(self, client, db_session):
        body = _intake_body(overrides={"name": None})
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_intake_missing_final_urgency_422(self, client, db_session):
        body = {k: v for k, v in _intake_body().items() if k != "final_urgency"}
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_intake_invalid_urgency_enum_422(self, client, db_session):
        body = _intake_body(overrides={"final_urgency": "super_urgent"})
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_intake_invalid_department_enum_422(self, client, db_session):
        body = _intake_body(overrides={"final_department": "cardio"})
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_intake_symptoms_exactly_2000_accepted(self, client, db_session):
        body = _intake_body(overrides={"symptoms_text": "x" * 2000})
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 201
        data = response.json()
        assert len(data["symptoms_text"]) == 2000

    @pytest.mark.asyncio
    async def test_create_intake_symptoms_2001_422(self, client, db_session):
        body = _intake_body(overrides={"symptoms_text": "x" * 2001})
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_intake_age_131_422(self, client, db_session):
        body = _intake_body(overrides={"age": 131})
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_intake_age_negative_422(self, client, db_session):
        body = _intake_body(overrides={"age": -1})
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_intake_override_flag_via_http(self, client, db_session):
        body = _intake_body(overrides={
            "triage_source": "llm",
            "ai_suggested_urgency": "routine",
            "ai_suggested_department": "general_medicine",
            "ai_confidence": 0.75,
            "final_urgency": "urgent",
            "final_department": "emergency",
        })
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 201
        data = response.json()
        assert data["urgency_overridden"] is True
        assert data["department_overridden"] is True
        assert data["ai_suggested_urgency"] == "routine"
        assert data["final_urgency"] == "urgent"

    @pytest.mark.asyncio
    async def test_create_no_ai_all_fields_null(self, client, db_session):
        body = _intake_body(overrides={
            "triage_source": None,
            "ai_suggested_urgency": None,
            "ai_suggested_department": None,
            "ai_confidence": None,
            "final_urgency": "routine",
            "final_department": "general_medicine",
        })
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 201
        data = response.json()
        assert data["triage_source"] is None
        assert data["ai_suggested_urgency"] is None
        assert data["ai_suggested_department"] is None
        assert data["ai_confidence"] is None
        assert data["urgency_overridden"] is None
        assert data["department_overridden"] is None

    @pytest.mark.asyncio
    async def test_create_partial_override_urgency_only(self, client, db_session):
        body = _intake_body(overrides={
            "triage_source": "llm",
            "ai_suggested_urgency": "routine",
            "ai_suggested_department": "general_medicine",
            "final_urgency": "priority",
            "final_department": "general_medicine",
        })
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 201
        data = response.json()
        assert data["urgency_overridden"] is True
        assert data["department_overridden"] is False

    @pytest.mark.asyncio
    async def test_create_partial_override_department_only(self, client, db_session):
        body = _intake_body(overrides={
            "triage_source": "rule_engine",
            "ai_suggested_urgency": "urgent",
            "ai_suggested_department": "emergency",
            "final_urgency": "urgent",
            "final_department": "cardiology",
        })
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 201
        data = response.json()
        assert data["urgency_overridden"] is False
        assert data["department_overridden"] is True


class TestListIntake:
    @pytest.mark.asyncio
    async def test_get_intake_pagination(self, client, db_session):
        for i in range(5):
            await client.post("/api/v1/intake", json=_intake_body(overrides={
                "name": f"Patient {i}",
                "age": 20 + i,
            }))

        page1 = await client.get("/api/v1/intake", params={"limit": 2, "offset": 0})
        assert page1.status_code == 200
        d1 = page1.json()
        assert d1["total"] == 5
        assert len(d1["items"]) == 2
        assert d1["page"] == 1

        page2 = await client.get("/api/v1/intake", params={"limit": 2, "offset": 2})
        d2 = page2.json()
        assert len(d2["items"]) == 2
        assert d2["page"] == 2

    @pytest.mark.asyncio
    async def test_get_intake_name_filter(self, client, db_session):
        await client.post("/api/v1/intake", json=_intake_body(overrides={"name": "Alice Wonderland"}))
        await client.post("/api/v1/intake", json=_intake_body(overrides={"name": "Bob Smith"}))
        await client.post("/api/v1/intake", json=_intake_body(overrides={"name": "Alice Cooper"}))

        result = await client.get("/api/v1/intake", params={"name": "alice"})
        data = result.json()
        assert data["total"] == 2
        names = {item["patient"]["name"] for item in data["items"]}
        assert names == {"Alice Wonderland", "Alice Cooper"}

    @pytest.mark.asyncio
    async def test_get_intake_date_filter(self, client, db_session):
        await client.post("/api/v1/intake", json=_intake_body(overrides={"name": "Today Patient"}))
        result = await client.get("/api/v1/intake", params={"date_from": "2020-01-01", "date_to": "2030-12-31"})
        assert result.status_code == 200
        data = result.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_intake_urgency_filter(self, client, db_session):
        await client.post("/api/v1/intake", json=_intake_body(overrides={"name": "Urgent Patient", "final_urgency": "urgent"}))
        await client.post("/api/v1/intake", json=_intake_body(overrides={"name": "Routine Patient", "final_urgency": "routine"}))

        result = await client.get("/api/v1/intake", params={"urgency": "urgent"})
        data = result.json()
        assert data["total"] == 1
        assert data["items"][0]["final_urgency"] == "urgent"

    @pytest.mark.asyncio
    async def test_get_intake_department_filter(self, client, db_session):
        await client.post("/api/v1/intake", json=_intake_body(overrides={"name": "Cardio Patient", "final_department": "cardiology"}))
        await client.post("/api/v1/intake", json=_intake_body(overrides={"name": "Neuro Patient", "final_department": "neurology"}))

        result = await client.get("/api/v1/intake", params={"department": "cardiology"})
        data = result.json()
        assert data["total"] == 1
        assert data["items"][0]["final_department"] == "cardiology"


class TestGetIntakeById:
    @pytest.mark.asyncio
    async def test_get_intake_by_id_found(self, client, db_session):
        create_resp = await client.post("/api/v1/intake", json=_intake_body(overrides={"name": "Find Me"}))
        record_id = create_resp.json()["id"]

        get_resp = await client.get(f"/api/v1/intake/{record_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["patient"]["name"] == "Find Me"
        assert data["symptoms_text"] == "Mild fever and headache for 2 days"

    @pytest.mark.asyncio
    async def test_get_intake_by_id_not_found_404(self, client, db_session):
        import uuid
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/intake/{fake_id}")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


class TestDashboardSummary:
    @pytest.mark.asyncio
    async def test_dashboard_after_intake(self, client, db_session):
        await client.post("/api/v1/intake", json=_intake_body(overrides={
            "name": "Dash Patient",
            "final_urgency": "priority",
            "final_department": "neurology",
        }))

        response = await client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["by_urgency"]["priority"] >= 1
        assert data["by_department"]["neurology"] >= 1


class TestFullFlow:
    @pytest.mark.asyncio
    async def test_full_flow_create_search_dashboard(self, client, db_session):
        body = _intake_body(overrides={
            "name": "Flow Test Patient",
            "age": 45,
            "gender": "F",
            "contact_number": "555-9999",
            "symptoms_text": "Severe migraine for the past week",
            "triage_source": "llm",
            "ai_suggested_urgency": "priority",
            "ai_suggested_department": "neurology",
            "ai_confidence": 0.78,
            "final_urgency": "priority",
            "final_department": "neurology",
        })

        create_resp = await client.post("/api/v1/intake", json=body)
        assert create_resp.status_code == 201
        created = create_resp.json()
        record_id = created["id"]
        assert created["patient"]["name"] == "Flow Test Patient"
        assert created["final_urgency"] == "priority"
        assert created["urgency_overridden"] is False

        search_resp = await client.get("/api/v1/intake", params={"name": "flow test"})
        assert search_resp.status_code == 200
        search_data = search_resp.json()
        assert search_data["total"] == 1
        assert search_data["items"][0]["id"] == record_id

        get_resp = await client.get(f"/api/v1/intake/{record_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["patient"]["name"] == "Flow Test Patient"

        dash_resp = await client.get("/api/v1/dashboard/summary")
        assert dash_resp.status_code == 200
        dash_data = dash_resp.json()
        assert dash_data["total"] >= 1
        assert dash_data["by_urgency"]["priority"] >= 1
        assert dash_data["by_department"]["neurology"] >= 1
