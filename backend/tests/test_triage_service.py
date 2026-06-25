"""tests/test_triage_service.py — Phase 3 triage service tests.

All LLM calls are mocked — zero real API calls.
Tests verify: rule engine, LLM wiring, validation, retry, fallback.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.models.intake import Department, TriageSource, UrgencyLevel
from app.services.triage_service import (
    _rule_engine_check,
    analyze,
    validate_llm_output,
)


class TestRuleEngine:
    def test_chest_pain_returns_urgent_emergency(self):
        result = _rule_engine_check("chest pain")
        assert result is not None
        assert result.source == TriageSource.rule_engine
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_seizure_returns_urgent_emergency(self):
        result = _rule_engine_check(" seizure ")
        assert result is not None
        assert result.source == TriageSource.rule_engine
        assert result.urgency == UrgencyLevel.urgent

    def test_no_match_returns_none(self):
        result = _rule_engine_check("mild headache")
        assert result is None

    def test_case_insensitive(self):
        result = _rule_engine_check("CHEST PAIN")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent

    def test_no_llm_call_on_rule_match(self):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            result = _rule_engine_check("chest pain")
            assert result is not None
            mock.assert_not_called()


class TestValidateLLMOutput:
    def test_valid_output_returns_suggestion(self):
        raw = {"urgency": "priority", "department": "cardiology", "confidence": 0.85, "reasoning": "palpitations"}
        result = validate_llm_output(raw)
        assert result is not None
        assert result.source == TriageSource.llm
        assert result.urgency == UrgencyLevel.priority
        assert result.department == Department.cardiology
        assert result.confidence == 0.85
        assert result.reasoning == "palpitations"

    def test_invalid_urgency_returns_none(self):
        raw = {"urgency": "super_urgent", "department": "cardiology", "confidence": 0.9}
        assert validate_llm_output(raw) is None

    def test_invalid_department_returns_none(self):
        raw = {"urgency": "routine", "department": "cardio", "confidence": 0.9}
        assert validate_llm_output(raw) is None

    def test_missing_urgency_returns_none(self):
        raw = {"department": "cardiology", "confidence": 0.9}
        assert validate_llm_output(raw) is None

    def test_missing_department_returns_none(self):
        raw = {"urgency": "priority", "confidence": 0.9}
        assert validate_llm_output(raw) is None

    def test_confidence_clamped_to_1(self):
        raw = {"urgency": "routine", "department": "general_medicine", "confidence": 1.5}
        result = validate_llm_output(raw)
        assert result is not None
        assert result.confidence == 1.0

    def test_confidence_clamped_to_0(self):
        raw = {"urgency": "routine", "department": "general_medicine", "confidence": -0.1}
        result = validate_llm_output(raw)
        assert result is not None
        assert result.confidence == 0.0

    def test_missing_confidence_ok(self):
        raw = {"urgency": "routine", "department": "general_medicine"}
        result = validate_llm_output(raw)
        assert result is not None
        assert result.confidence is None

    def test_missing_reasoning_ok(self):
        raw = {"urgency": "urgent", "department": "emergency", "confidence": 0.9}
        result = validate_llm_output(raw)
        assert result is not None
        assert result.reasoning is None


class TestAnalyze:
    @pytest.mark.asyncio
    async def test_rule_engine_short_circuits_llm(self):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            result = await analyze("chest pain")
            assert result is not None
            assert result.source == TriageSource.rule_engine
            mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_llm_valid_response_returned(self):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            mock.return_value = {"urgency": "priority", "department": "neurology", "confidence": 0.85}
            result = await analyze("mild headache")
            assert result is not None
            assert result.source == TriageSource.llm
            assert result.urgency == UrgencyLevel.priority
            assert result.department == Department.neurology

    @pytest.mark.asyncio
    async def test_llm_timeout_returns_none(self):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            mock.return_value = None
            result = await analyze("mild headache")
            assert result is None

    @pytest.mark.asyncio
    async def test_llm_malformed_json_returns_none(self):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            mock.return_value = {"urgency": "invalid"}
            result = await analyze("mild headache")
            assert result is None

    @pytest.mark.asyncio
    async def test_llm_invalid_urgency_retries_then_fails(self):
        call_count = 0
        async def _mock(symptoms_text):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"urgency": "super_urgent", "department": "general_medicine", "confidence": 0.9}
            return {"urgency": "invalid", "department": "general_medicine", "confidence": 0.9}

        with patch("app.services.llm_client.call_llm", side_effect=_mock):
            result = await analyze("vague symptoms")
            assert result is None

    @pytest.mark.asyncio
    async def test_llm_retry_succeeds_on_second_attempt(self):
        call_count = 0
        async def _mock(symptoms_text):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"urgency": "bad_enum", "department": "general_medicine", "confidence": 0.9}
            return {"urgency": "routine", "department": "dermatology", "confidence": 0.75}

        with patch("app.services.llm_client.call_llm", side_effect=_mock):
            result = await analyze("skin rash")
            assert result is not None
            assert result.urgency == UrgencyLevel.routine
            assert result.department == Department.dermatology
            assert result.confidence == 0.75

    @pytest.mark.asyncio
    async def test_vague_symptoms_pass_through_to_llm(self):
        with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
            mock.return_value = {"urgency": "priority", "department": "general_medicine", "confidence": 0.6}
            result = await analyze("not feeling well")
            assert result is not None
            assert result.source == TriageSource.llm
            mock.assert_called_once()
