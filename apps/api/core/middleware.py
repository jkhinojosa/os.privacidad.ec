"""
OS Privacidad — Middleware de Tenant (RLS)
============================================
Stub para Fase 0 — se implementa completamente en Fase 1.

En Fase 1:
1. Extrae tenant_id del JWT en cada request
2. Ejecuta SET app.tenant_id = '<uuid>' en la conexión PostgreSQL
3. RLS policies filtran automáticamente por tenant
"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("os_privacidad.middleware.tenant")

# Rutas que no requieren tenant context
TENANT_EXEMPT_PATHS = {
    "/api/v1/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware que establece el contexto de tenant en cada request.

    Fase 0: Solo logging — no aplica RLS aún.
    Fase 1: Extrae tenant_id del JWT → SET app.tenant_id en PostgreSQL.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # Rutas exentas de tenant context
        if path in TENANT_EXEMPT_PATHS or not path.startswith("/api/"):
            return await call_next(request)

        # TODO (Fase 1): Extraer tenant_id del JWT
        # TODO (Fase 1): Setear app.tenant_id en la sesión de BD
        logger.debug("Tenant middleware: request a %s (tenant context pendiente Fase 1)", path)

        return await call_next(request)
