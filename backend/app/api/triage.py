"""app/api/triage.py — Triage analyze endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import settings
from app.core.limiter import limiter
from app.schemas.triage import TriageAnalyzeRequest, TriageAnalyzeResponse
from app.services import triage_service

router = APIRouter(prefix="/triage", tags=["triage"])


@router.post(
    "/analyze",
    response_model=TriageAnalyzeResponse,
    summary="Analyze symptoms and return AI triage suggestion",
)
@limiter.limit(settings.triage_rate_limit)
async def analyze_symptoms(
    request: Request,
    body: TriageAnalyzeRequest,
) -> TriageAnalyzeResponse:
    suggestion = await triage_service.analyze(body.symptoms_text)

    if suggestion is None:
        raise HTTPException(
            status_code=503,
            detail="Triage service unavailable. Please select urgency and department manually.",
        )

    return TriageAnalyzeResponse(
        source=suggestion.source,
        urgency=suggestion.urgency,
        department=suggestion.department,
        confidence=suggestion.confidence,
        reasoning=suggestion.reasoning,
    )
