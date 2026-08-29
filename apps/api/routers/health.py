"""
OS Privacidad — Health Check Router
=====================================
Endpoint /api/v1/health para verificar que la API,
la base de datos y Redis están operativos.
"""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text

from db.session import async_session_factory

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Esquema de respuesta del health check."""

    status: str
    db: str
    redis: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Verifica el estado de la API, PostgreSQL y Redis.",
)
async def health_check() -> HealthResponse:
    """
    Endpoint de health check que verifica:
    1. PostgreSQL: ejecuta SELECT 1
    2. Redis: ejecuta PING

    Retorna 200 si todo está operativo.
    """
    # ── Verificar PostgreSQL ─────────────────────────────────
    db_status = "disconnected"
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        db_status = "error"

    # ── Verificar Redis ──────────────────────────────────────
    redis_status = "disconnected"
    try:
        from redis.asyncio import Redis

        from core.config import settings

        redis = Redis.from_url(str(settings.REDIS_URL))
        await redis.ping()
        redis_status = "connected"
        await redis.aclose()
    except Exception:
        redis_status = "error"

    # ── Determinar estado global ─────────────────────────────
    overall = "ok" if db_status == "connected" and redis_status == "connected" else "degraded"

    return HealthResponse(status=overall, db=db_status, redis=redis_status)
