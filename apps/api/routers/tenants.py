"""
OS Privacidad — Router de Tenants
=================================
Endpoints CRUD de organizaciones (restringido a SuperAdmin).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_db, log_audit, require_role
from models.tenant import Tenant
from models.usuario import UserRole, Usuario
from schemas.tenant import TenantCreate, TenantResponse, TenantUpdate

router = APIRouter(prefix="/tenants", tags=["Tenants (Organizaciones)"])


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(UserRole.super_admin)),
) -> list[TenantResponse]:
    """
    Lista todos los tenants del sistema (Solo SuperAdmin).
    """
    stmt = select(Tenant).order_by(Tenant.created_at.desc())
    result = await db.execute(stmt)
    tenants = result.scalars().all()
    return [TenantResponse.model_validate(t) for t in tenants]


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(UserRole.super_admin)),
) -> TenantResponse:
    """
    Crea un nuevo tenant en el sistema (Solo SuperAdmin).
    """
    # Verificar unicidad del slug
    stmt = select(Tenant).where(Tenant.slug == payload.slug)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "SLUG_ALREADY_EXISTS", "message": f"El slug '{payload.slug}' ya está en uso"}},
        )

    tenant = Tenant(
        nombre=payload.nombre,
        slug=payload.slug,
        plan=payload.plan,
    )
    db.add(tenant)
    await db.flush()

    # Log de auditoría
    await log_audit(
        db=db,
        accion="CREATE",
        entidad="tenant",
        entidad_id=tenant.id,
        usuario=current_user,
        detalles={"nombre": tenant.nombre, "slug": tenant.slug, "plan": tenant.plan.value},
        request=request,
    )
    await db.commit()
    await db.refresh(tenant)

    return TenantResponse.model_validate(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(UserRole.super_admin)),
) -> TenantResponse:
    """
    Obtiene los detalles de un tenant específico por ID.
    """
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TENANT_NOT_FOUND", "message": "Organización no encontrada"}},
        )

    return TenantResponse.model_validate(tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    payload: TenantUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(UserRole.super_admin)),
) -> TenantResponse:
    """
    Actualiza la configuración o estado de un tenant.
    """
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TENANT_NOT_FOUND", "message": "Organización no encontrada"}},
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    await log_audit(
        db=db,
        accion="UPDATE",
        entidad="tenant",
        entidad_id=tenant.id,
        usuario=current_user,
        detalles=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(tenant)

    return TenantResponse.model_validate(tenant)
