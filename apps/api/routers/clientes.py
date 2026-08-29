"""
OS Privacidad — Router de Clientes
==================================
Endpoints CRUD para empresas clientes, protegidos con RLS por Tenant.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_tenant_db, log_audit, require_role
from models.cliente import Cliente
from models.usuario import UserRole, Usuario
from schemas.cliente import ClienteCreate, ClienteResponse, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("", response_model=list[ClienteResponse])
async def list_clientes(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(
            UserRole.super_admin,
            UserRole.tenant_admin,
            UserRole.dpo,
            UserRole.analista,
            UserRole.auditor,
        )
    ),
) -> list[ClienteResponse]:
    """
    Lista todos los clientes del tenant autenticado (RLS + query filter).
    """
    stmt = select(Cliente).where(Cliente.activo.is_(True))
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Cliente.tenant_id == current_user.tenant_id)

    stmt = stmt.order_by(Cliente.nombre_razon_social.asc())
    result = await db.execute(stmt)
    clientes = result.scalars().all()
    return [ClienteResponse.model_validate(c) for c in clientes]


@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    payload: ClienteCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo)
    ),
) -> ClienteResponse:
    """
    Crea un nuevo cliente dentro del tenant del usuario actual.
    """
    if not current_user.tenant_id and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "NO_TENANT", "message": "Usuario no pertenece a un tenant válido"}},
        )

    tenant_id = current_user.tenant_id

    # Verificar unicidad de RUC para este tenant
    stmt = select(Cliente).where(Cliente.tenant_id == tenant_id, Cliente.ruc == payload.ruc)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "RUC_EXISTS", "message": f"Ya existe un cliente con RUC {payload.ruc} en esta organización"}},
        )

    cliente = Cliente(
        tenant_id=tenant_id,
        nombre_razon_social=payload.nombre_razon_social,
        ruc=payload.ruc,
        sector=payload.sector,
        contacto_principal_nombre=payload.contacto_principal_nombre,
        contacto_principal_email=payload.contacto_principal_email,
        created_by=current_user.id,
    )
    db.add(cliente)
    await db.flush()

    # Auditoría
    await log_audit(
        db=db,
        accion="CREATE",
        entidad="cliente",
        entidad_id=cliente.id,
        usuario=current_user,
        detalles={"nombre": cliente.nombre_razon_social, "ruc": cliente.ruc},
        request=request,
    )
    await db.commit()
    await db.refresh(cliente)

    return ClienteResponse.model_validate(cliente)


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def get_cliente(
    cliente_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(
            UserRole.super_admin,
            UserRole.tenant_admin,
            UserRole.dpo,
            UserRole.analista,
            UserRole.auditor,
        )
    ),
) -> ClienteResponse:
    """
    Obtiene los datos de un cliente específico por ID (aislado por RLS).
    """
    stmt = select(Cliente).where(Cliente.id == cliente_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Cliente.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    cliente = result.scalar_one_or_none()

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CLIENTE_NOT_FOUND", "message": "Cliente no encontrado"}},
        )

    return ClienteResponse.model_validate(cliente)


@router.patch("/{cliente_id}", response_model=ClienteResponse)
async def update_cliente(
    cliente_id: uuid.UUID,
    payload: ClienteUpdate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo)
    ),
) -> ClienteResponse:
    """
    Actualiza la información de un cliente.
    """
    stmt = select(Cliente).where(Cliente.id == cliente_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Cliente.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    cliente = result.scalar_one_or_none()

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CLIENTE_NOT_FOUND", "message": "Cliente no encontrado"}},
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cliente, field, value)

    cliente.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="UPDATE",
        entidad="cliente",
        entidad_id=cliente.id,
        usuario=current_user,
        detalles=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(cliente)

    return ClienteResponse.model_validate(cliente)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cliente(
    cliente_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin)
    ),
):
    """
    Desactiva (soft-delete) un cliente dentro del tenant.
    """
    stmt = select(Cliente).where(Cliente.id == cliente_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Cliente.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    cliente = result.scalar_one_or_none()

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CLIENTE_NOT_FOUND", "message": "Cliente no encontrado"}},
        )

    cliente.activo = False
    cliente.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="DELETE",
        entidad="cliente",
        entidad_id=cliente.id,
        usuario=current_user,
        detalles={"soft_delete": True},
        request=request,
    )
    await db.commit()
