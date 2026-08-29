"""
OS Privacidad — Router de Usuarios
==================================
Endpoints CRUD para gestión de usuarios dentro del tenant, con control de roles y prevención de escalamiento de privilegios.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_tenant_db, log_audit, require_role
from core.security import hash_password
from models.usuario import UserRole, Usuario
from schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("", response_model=list[UsuarioResponse])
async def list_usuarios(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo)
    ),
) -> list[UsuarioResponse]:
    """
    Lista todos los usuarios del tenant actual.
    """
    stmt = select(Usuario).order_by(Usuario.nombre.asc(), Usuario.apellido.asc())
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Usuario.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    usuarios = result.scalars().all()
    return [UsuarioResponse.model_validate(u) for u in usuarios]


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    payload: UsuarioCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin)
    ),
) -> UsuarioResponse:
    """
    Crea un nuevo usuario en el tenant.
    Valida que no haya escalamiento de privilegios (TenantAdmin no puede crear SuperAdmin).
    """
    # Prevención de escalamiento de privilegios
    if payload.rol == UserRole.super_admin and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN_ROLE", "message": "Solo un SuperAdmin puede asignar el rol super_admin"}},
        )

    tenant_id = current_user.tenant_id

    # Verificar si el email ya existe para este tenant
    stmt = select(Usuario).where(Usuario.tenant_id == tenant_id, Usuario.email == payload.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "EMAIL_EXISTS", "message": f"El email '{payload.email}' ya está registrado en este tenant"}},
        )

    usuario = Usuario(
        tenant_id=tenant_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        nombre=payload.nombre,
        apellido=payload.apellido,
        rol=payload.rol,
        cliente_id=payload.cliente_id,
        created_by=current_user.id,
    )
    db.add(usuario)
    await db.flush()

    # Auditoría
    await log_audit(
        db=db,
        accion="CREATE",
        entidad="usuario",
        entidad_id=usuario.id,
        usuario=current_user,
        detalles={"email": usuario.email, "rol": usuario.rol.value},
        request=request,
    )
    await db.commit()
    await db.refresh(usuario)

    return UsuarioResponse.model_validate(usuario)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(
    usuario_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo)
    ),
) -> UsuarioResponse:
    """
    Obtiene los detalles de un usuario específico.
    """
    stmt = select(Usuario).where(Usuario.id == usuario_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Usuario.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    usuario = result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"}},
        )

    return UsuarioResponse.model_validate(usuario)


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: uuid.UUID,
    payload: UsuarioUpdate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin)
    ),
) -> UsuarioResponse:
    """
    Actualiza datos de un usuario en el tenant.
    """
    stmt = select(Usuario).where(Usuario.id == usuario_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Usuario.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    usuario = result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"}},
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Validar escalamiento si se intenta modificar el rol
    if "rol" in update_data and update_data["rol"] == UserRole.super_admin and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN_ROLE", "message": "Solo un SuperAdmin puede asignar el rol super_admin"}},
        )

    for field, value in update_data.items():
        setattr(usuario, field, value)

    usuario.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="UPDATE",
        entidad="usuario",
        entidad_id=usuario.id,
        usuario=current_user,
        detalles=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(usuario)

    return UsuarioResponse.model_validate(usuario)
