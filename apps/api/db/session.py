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

from core.config import settings

# ── Engine ───────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.is_development,  # SQL logging solo en dev
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,            # Detecta conexiones rotas
    pool_recycle=3600,             # Recicla conexiones cada hora
)

# ── Session Factory ──────────────────────────────────────────
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


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
