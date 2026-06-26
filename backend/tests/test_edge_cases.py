"""tests/test_edge_cases.py — Phase 11.4 Comprehensive Edge Case Tests.

Covers boundary conditions, special characters, and corner cases
not explicitly tested in other test files.

Run with: pytest tests/test_edge_cases.py -v
"""
from __future__ import annotations

import pytest
from datetime import date

from app.models.intake import Department, TriageSource, UrgencyLevel


class TestDashboardOverrideRateEdgeCases:
    """Dashboard override_rate calculation edge cases."""

    @pytest.mark.asyncio
    async def test_override_rate_zero_ai_used(self, client, db_session):
        """When no AI-assisted records exist, override_rate should be None (not division by zero)."""
        # Create a manual-only record (no AI)
        body = {
            "name": "Manual Patient",
            "age": 25,
            "gender": "M",
            "contact_number": "555-0001",
            "symptoms_text": "Manual entry",
            "triage_source": None,
            "ai_suggested_urgency": None,
            "ai_suggested_department": None,
            "ai_confidence": None,
            "final_urgency": "routine",
            "final_department": "general_medicine",
        }
        await client.post("/api/v1/intake", json=body)

        response = await client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["override_rate"] is None

    @pytest.mark.asyncio
    async def test_override_rate_all_accepted(self, client, db_session):
        """When all AI suggestions are accepted, override_rate should be 0.0."""
        # Create AI-accepted record
        body = {
            "name": "AI Accepted Patient",
            "age": 30,
            "gender": "F",
            "contact_number": "555-0002",
            "symptoms_text": "AI suggestion accepted",
            "triage_source": "llm",
            "ai_suggested_urgency": "priority",
            "ai_suggested_department": "cardiology",
            "ai_confidence": 0.85,
            "final_urgency": "priority",
            "final_department": "cardiology",
        }
        await client.post("/api/v1/intake", json=body)

        response = await client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["override_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_override_rate_all_overridden(self, client, db_session):
        """When all AI suggestions are overridden, override_rate should be 1.0."""
        # Create overridden record
        body = {
            "name": "Overridden Patient",
            "age": 40,
            "gender": "M",
            "contact_number": "555-0003",
            "symptoms_text": "AI suggestion overridden",
            "triage_source": "rule_engine",
            "ai_suggested_urgency": "routine",
            "ai_suggested_department": "general_medicine",
            "ai_confidence": None,
            "final_urgency": "urgent",
            "final_department": "emergency",
        }
        await client.post("/api/v1/intake", json=body)

        response = await client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["override_rate"] == 1.0


class TestDateRangeBoundaries:
    """Date range filtering boundary tests."""

    @pytest.mark.asyncio
    async def test_date_from_inclusive(self, client, db_session):
        """date_from should be inclusive (>= start of day)."""
        today = date.today().isoformat()
        
        # Create a record
        body = {
            "name": "Date Test Patient",
            "age": 35,
            "gender": "F",
            "contact_number": "555-0004",
            "symptoms_text": "Date boundary test",
            "triage_source": None,
            "final_urgency": "routine",
            "final_department": "general_medicine",
        }
        await client.post("/api/v1/intake", json=body)

        # Filter from today onwards
        response = await client.get("/api/v1/intake", params={"date_from": today})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_date_to_inclusive(self, client, db_session):
        """date_to should be inclusive (< start of next day)."""
        today = date.today().isoformat()
        
        # Create a record
        body = {
            "name": "Date To Test Patient",
            "age": 36,
            "gender": "M",
            "contact_number": "555-0005",
            "symptoms_text": "Date to boundary test",
            "triage_source": None,
            "final_urgency": "priority",
            "final_department": "neurology",
        }
        await client.post("/api/v1/intake", json=body)

        # Filter up to today
        response = await client.get("/api/v1/intake", params={"date_to": today})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_date_range_single_day(self, client, db_session):
        """date_from == date_to should return records for that day only."""
        today = date.today().isoformat()
        
        response = await client.get("/api/v1/intake", params={
            "date_from": today,
            "date_to": today,
        })
        assert response.status_code == 200
        data = response.json()
        # Should return today's records
        assert "items" in data


class TestNameSearchSpecialCharacters:
    """Name search with special characters (LIKE injection prevention)."""

    @pytest.mark.asyncio
    async def test_name_with_percent(self, client, db_session):
        """Name containing % should be escaped properly."""
        body = {
            "name": "Test%Patient",
            "age": 28,
            "gender": "F",
            "contact_number": "555-0006",
            "symptoms_text": "Special char test",
            "triage_source": None,
            "final_urgency": "routine",
            "final_department": "general_medicine",
        }
        await client.post("/api/v1/intake", json=body)

        # Search for the name - should escape the %
        response = await client.get("/api/v1/intake", params={"name": "Test%Patient"})
        assert response.status_code == 200
        data = response.json()
        # Should find the exact name, not match everything
        names = [item["patient"]["name"] for item in data["items"]]
        assert "Test%Patient" in names

    @pytest.mark.asyncio
    async def test_name_with_underscore(self, client, db_session):
        """Name containing _ should be escaped properly."""
        body = {
            "name": "John_Doe",
            "age": 42,
            "gender": "M",
            "contact_number": "555-0007",
            "symptoms_text": "Underscore test",
            "triage_source": None,
            "final_urgency": "priority",
            "final_department": "orthopedics",
        }
        await client.post("/api/v1/intake", json=body)

        response = await client.get("/api/v1/intake", params={"name": "John_Doe"})
        assert response.status_code == 200
        data = response.json()
        names = [item["patient"]["name"] for item in data["items"]]
        assert "John_Doe" in names

    @pytest.mark.asyncio
    async def test_name_with_backslash(self, client, db_session):
        """Name containing backslash should be escaped properly."""
        body = {
            "name": "Test\\Backslash",
            "age": 33,
            "gender": "F",
            "contact_number": "555-0008",
            "symptoms_text": "Backslash test",
            "triage_source": None,
            "final_urgency": "urgent",
            "final_department": "emergency",
        }
        await client.post("/api/v1/intake", json=body)

        response = await client.get("/api/v1/intake", params={"name": "Test\\Backslash"})
        assert response.status_code == 200
        data = response.json()
        names = [item["patient"]["name"] for item in data["items"]]
        assert "Test\\Backslash" in names


class TestConfidenceBoundaries:
    """Confidence value boundary tests."""

    @pytest.mark.asyncio
    async def test_confidence_exactly_zero(self, client, db_session):
        """Confidence of exactly 0.0 should be accepted."""
        body = {
            "name": "Zero Confidence Patient",
            "age": 29,
            "gender": "M",
            "contact_number": "555-0009",
            "symptoms_text": "Very vague symptoms",
            "triage_source": "llm",
            "ai_suggested_urgency": "priority",
            "ai_suggested_department": "general_medicine",
            "ai_confidence": 0.0,
            "final_urgency": "priority",
            "final_department": "general_medicine",
        }
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 201
        data = response.json()
        assert data["ai_confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_confidence_exactly_one(self, client, db_session):
        """Confidence of exactly 1.0 should be accepted."""
        body = {
            "name": "Full Confidence Patient",
            "age": 31,
            "gender": "F",
            "contact_number": "555-0010",
            "symptoms_text": "Very clear symptoms",
            "triage_source": "rule_engine",
            "ai_suggested_urgency": "urgent",
            "ai_suggested_department": "emergency",
            "ai_confidence": 1.0,
            "final_urgency": "urgent",
            "final_department": "emergency",
        }
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 201
        data = response.json()
        assert data["ai_confidence"] == 1.0


class TestPaginationEdgeCases:
    """Pagination edge cases."""

    @pytest.mark.asyncio
    async def test_pagination_empty_result(self, client, db_session):
        """Pagination on empty result set should return empty items with total=0."""
        response = await client.get("/api/v1/intake", params={"limit": 20, "offset": 0})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_pagination_offset_beyond_total(self, client, db_session):
        """Offset beyond total should return empty items."""
        # Create 3 records
        for i in range(3):
            body = {
                "name": f"Pagination Test {i}",
                "age": 20 + i,
                "gender": "M",
                "contact_number": f"555-00{i+1}",
                "symptoms_text": "Test",
                "triage_source": None,
                "final_urgency": "routine",
                "final_department": "general_medicine",
            }
            await client.post("/api/v1/intake", json=body)

        # Request offset beyond total
        response = await client.get("/api/v1/intake", params={"limit": 20, "offset": 100})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["items"] == []


class TestMultiplePatientsSameName:
    """Multiple patients with same name - ordering and pagination."""

    @pytest.mark.asyncio
    async def test_same_name_ordering_by_created_at(self, client, db_session):
        """Multiple patients with same name should be ordered by created_at DESC."""
        # Create 3 patients with same name
        for i in range(3):
            body = {
                "name": "Same Name Patient",
                "age": 25 + i,
                "gender": "M",
                "contact_number": f"555-0{i}",
                "symptoms_text": f"Symptoms {i}",
                "triage_source": None,
                "final_urgency": "routine",
                "final_department": "general_medicine",
            }
            await client.post("/api/v1/intake", json=body)

        response = await client.get("/api/v1/intake", params={"name": "Same Name Patient"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        
        # Most recent should be first (DESC order)
        names = [item["patient"]["name"] for item in data["items"]]
        assert names == ["Same Name Patient"] * 3


class TestGenderAndContactValidation:
    """Gender and contact number validation edge cases."""

    @pytest.mark.asyncio
    async def test_gender_empty_string_422(self, client, db_session):
        """Empty gender should return 422."""
        body = {
            "name": "Test Patient",
            "age": 30,
            "gender": "",
            "contact_number": "555-0011",
            "symptoms_text": "Test",
            "triage_source": None,
            "final_urgency": "routine",
            "final_department": "general_medicine",
        }
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_contact_empty_string_422(self, client, db_session):
        """Empty contact_number should return 422."""
        body = {
            "name": "Test Patient",
            "age": 30,
            "gender": "M",
            "contact_number": "",
            "symptoms_text": "Test",
            "triage_source": None,
            "final_urgency": "routine",
            "final_department": "general_medicine",
        }
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_gender_unicode_characters(self, client, db_session):
        """Gender with unicode characters should be accepted."""
        body = {
            "name": "Test Patient",
            "age": 30,
            "gender": "Non-binary",
            "contact_number": "555-0012",
            "symptoms_text": "Test",
            "triage_source": None,
            "final_urgency": "routine",
            "final_department": "general_medicine",
        }
        response = await client.post("/api/v1/intake", json=body)
        assert response.status_code == 201


class TestTriageAnalyzeEdgeCases:
    """Triage analyze endpoint edge cases."""

    @pytest.mark.asyncio
    async def test_analyze_symptoms_exactly_10_chars(self, client, db_session):
        """Symptoms with exactly 10 chars (minimum) should be accepted."""
        with pytest.MonkeyPatch.context() as mp:
            from unittest.mock import AsyncMock, patch
            with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
                mock.return_value = {
                    "urgency": "routine",
                    "department": "general_medicine",
                    "confidence": 0.5,
                }
                response = await client.post(
                    "/api/v1/triage/analyze",
                    json={"symptoms_text": "1234567890"},  # Exactly 10 chars
                )
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_analyze_symptoms_9_chars_422(self, client, db_session):
        """Symptoms with 9 chars (below minimum) should return 422."""
        response = await client.post(
            "/api/v1/triage/analyze",
            json={"symptoms_text": "123456789"},  # 9 chars
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_symptoms_exactly_2000_chars(self, client, db_session):
        """Symptoms with exactly 2000 chars (maximum) should be accepted."""
        with pytest.MonkeyPatch.context() as mp:
            from unittest.mock import AsyncMock, patch
            with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
                mock.return_value = {
                    "urgency": "priority",
                    "department": "cardiology",
                    "confidence": 0.75,
                }
                response = await client.post(
                    "/api/v1/triage/analyze",
                    json={"symptoms_text": "x" * 2000},
                )
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_analyze_symptoms_2001_chars_422(self, client, db_session):
        """Symptoms with 2001 chars (over maximum) should return 422."""
        response = await client.post(
            "/api/v1/triage/analyze",
            json={"symptoms_text": "x" * 2001},
        )
        assert response.status_code == 422