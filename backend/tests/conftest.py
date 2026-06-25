"""
tests/conftest.py — Shared pytest fixtures.

Phase 0: Provides a synchronous TestClient for smoke tests.
Later phases will add async database fixtures and mocked LLM client.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    FastAPI TestClient — synchronous, uses ASGI transport.
    scope="module" so the app is created once per test module.
    """
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
