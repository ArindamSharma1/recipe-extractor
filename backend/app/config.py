"""Application configuration via pydantic-settings.

All settings are loaded from environment variables or a .env file.
Secrets (API keys, DB credentials) are never hardcoded.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized, validated application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────────────
    database_url: str

    # ── Google Gemini ─────────────────────────────────────────────────
    gemini_api_key: str = ""

    # ── CORS ──────────────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:5173"

    # ── Rate Limiting ─────────────────────────────────────────────────
    rate_limit: str = "10/minute"

    # ── Scraper ───────────────────────────────────────────────────────
    scraper_timeout_seconds: int = 10
    scraper_max_content_length: int = 50_000
    scraper_user_agent: str = "RecipeExtractor/1.0 (+https://github.com/recipe-extractor)"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated allowed origins into a list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


# Singleton — import this everywhere
settings = Settings()
