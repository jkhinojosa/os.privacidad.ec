"""
OS Privacidad — API Backend
============================
Entrypoint de la aplicación FastAPI.
Patrón: App Factory para testabilidad.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación (startup/shutdown)."""
    # ── Startup ──────────────────────────────────────────────
    from db.session import engine
    from redis.asyncio import Redis

    # Verificar conexión a PostgreSQL
    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("SELECT 1")
        )

    # Verificar conexión a Redis
    redis = Redis.from_url(str(settings.REDIS_URL))
    await redis.ping()
    app.state.redis = redis

    yield

    # ── Shutdown ─────────────────────────────────────────────
    await app.state.redis.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    """Factory de la aplicación FastAPI."""
    app = FastAPI(
        title="OS Privacidad API",
        description="Sistema Operativo de Privacidad y Protección de Datos Personales",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────
    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """Registra todos los routers de la API."""
    from routers.health import router as health_router

    app.include_router(health_router, prefix="/api/v1")


# Instancia global para uvicorn
app = create_app()
