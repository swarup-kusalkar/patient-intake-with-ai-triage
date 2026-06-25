"""tests/test_rule_engine.py — Phase 11.1 Rule Engine Unit Tests.

Every red-flag keyword fires the rule engine → urgent/emergency.
Non-matching text passes through to LLM (returns None from rule engine).
Case-insensitive matching.
Partial match within longer text.

LLM is never called in these tests — purely unit-testing the rule engine.
"""
from __future__ import annotations

import pytest

from app.models.intake import Department, TriageSource, UrgencyLevel
from app.services.triage_service import _rule_engine_check


class TestRuleEngineKeywords:
    """Every red-flag keyword maps to urgent/emergency."""

    def test_chest_pain(self):
        result = _rule_engine_check("chest pain")
        assert result is not None
        assert result.source == TriageSource.rule_engine
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_chest_tightness(self):
        result = _rule_engine_check("chest tightness")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_cant_breathe(self):
        result = _rule_engine_check("I can't breathe")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_cannot_breathe(self):
        result = _rule_engine_check("cannot breathe properly")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_shortness_of_breath(self):
        result = _rule_engine_check("shortness of breath for 3 days")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_difficulty_breathing(self):
        result = _rule_engine_check("difficulty breathing")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_severe_bleeding(self):
        result = _rule_engine_check("severe bleeding from wound")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_loss_of_consciousness(self):
        result = _rule_engine_check("loss of consciousness")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_unconscious(self):
        result = _rule_engine_check("found unconscious")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_unresponsive(self):
        result = _rule_engine_check("patient is unresponsive")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_stroke(self):
        result = _rule_engine_check("suspected stroke")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_seizure(self):
        result = _rule_engine_check("seizure")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_heart_attack(self):
        result = _rule_engine_check("heart attack symptoms")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_cardiac_arrest(self):
        result = _rule_engine_check("cardiac arrest")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_severe_chest(self):
        result = _rule_engine_check("severe chest pain")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_overdose(self):
        result = _rule_engine_check("drug overdose")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_anaphylaxis(self):
        result = _rule_engine_check("anaphylaxis reaction")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency

    def test_allergic_reaction_severe(self):
        result = _rule_engine_check("allergic reaction severe")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent
        assert result.department == Department.emergency


class TestRuleEngineNoMatch:
    """Non-matching text returns None — passes through to LLM path."""

    def test_mild_headache(self):
        result = _rule_engine_check("mild headache")
        assert result is None

    def test_common_cold(self):
        result = _rule_engine_check("common cold symptoms")
        assert result is None

    def test_small_cut(self):
        result = _rule_engine_check("small cut on finger")
        assert result is None

    def test_vague_symptoms(self):
        result = _rule_engine_check("not feeling well for a few days")
        assert result is None

    def test_skin_rash_mild(self):
        result = _rule_engine_check("mild skin rash")
        assert result is None


class TestRuleEngineCaseInsensitive:
    """Matching is case-insensitive."""

    def test_uppercase(self):
        result = _rule_engine_check("CHEST PAIN")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent

    def test_mixed_case(self):
        result = _rule_engine_check("Chest Pain")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent

    def test_lowercase(self):
        result = _rule_engine_check("seizure")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent


class TestRuleEnginePartialMatch:
    """Keyword matched as substring within longer text."""

    def test_chest_pain_in_sentence(self):
        result = _rule_engine_check("Patient reports severe chest pain radiating to left arm")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent

    def test_seizure_in_sentence(self):
        result = _rule_engine_check("She had a seizure this morning at 9am")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent

    def test_stroke_in_sentence(self):
        result = _rule_engine_check("Doctor suspects possible stroke — CT scan ordered")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent

    def test_shortness_in_sentence(self):
        result = _rule_engine_check("Patient complains of shortness of breath and dizziness")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent

    def test_unconscious_in_sentence(self):
        result = _rule_engine_check("Found unconscious behind the wheel")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent

    def test_keyword_at_start(self):
        result = _rule_engine_check("Chest pain started suddenly")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent

    def test_keyword_at_end(self):
        result = _rule_engine_check("Patient has been diagnosed with seizure")
        assert result is not None
        assert result.urgency == UrgencyLevel.urgent


class TestRuleEngineConfidence:
    """Rule engine always returns confidence=None (deterministic)."""

    @pytest.mark.parametrize("keyword", [
        "chest pain",
        "seizure",
        "can't breathe",
        "stroke",
        "severe bleeding",
    ])
    def test_confidence_is_none(self, keyword):
        result = _rule_engine_check(keyword)
        assert result is not None
        assert result.confidence is None
        assert result.reasoning is None

    @pytest.mark.parametrize("keyword", [
        "mild headache",
        "common cold",
        "skin rash",
    ])
    def test_no_match_confidence_is_none(self, keyword):
        result = _rule_engine_check(keyword)
        assert result is None
