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
    from redis.asyncio import Redis

    from db.session import engine

    # Verificar conexión a PostgreSQL
    async with engine.begin() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))

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

    # ── Exception Handlers (Standard Error Format) ────────────
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Datos de entrada inválidos",
                    "details": exc.errors(),
                }
            },
        )

    # ── Routers ──────────────────────────────────────────────
    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """Registra todos los routers de la API."""
    from routers.auth import router as auth_router
    from routers.casos import router as casos_router
    from routers.clientes import router as clientes_router
    from routers.eipds import router as eipds_router
    from routers.expedientes import router as expedientes_router
    from routers.health import router as health_router
    from routers.medidas_seguridad import router as medidas_seguridad_router
    from routers.procesos import router as procesos_router
    from routers.riesgos import router as riesgos_router
    from routers.solicitudes_derechos import router as solicitudes_derechos_router
    from routers.tenants import router as tenants_router
    from routers.usuarios import router as usuarios_router

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(tenants_router, prefix="/api/v1")
    app.include_router(clientes_router, prefix="/api/v1")
    app.include_router(usuarios_router, prefix="/api/v1")
    app.include_router(procesos_router, prefix="/api/v1")
    app.include_router(casos_router, prefix="/api/v1")
    app.include_router(expedientes_router, prefix="/api/v1")
    app.include_router(medidas_seguridad_router, prefix="/api/v1")
    app.include_router(riesgos_router, prefix="/api/v1")
    app.include_router(eipds_router, prefix="/api/v1")
    app.include_router(solicitudes_derechos_router, prefix="/api/v1")


# Instancia global para uvicorn
app = create_app()
