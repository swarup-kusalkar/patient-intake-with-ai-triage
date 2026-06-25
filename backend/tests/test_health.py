"""
tests/test_health.py — Phase 0 smoke tests.

These tests verify the application boots, routes are registered correctly,
and the meta endpoints return the expected data. No database required.

Phase 0 verification checklist (from the detailed breakdown):
  ✓ GET /health → 200
  ✓ GET /api/v1/meta/departments → 200, 9 items, contains "emergency"
  ✓ GET /api/v1/meta/urgency-levels → 200, 3 items, contains "urgent"
  ✓ Stub routes return 501, not 500
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealth:
    """Health endpoint smoke tests."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """GET /health must return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, client: TestClient) -> None:
        """GET /health body must contain {"status": "ok"}."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"


class TestMetaDepartments:
    """Meta departments endpoint tests."""

    def test_departments_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/meta/departments")
        assert response.status_code == 200

    def test_departments_returns_9_items(self, client: TestClient) -> None:
        """Exactly 9 departments as defined in the design document."""
        response = client.get("/api/v1/meta/departments")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 9, f"Expected 9 departments, got {len(data)}: {data}"

    def test_departments_contains_emergency(self, client: TestClient) -> None:
        """'emergency' is the highest-priority department and must be present."""
        response = client.get("/api/v1/meta/departments")
        data = response.json()
        assert "emergency" in data

    def test_departments_contains_all_expected(self, client: TestClient) -> None:
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
        response = client.get("/api/v1/meta/departments")
        data = set(response.json())
        assert data == expected, f"Mismatch: {data.symmetric_difference(expected)}"


class TestMetaUrgencyLevels:
    """Meta urgency levels endpoint tests."""

    def test_urgency_levels_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/meta/urgency-levels")
        assert response.status_code == 200

    def test_urgency_levels_returns_3_items(self, client: TestClient) -> None:
        """Exactly 3 urgency levels: routine, priority, urgent."""
        response = client.get("/api/v1/meta/urgency-levels")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3, f"Expected 3 urgency levels, got {len(data)}: {data}"

    def test_urgency_levels_contains_urgent(self, client: TestClient) -> None:
        response = client.get("/api/v1/meta/urgency-levels")
        data = response.json()
        assert "urgent" in data

    def test_urgency_levels_contains_all_expected(self, client: TestClient) -> None:
        expected = {"routine", "priority", "urgent"}
        response = client.get("/api/v1/meta/urgency-levels")
        data = set(response.json())
        assert data == expected


class TestStubRoutes:
    """Verify stub routes return 501, not 500 (router wiring check)."""

    def test_triage_analyze_returns_501(self, client: TestClient) -> None:
        """POST /api/v1/triage/analyze is a stub — must return 501 Not Implemented."""
        response = client.post("/api/v1/triage/analyze")
        assert response.status_code == 501

    def test_intake_post_returns_501(self, client: TestClient) -> None:
        """POST /api/v1/intake is a stub — must return 501 Not Implemented."""
        response = client.post("/api/v1/intake")
        assert response.status_code == 501

    def test_intake_get_returns_501(self, client: TestClient) -> None:
        """GET /api/v1/intake is a stub — must return 501 Not Implemented."""
        response = client.get("/api/v1/intake")
        assert response.status_code == 501

    def test_dashboard_summary_returns_501(self, client: TestClient) -> None:
        """GET /api/v1/dashboard/summary is a stub — must return 501 Not Implemented."""
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 501

    def test_stub_error_envelope_shape(self, client: TestClient) -> None:
        """Stub routes must return the unified error envelope shape."""
        response = client.post("/api/v1/intake")
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
