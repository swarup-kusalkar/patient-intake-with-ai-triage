"""app/services/triage_service.py — AI Triage Service.

Full pipeline (Phase 3): rule engine -> LLM -> validation -> retry -> fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models.intake import Department, TriageSource, UrgencyLevel

RED_FLAG_KEYWORDS: dict[str, tuple[str, str]] = {
    "chest pain": ("urgent", "emergency"),
    "chest tightness": ("urgent", "emergency"),
    "can't breathe": ("urgent", "emergency"),
    "cannot breathe": ("urgent", "emergency"),
    "shortness of breath": ("urgent", "emergency"),
    "difficulty breathing": ("urgent", "emergency"),
    "severe bleeding": ("urgent", "emergency"),
    "loss of consciousness": ("urgent", "emergency"),
    "unconscious": ("urgent", "emergency"),
    "unresponsive": ("urgent", "emergency"),
    "stroke": ("urgent", "emergency"),
    "seizure": ("urgent", "emergency"),
    "heart attack": ("urgent", "emergency"),
    "cardiac arrest": ("urgent", "emergency"),
    "severe chest": ("urgent", "emergency"),
    "overdose": ("urgent", "emergency"),
    "anaphylaxis": ("urgent", "emergency"),
    "allergic reaction severe": ("urgent", "emergency"),
}

ALLOWED_DEPARTMENTS: frozenset[str] = frozenset(d.value for d in Department)
ALLOWED_URGENCY: frozenset[str] = frozenset(u.value for u in UrgencyLevel)


@dataclass
class TriageSuggestion:
    source: TriageSource
    urgency: UrgencyLevel
    department: Department
    confidence: Optional[float] = None
    reasoning: Optional[str] = None


def _rule_engine_check(symptoms_text: str) -> Optional[TriageSuggestion]:
    """Case-insensitive substring match. Returns immediately on first match."""
    text_lower = symptoms_text.lower()
    for keyword, (urgency, department) in RED_FLAG_KEYWORDS.items():
        if keyword in text_lower:
            return TriageSuggestion(
                source=TriageSource.rule_engine,
                urgency=UrgencyLevel(urgency),
                department=Department(department),
                confidence=None,
                reasoning=None,
            )
    return None


def validate_llm_output(raw: dict) -> Optional[TriageSuggestion]:
    """
    Validate LLM JSON output against allowed enums and clamp confidence to [0, 1].

    Layer 3 of four-layer validation (Section 6.3): application-level enum check.
    """
    try:
        urgency_str = raw.get("urgency")
        department_str = raw.get("department")
        confidence = raw.get("confidence")
        reasoning = raw.get("reasoning")

        if urgency_str not in ALLOWED_URGENCY:
            return None
        if department_str not in ALLOWED_DEPARTMENTS:
            return None

        if confidence is not None:
            try:
                confidence = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                confidence = 0.0

        return TriageSuggestion(
            source=TriageSource.llm,
            urgency=UrgencyLevel(urgency_str),
            department=Department(department_str),
            confidence=confidence,
            reasoning=reasoning,
        )
    except (TypeError, ValueError, KeyError):
        return None


async def analyze(symptoms_text: str) -> Optional[TriageSuggestion]:
    """
    Full triage pipeline (Section 6):

    1. Rule engine check - fires immediately for red-flag keywords (no LLM call)
    2. LLM call with structured JSON output - one retry on invalid output
    3. Return None on persistent failure - caller shows manual dropdowns

    The call_llm import is inside this function so that tests can patch
    app.services.triage_service.call_llm cleanly.
    """
    from app.services.llm_client import call_llm

    result = _rule_engine_check(symptoms_text)
    if result is not None:
        return result

    for attempt in range(2):
        raw = await call_llm(symptoms_text)

        if raw is None:
            break  # network/timeout - no point retrying

        suggestion = validate_llm_output(raw)
        if suggestion is not None:
            return suggestion

    return None
