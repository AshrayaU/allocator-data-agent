from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    APP_SECRET: str
    SERVER_TYPE: str
    ALLOCATOR_API_BASE: str = "https://secure.allocator.com/admin/api"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"

    # Allocator Admin API (HTTP Basic auth) — used only by
    # app/services/allocator_admin_service.py, imported only by
    # app/services/data_sync.py. Never read by the chat/LLM path.
    ALLOCATOR_ADMIN_SECRET_KEY: str = ""
    ALLOCATOR_ADMIN_AUTH_TOKEN: str = ""

    # Anthropic / Claude API (chat Q&A over the local cache)
    ANTHROPIC_API_KEY: str = ""
    SUMMARY_MODEL: str = "claude-sonnet-5"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        """
        Rewrite Heroku's postgres:// to postgresql+psycopg://, and append
        sslmode=require for non-localhost connections.
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://") and "+psycopg" not in url:
            url = "postgresql+psycopg://" + url[len("postgresql://"):]

        is_localhost = "localhost" in url or "127.0.0.1" in url
        if not is_localhost and "sslmode" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"

        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
