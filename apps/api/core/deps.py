"""
OS Privacidad — Dependencias de Inyección (FastAPI)
===================================================
Manejo de Autenticación, RBAC y Contexto Multi-Tenant con RLS.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Callable
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decode_token
from db.session import async_session_maker
from models.audit_log import AuditLog
from models.usuario import UserRole, Usuario

security_scheme = HTTPBearer(auto_error=False)


# ── Inyección de Sesión de Base de Datos ────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Generador de sesión SQLAlchemy asíncrona estándar."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# ── Extracción y Validación de Usuario Actual ───────────────
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """
    Extrae el token JWT del header Authorization (Bearer) o de cookies,
    lo valida y recupera el usuario correspondiente desde la BD.
    """
    token: str | None = None
    if credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "No autenticado"}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
        user_id_str: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if not user_id_str or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "INVALID_TOKEN", "message": "Token inválido o expirado"}},
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Token inválido o expirado"}},
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    stmt = select(Usuario).where(Usuario.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"}},
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "USER_INACTIVE", "message": "Cuenta de usuario desactivada"}},
        )

    return user


# ── RBAC: Verificación de Roles ──────────────────────────────
def require_role(*allowed_roles: UserRole) -> Callable:
    """
    Dependency factory para verificar que el usuario posea uno de los roles permitidos.
    El rol 'super_admin' tiene acceso por defecto a todos los endpoints excepto si se restringe.
    """

    async def role_checker(
        current_user: Usuario = Depends(get_current_user),
    ) -> Usuario:
        if current_user.rol == UserRole.super_admin or current_user.rol in allowed_roles:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": f"Rol '{current_user.rol.value}' no tiene permisos para esta acción",
                }
            },
        )

    return role_checker


# ── RLS: Sesión de BD con Tenant Context ──────────────────────
async def get_tenant_db(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """
    Configura la variable de sesión 'app.tenant_id' en PostgreSQL
    para que las políticas de RLS filtren los datos automáticamente por tenant.
    """
    if current_user.tenant_id is not None:
        await db.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(current_user.tenant_id)},
        )
    elif current_user.rol == UserRole.super_admin:
        # SuperAdmin puede operar sin filtro de tenant
        await db.execute(text("SELECT set_config('app.tenant_id', '', true)"))

    return db


# ── Helper de Auditoría ──────────────────────────────────────
async def log_audit(
    db: AsyncSession,
    accion: str,
    entidad: str,
    entidad_id: uuid.UUID | None = None,
    usuario: Usuario | None = None,
    detalles: dict[str, Any] | None = None,
    request: Request | None = None,
    tenant_id: uuid.UUID | None = None,
) -> AuditLog:
    """
    Registra una entrada en la tabla audit_logs dentro de la transacción actual.
    """
    ip_address = None
    if request and request.client:
        ip_address = request.client.host

    t_id = tenant_id or (usuario.tenant_id if usuario else None)
    u_id = usuario.id if usuario else None

    audit_entry = AuditLog(
        tenant_id=t_id,
        usuario_id=u_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        detalles=detalles,
        ip_address=ip_address,
    )
    db.add(audit_entry)
    return audit_entry
