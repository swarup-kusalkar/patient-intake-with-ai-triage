"""
app/services/triage_service.py — AI Triage Service.

STUB: Rule engine skeleton only. Full pipeline (LLM call, validation,
retry, fallback) implemented in Phase 3.

Architecture: This is an internal service module, not inline route logic.
It has its own failure modes (LLM timeout, malformed JSON, rate limiting)
that are unrelated to "save a patient record." Isolating it lets the
route handler treat it as a plain typed function call — no exceptions
about external APIs ever expected to bubble up.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models.intake import Department, TriageSource, UrgencyLevel

# ---------------------------------------------------------------------------
# Red-flag keyword map: keyword → (urgency, department)
#
# These are hand-maintained, deterministic, and trusted without further
# validation — you wrote the keyword map, its output space is fully under
# your control by construction.
#
# Key design principle: the rule engine runs BEFORE the LLM, not after.
# For cases where being wrong matters most (cardiac arrest, stroke, etc.),
# we don't want to depend on a probabilistic model at all.
#
# Honest caveat: this list is not exhaustive. The override log (Phase 4)
# is the data that would surface missing terms over time.
# ---------------------------------------------------------------------------
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

# Pre-computed sets for O(1) membership checks at validate time
ALLOWED_DEPARTMENTS: frozenset[str] = frozenset(d.value for d in Department)
ALLOWED_URGENCY: frozenset[str] = frozenset(u.value for u in UrgencyLevel)


@dataclass
class TriageSuggestion:
    """
    Result of a triage analysis — returned by the service, never persisted
    until the receptionist confirms Save.
    """
    source: TriageSource
    urgency: UrgencyLevel
    department: Department
    confidence: Optional[float] = None
    reasoning: Optional[str] = None


def _rule_engine_check(symptoms_text: str) -> Optional[TriageSuggestion]:
    """
    Check symptoms text against red-flag keywords.

    Case-insensitive substring match. Returns a TriageSuggestion immediately
    on first match, skipping the LLM entirely.

    Returns None if no red-flag keywords are found — caller proceeds to LLM.
    """
    text_lower = symptoms_text.lower()
    for keyword, (urgency, department) in RED_FLAG_KEYWORDS.items():
        if keyword in text_lower:
            return TriageSuggestion(
                source=TriageSource.rule_engine,
                urgency=UrgencyLevel(urgency),
                department=Department(department),
                confidence=None,   # Rule engine: deterministic, not probabilistic
                reasoning=None,    # No reasoning needed — keyword is self-evident
            )
    return None


async def analyze(symptoms_text: str) -> Optional[TriageSuggestion]:
    """
    STUB: Full pipeline will be implemented in Phase 3.

    Phase 0: Rule engine skeleton only — LLM path not yet wired.

    Full pipeline (Phase 3):
      1. Rule engine check → return immediately if red-flag match
      2. LLM call (structured JSON schema output)
      3. Validate output (membership check + confidence clamp)
      4. Retry once on invalid output
      5. Return None (fallback to manual) on persistent failure

    Returns:
        TriageSuggestion if analysis succeeded (either path)
        None if analysis failed — caller shows manual dropdowns
    """
    # Step 1: Rule engine — always runs first, even in Phase 0
    result = _rule_engine_check(symptoms_text)
    if result:
        return result

    # Phase 3: LLM call + validation + retry + fallback will go here
    # For now, return None so the caller falls back to manual entry
    return None
