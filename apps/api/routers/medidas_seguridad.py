"""
OS Privacidad — Router de Medidas de Seguridad (Salvaguardas)
=============================================================
Endpoints CRUD para el catálogo de controles técnicos, organizativos, jurídicos y físicos.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_tenant_db, log_audit, require_role
from core.state_machine import generate_next_codigo
from models.medida_seguridad import MedidaEstado, MedidaSeguridad, MedidaTipo
from models.usuario import UserRole, Usuario
from schemas.medida_seguridad import (
    MedidaSeguridadCreate,
    MedidaSeguridadResponse,
    MedidaSeguridadUpdate,
)

router = APIRouter(prefix="/medidas-seguridad", tags=["Medidas de Seguridad (Salvaguardas)"])


@router.get("", response_model=list[MedidaSeguridadResponse])
async def list_medidas_seguridad(
    tipo: MedidaTipo | None = Query(None, description="Filtrar por tipología de medida"),
    estado: MedidaEstado | None = Query(None, description="Filtrar por estado de implementación"),
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
) -> list[MedidaSeguridadResponse]:
    """
    Lista las medidas de seguridad registradas en el tenant.
    """
    stmt = select(MedidaSeguridad).where(MedidaSeguridad.activo.is_(True))
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(MedidaSeguridad.tenant_id == current_user.tenant_id)

    if tipo:
        stmt = stmt.where(MedidaSeguridad.tipo == tipo)
    if estado:
        stmt = stmt.where(MedidaSeguridad.estado_implementacion == estado)

    stmt = stmt.order_by(MedidaSeguridad.codigo.asc())
    result = await db.execute(stmt)
    medidas = result.scalars().all()
    return [MedidaSeguridadResponse.model_validate(m) for m in medidas]


@router.post("", response_model=MedidaSeguridadResponse, status_code=status.HTTP_201_CREATED)
async def create_medida_seguridad(
    payload: MedidaSeguridadCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> MedidaSeguridadResponse:
    """
    Registra una nueva medida o salvaguarda de seguridad con código correlativo MED-YYYY-NNNN.
    """
    if not current_user.tenant_id and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "NO_TENANT", "message": "Usuario no pertenece a un tenant válido"}
            },
        )

    tenant_id = current_user.tenant_id
    codigo = await generate_next_codigo(db, tenant_id, "MED")

    medida = MedidaSeguridad(
        tenant_id=tenant_id,
        codigo=codigo,
        tipo=payload.tipo,
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        estado_implementacion=payload.estado_implementacion,
        responsable=payload.responsable,
        evidencia_url=payload.evidencia_url,
        created_by=current_user.id,
    )
    db.add(medida)
    await db.flush()

    # Auditoría
    await log_audit(
        db=db,
        accion="CREATE",
        entidad="medida_seguridad",
        entidad_id=medida.id,
        usuario=current_user,
        detalles={"codigo": medida.codigo, "tipo": medida.tipo.value, "nombre": medida.nombre},
        request=request,
    )
    await db.commit()
    await db.refresh(medida)

    return MedidaSeguridadResponse.model_validate(medida)


@router.get("/{medida_id}", response_model=MedidaSeguridadResponse)
async def get_medida_seguridad(
    medida_id: uuid.UUID,
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
) -> MedidaSeguridadResponse:
    """
    Obtiene los detalles de una medida de seguridad.
    """
    stmt = select(MedidaSeguridad).where(MedidaSeguridad.id == medida_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(MedidaSeguridad.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    medida = result.scalar_one_or_none()

    if not medida:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "MEDIDA_NOT_FOUND",
                    "message": "Medida de seguridad no encontrada",
                }
            },
        )

    return MedidaSeguridadResponse.model_validate(medida)


@router.patch("/{medida_id}", response_model=MedidaSeguridadResponse)
async def update_medida_seguridad(
    medida_id: uuid.UUID,
    payload: MedidaSeguridadUpdate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> MedidaSeguridadResponse:
    """
    Actualiza el estado o descripción de una medida de seguridad.
    """
    stmt = select(MedidaSeguridad).where(MedidaSeguridad.id == medida_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(MedidaSeguridad.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    medida = result.scalar_one_or_none()

    if not medida:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "MEDIDA_NOT_FOUND",
                    "message": "Medida de seguridad no encontrada",
                }
            },
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(medida, field, value)

    medida.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="UPDATE",
        entidad="medida_seguridad",
        entidad_id=medida.id,
        usuario=current_user,
        detalles=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(medida)

    return MedidaSeguridadResponse.model_validate(medida)
