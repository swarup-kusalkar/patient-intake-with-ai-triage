"""tests/test_triage_api.py — Phase 3 triage API HTTP tests."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.models.intake import TriageSource
from app.schemas.triage import TriageAnalyzeResponse


class TestAnalyzeEndpoint:
    @pytest.mark.asyncio
    async def test_analyze_rule_engine_fires(self, client, db_session):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            response = await client.post(
                "/api/v1/triage/analyze",
                json={"symptoms_text": "chest pain"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["source"] == "rule_engine"
            assert data["urgency"] == "urgent"
            assert data["department"] == "emergency"
            mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_analyze_llm_suggestion_returned(self, client, db_session):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "urgency": "priority",
                "department": "neurology",
                "confidence": 0.87,
                "reasoning": "recurring headache",
            }
            response = await client.post(
                "/api/v1/triage/analyze",
                json={"symptoms_text": "mild recurring headache"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["source"] == "llm"
            assert data["urgency"] == "priority"
            assert data["department"] == "neurology"
            assert data["confidence"] == 0.87
            assert data["reasoning"] == "recurring headache"

    @pytest.mark.asyncio
    async def test_analyze_llm_failure_returns_503(self, client, db_session):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            mock.return_value = None
            response = await client.post(
                "/api/v1/triage/analyze",
                json={"symptoms_text": "vague feeling"},
            )
            assert response.status_code == 503
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "HTTP_ERROR"
            assert "unavailable" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_analyze_empty_text_422(self, client, db_session):
        response = await client.post(
            "/api/v1/triage/analyze",
            json={"symptoms_text": ""},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_too_short_422(self, client, db_session):
        response = await client.post(
            "/api/v1/triage/analyze",
            json={"symptoms_text": "ok"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_low_confidence_returned(self, client, db_session):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "urgency": "priority",
                "department": "general_medicine",
                "confidence": 0.2,
            }
            response = await client.post(
                "/api/v1/triage/analyze",
                json={"symptoms_text": "not feeling great"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["confidence"] == 0.2

    @pytest.mark.asyncio
    async def test_analyze_no_db_write(self, client, db_session):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "urgency": "routine",
                "department": "general_medicine",
                "confidence": 0.75,
            }
            await client.post(
                "/api/v1/triage/analyze",
                json={"symptoms_text": "mild symptoms"},
            )

        from app.models.intake import IntakeRecord
        from sqlalchemy import select, func
        result = await db_session.execute(select(func.count(IntakeRecord.id)))
        count = result.scalar()
        assert count == 0

    @pytest.mark.asyncio
    async def test_error_envelope_on_503(self, client, db_session):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            mock.return_value = None
            response = await client.post(
                "/api/v1/triage/analyze",
                json={"symptoms_text": "symptoms"},
            )
            assert response.status_code == 503
            data = response.json()
            assert "error" in data
            assert "code" in data["error"]
            assert "message" in data["error"]
            assert data["error"]["field"] is None
