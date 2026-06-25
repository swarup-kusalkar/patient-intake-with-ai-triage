"""
app/core/config.py — Application settings via Pydantic Settings.

Loads from environment variables / .env file.
Uses @lru_cache so settings are read once at startup, not on every import.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@postgres:5432/patient_intake"
    )

    # ------------------------------------------------------------------
    # LLM / OpenAI
    # ------------------------------------------------------------------
    llm_api_key: str = "sk-placeholder"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 15
    llm_max_tokens: int = 150

    # ------------------------------------------------------------------
    # CORS — comma-separated string in .env → parsed to list at startup
    # Never use * in production; always an explicit allow-list (Section 10).
    # ------------------------------------------------------------------
    cors_origins_raw: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    # ------------------------------------------------------------------
    # Rate limiting (slowapi format, e.g. "10/minute")
    # ------------------------------------------------------------------
    triage_rate_limit: str = "10/minute"

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton — loaded once at startup."""
    return Settings()


# Convenience alias used throughout the app
settings = get_settings()
