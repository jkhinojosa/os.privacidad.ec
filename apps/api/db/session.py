"""
OS Privacidad — Sesión de Base de Datos (Async)
=================================================
Configura el engine async y session factory para PostgreSQL + asyncpg.
Provee dependency injection para FastAPI routes.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.config import settings

# ── Engine ───────────────────────────────────────────────────
engine_kwargs = {
    "echo": settings.is_development,
    "pool_pre_ping": True,
}

if settings.API_ENV == "testing":
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 10
    engine_kwargs["pool_recycle"] = 3600

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# ── Session Factory ──────────────────────────────────────────
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
async_session_maker = async_session_factory


# ── Dependency Injection ─────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency de FastAPI que provee una sesión de BD.

    Uso:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...

    En Fase 1, este dependency también seteará app.tenant_id
    en la sesión de PostgreSQL para RLS.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
