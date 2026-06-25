"""
tests/test_health.py — Phase 0 smoke tests (updated for Phase 3).

These tests verify the application boots, routes are registered correctly,
and the meta endpoints return the expected data. No database required.

Phase 0 verification checklist (updated after Phase 3):
  ✓ GET /health → 200
  ✓ GET /api/v1/meta/departments → 200, 9 items, contains "emergency"
  ✓ GET /api/v1/meta/urgency-levels → 200, 3 items, contains "urgent"
  ✓ POST /api/v1/triage/analyze → 422 on empty body (fully implemented)
  ✓ POST /api/v1/intake → 422 on missing required fields (fully implemented)
  ✓ GET /api/v1/intake → 200 (empty list, fully implemented)
  ✓ GET /api/v1/dashboard/summary → 200 (empty counts, fully implemented)
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealth:
    """Health endpoint smoke tests."""

    def test_health_returns_200(self, sync_client: TestClient) -> None:
        """GET /health must return HTTP 200."""
        response = sync_client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, sync_client: TestClient) -> None:
        """GET /health body must contain {"status": "ok"}."""
        response = sync_client.get("/health")
        data = response.json()
        assert data["status"] == "ok"


class TestMetaDepartments:
    """Meta departments endpoint tests."""

    def test_departments_returns_200(self, sync_client: TestClient) -> None:
        response = sync_client.get("/api/v1/meta/departments")
        assert response.status_code == 200

    def test_departments_returns_9_items(self, sync_client: TestClient) -> None:
        """Exactly 9 departments as defined in the design document."""
        response = sync_client.get("/api/v1/meta/departments")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 9, f"Expected 9 departments, got {len(data)}: {data}"

    def test_departments_contains_emergency(self, sync_client: TestClient) -> None:
        """'emergency' is the highest-priority department and must be present."""
        response = sync_client.get("/api/v1/meta/departments")
        data = response.json()
        assert "emergency" in data

    def test_departments_contains_all_expected(self, sync_client: TestClient) -> None:
        """All 9 departments from the design document must be present."""
        expected = {
            "general_medicine",
            "cardiology",
            "neurology",
            "orthopedics",
            "dermatology",
            "ent",
            "pulmonology",
            "gastroenterology",
            "emergency",
        }
        response = sync_client.get("/api/v1/meta/departments")
        data = set(response.json())
        assert data == expected, f"Mismatch: {data.symmetric_difference(expected)}"


class TestMetaUrgencyLevels:
    """Meta urgency levels endpoint tests."""

    def test_urgency_levels_returns_200(self, sync_client: TestClient) -> None:
        response = sync_client.get("/api/v1/meta/urgency-levels")
        assert response.status_code == 200

    def test_urgency_levels_returns_3_items(self, sync_client: TestClient) -> None:
        """Exactly 3 urgency levels: routine, priority, urgent."""
        response = sync_client.get("/api/v1/meta/urgency-levels")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3, f"Expected 3 urgency levels, got {len(data)}: {data}"

    def test_urgency_levels_contains_urgent(self, sync_client: TestClient) -> None:
        response = sync_client.get("/api/v1/meta/urgency-levels")
        data = response.json()
        assert "urgent" in data

    def test_urgency_levels_contains_all_expected(self, sync_client: TestClient) -> None:
        expected = {"routine", "priority", "urgent"}
        response = sync_client.get("/api/v1/meta/urgency-levels")
        data = set(response.json())
        assert data == expected


class TestImplementedRoutes:
    """Verify fully-implemented routes return appropriate status codes."""

    def test_triage_analyze_empty_body_422(self, sync_client: TestClient) -> None:
        """POST /api/v1/triage/analyze with empty body returns 422."""
        response = sync_client.post("/api/v1/triage/analyze", json={"symptoms_text": ""})
        assert response.status_code == 422

    def test_intake_missing_required_fields_422(self, sync_client: TestClient) -> None:
        """POST /api/v1/intake with missing required fields returns 422."""
        response = sync_client.post("/api/v1/intake", json={"name": "Test"})
        assert response.status_code == 422

    def test_intake_get_returns_200(self, sync_client: TestClient) -> None:
        """GET /api/v1/intake returns 200 (empty list)."""
        response = sync_client.get("/api/v1/intake")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_dashboard_summary_returns_200(self, sync_client: TestClient) -> None:
        """GET /api/v1/dashboard/summary returns 200 with empty counts."""
        response = sync_client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert "by_urgency" in data
        assert "by_department" in data

    def test_error_envelope_shape_on_422(self, sync_client: TestClient) -> None:
        """422 responses must return the unified error envelope shape."""
        response = sync_client.post("/api/v1/intake", json={})
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]