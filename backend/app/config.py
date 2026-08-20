"""
GovGuide AI — Backend Application Configuration
Uses pydantic-settings for type-safe environment variable loading.
All secrets are sourced from environment variables / .env file.
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Central application configuration.
    Values are loaded from environment variables or a .env file.
    No secrets are hard-coded.
    """

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8-sig",  # handles BOM from Windows editors
        case_sensitive=False,
        extra="ignore",                 # ignore VITE_* and other unknown vars
    )

    # ── Application ───────────────────────────────────────────
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str  # async driver: postgresql+asyncpg://...
    DATABASE_SYNC_URL: str  # sync driver for Alembic: postgresql://...

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ──────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # ── Rate Limiting ─────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_QUERY_PER_MINUTE: int = 10

    # ── LLM (Phase 2 — stubs in Phase 1) ─────────────────────
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""
    LLM_MAX_TOKENS: int = 800
    LLM_TEMPERATURE: float = 0.1

    # ── Embedding (awaiting model selection) ─────────────────
    EMBEDDING_MODEL: str = ""
    EMBEDDING_DIMENSION: int = 0  # 0 = not yet configured

    @field_validator("EMBEDDING_DIMENSION", mode="before")
    @classmethod
    def parse_embedding_dimension(cls, v):
        if v is None or v == "":
            return 0
        return int(v)

    # ── Retrieval ─────────────────────────────────────────────
    RETRIEVAL_MODE: str = "hybrid"
    RETRIEVAL_TOP_K: int = 10
    RRF_K: int = 60
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    RETRIEVAL_CONFIDENCE_THRESHOLD: float = 0.15

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"


def get_settings() -> Settings:
    """Factory function — returns cached settings instance."""
    return _settings


# Module-level singleton (loaded once at startup)
_settings = Settings()
