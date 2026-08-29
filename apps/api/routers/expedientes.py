"""
OS Privacidad — Router de Expedientes
=====================================
Gestión de expedientes documentales y probatorios asociados a Casos y Clientes.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_tenant_db, log_audit, require_role
from core.state_machine import generate_next_codigo
from models.expediente import Expediente, ExpedienteEstado
from models.usuario import UserRole, Usuario
from schemas.expediente import (
    ExpedienteCreate,
    ExpedienteResponse,
    ExpedienteUpdate,
)

router = APIRouter(prefix="/expedientes", tags=["Expedientes"])


@router.get("", response_model=list[ExpedienteResponse])
async def list_expedientes(
    caso_id: uuid.UUID | None = Query(None, description="Filtrar por caso asociado"),
    cliente_id: uuid.UUID | None = Query(None, description="Filtrar por empresa cliente"),
    estado: ExpedienteEstado | None = Query(None, description="Filtrar por estado"),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(
            UserRole.super_admin,
            UserRole.tenant_admin,
            UserRole.dpo,
            UserRole.analista,
            UserRole.auditor,
            UserRole.cliente,
        )
    ),
) -> list[ExpedienteResponse]:
    """
    Lista los expedientes del tenant con filtros opcionales.
    """
    stmt = select(Expediente)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Expediente.tenant_id == current_user.tenant_id)

    if current_user.rol == UserRole.cliente and current_user.cliente_id:
        stmt = stmt.where(Expediente.cliente_id == current_user.cliente_id)

    if caso_id:
        stmt = stmt.where(Expediente.caso_id == caso_id)
    if cliente_id:
        stmt = stmt.where(Expediente.cliente_id == cliente_id)
    if estado:
        stmt = stmt.where(Expediente.estado == estado)

    stmt = stmt.order_by(Expediente.created_at.desc())
    result = await db.execute(stmt)
    expedientes = result.scalars().all()
    return [ExpedienteResponse.model_validate(e) for e in expedientes]


@router.post("", response_model=ExpedienteResponse, status_code=status.HTTP_201_CREATED)
async def create_expediente(
    payload: ExpedienteCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(
            UserRole.super_admin,
            UserRole.tenant_admin,
            UserRole.dpo,
            UserRole.analista,
        )
    ),
) -> ExpedienteResponse:
    """
    Crea un nuevo expediente documental asignando código correlativo EXP-YYYY-NNNN.
    """
    if not current_user.tenant_id and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "NO_TENANT", "message": "Usuario no pertenece a un tenant válido"}
            },
        )

    tenant_id = current_user.tenant_id

    # Generación atómica del código correlativo EXP-YYYY-NNNN
    codigo = await generate_next_codigo(db, tenant_id, "EXP")

    expediente = Expediente(
        tenant_id=tenant_id,
        codigo=codigo,
        caso_id=payload.caso_id,
        cliente_id=payload.cliente_id,
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        estado=payload.estado,
        created_by=current_user.id,
    )
    db.add(expediente)
    await db.flush()

    # Auditoría
    await log_audit(
        db=db,
        accion="CREATE",
        entidad="expediente",
        entidad_id=expediente.id,
        usuario=current_user,
        detalles={"codigo": expediente.codigo, "nombre": expediente.nombre},
        request=request,
    )
    await db.commit()
    await db.refresh(expediente)

    return ExpedienteResponse.model_validate(expediente)


@router.get("/{expediente_id}", response_model=ExpedienteResponse)
async def get_expediente(
    expediente_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(
            UserRole.super_admin,
            UserRole.tenant_admin,
            UserRole.dpo,
            UserRole.analista,
            UserRole.auditor,
            UserRole.cliente,
        )
    ),
) -> ExpedienteResponse:
    """
    Obtiene los detalles de un expediente por ID.
    """
    stmt = select(Expediente).where(Expediente.id == expediente_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Expediente.tenant_id == current_user.tenant_id)

    if current_user.rol == UserRole.cliente and current_user.cliente_id:
        stmt = stmt.where(Expediente.cliente_id == current_user.cliente_id)

    result = await db.execute(stmt)
    expediente = result.scalar_one_or_none()

    if not expediente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {"code": "EXPEDIENTE_NOT_FOUND", "message": "Expediente no encontrado"}
            },
        )

    return ExpedienteResponse.model_validate(expediente)


@router.patch("/{expediente_id}", response_model=ExpedienteResponse)
async def update_expediente(
    expediente_id: uuid.UUID,
    payload: ExpedienteUpdate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(
            UserRole.super_admin,
            UserRole.tenant_admin,
            UserRole.dpo,
            UserRole.analista,
        )
    ),
) -> ExpedienteResponse:
    """
    Actualiza la información o estado de un expediente.
    """
    stmt = select(Expediente).where(Expediente.id == expediente_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Expediente.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    expediente = result.scalar_one_or_none()

    if not expediente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {"code": "EXPEDIENTE_NOT_FOUND", "message": "Expediente no encontrado"}
            },
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expediente, field, value)

    expediente.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="UPDATE",
        entidad="expediente",
        entidad_id=expediente.id,
        usuario=current_user,
        detalles=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(expediente)

    return ExpedienteResponse.model_validate(expediente)
