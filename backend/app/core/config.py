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
    # LLM — Hybrid: Groq (primary) + Google Gemini Flash (fallback)
    # ------------------------------------------------------------------
    # Primary provider: "groq" or "gemini"
    # Recommended: Use Groq as primary (fastest, 30 RPM free), Gemini as fallback
    llm_primary_provider: str = "groq"
    
    # Groq settings (primary — fastest inference)
    groq_api_key: str = "your-groq-api-key-here"
    groq_model: str = "llama-3.1-70b-versatile"  # or "llama-3.2-3b-preview" for speed
    groq_timeout_seconds: int = 15
    groq_max_tokens: int = 150
    
    # Google Gemini Flash settings (fallback)
    gemini_api_key: str = "your-gemini-api-key-here"
    gemini_model: str = "gemini-2.0-flash-exp"  # or "gemini-1.5-flash" for stability
    gemini_max_tokens: int = 150
    
    # Legacy aliases for backward compatibility
    llm_api_key: str = "your-groq-api-key-here"
    llm_model: str = "llama-3.1-70b-versatile"
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
