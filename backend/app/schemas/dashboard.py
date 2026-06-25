"""
app/schemas/dashboard.py — Dashboard summary schema.
"""
from __future__ import annotations

from pydantic import BaseModel


class UrgencyBreakdown(BaseModel):
    routine: int = 0
    priority: int = 0
    urgent: int = 0


class DepartmentBreakdown(BaseModel):
    general_medicine: int = 0
    cardiology: int = 0
    neurology: int = 0
    orthopedics: int = 0
    dermatology: int = 0
    ent: int = 0
    pulmonology: int = 0
    gastroenterology: int = 0
    emergency: int = 0


class DashboardSummary(BaseModel):
    """Response for GET /api/v1/dashboard/summary."""
    date: str
    total: int
    by_urgency: UrgencyBreakdown
    by_department: DepartmentBreakdown
    override_rate: float | None