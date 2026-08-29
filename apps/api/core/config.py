"""
OS Privacidad — Configuración Central
=======================================
Usa Pydantic BaseSettings para cargar variables de entorno
con validación de tipos y valores por defecto seguros.
"""

from __future__ import annotations

import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── PostgreSQL ───────────────────────────────────────────
    POSTGRES_USER: str = "osprivacidad"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "osprivacidad"
    DATABASE_URL: str = "postgresql+asyncpg://osprivacidad:changeme@db:5432/osprivacidad"

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Auth (JWT) ───────────────────────────────────────────
    JWT_SECRET: str = "changeme-generate-a-strong-secret-at-least-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # ── API ──────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_ENV: str = "development"
    API_DEBUG: bool = True
    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost"]'

    # ── Microsoft Graph ──────────────────────────────────────
    MS_GRAPH_CLIENT_ID: str = ""
    MS_GRAPH_CLIENT_SECRET: str = ""
    MS_GRAPH_TENANT_ID: str = ""

    # ── Proveedores de IA (todos opcionales) ─────────────────
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """Parsea CORS_ORIGINS de string JSON a lista."""
        try:
            origins = json.loads(self.CORS_ORIGINS)
            if isinstance(origins, list):
                return origins
        except (json.JSONDecodeError, TypeError):
            pass
        return ["http://localhost:3000"]

    @property
    def is_development(self) -> bool:
        return self.API_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.API_ENV == "production"

    @field_validator("JWT_SECRET")
    @classmethod
    def jwt_secret_must_be_strong(cls, v: str) -> str:
        """Valida que el JWT_SECRET tenga longitud mínima segura."""
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET debe tener al menos 32 caracteres. "
                'Genera uno con: python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        return v


# Singleton — importar desde aquí
settings = Settings()
