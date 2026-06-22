"""
backend/config.py — Pydantic-settings configuration loader for LoanGuard AI.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: Literal["development", "staging", "production"] = "development"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:3001"

    # Rate limiting
    rate_limit: str = "10/minute"

    # Validation limits
    max_file_size_mb: int = 5
    max_text_length: int = 50_000
    min_word_count: int = 50

    # Supabase (stub)
    supabase_url: str = ""
    supabase_key: str = ""

    # Logging
    log_level: str = "INFO"

    # Model paths
    model_path: str = "ml/model.pkl"
    keywords_config_path: str = "ml/keywords_config.json"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return v.upper()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
