"""
app/schemas/dashboard.py — Dashboard summary schema.
STUB: Full implementation in Phase 2/4.
"""
from __future__ import annotations

from typing import Dict
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """Response for GET /api/v1/dashboard/summary."""
    total: int
    by_urgency: Dict[str, int]
    by_department: Dict[str, int]
    override_rate: float
