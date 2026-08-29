"""
OS Privacidad — Router de Casos
===============================
Gestión de incidentes, solicitudes ARCO y consultas con máquina de estados finita.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_tenant_db, log_audit, require_role
from core.state_machine import generate_next_codigo, validate_caso_transition
from models.caso import Caso, CasoEstado, CasoPrioridad, CasoTipo
from models.usuario import UserRole, Usuario
from schemas.caso import (
    CasoCreate,
    CasoResponse,
    CasoTransitionRequest,
    CasoUpdate,
)

router = APIRouter(prefix="/casos", tags=["Casos (Incidentes / ARCO)"])


@router.get("", response_model=list[CasoResponse])
async def list_casos(
    estado: CasoEstado | None = Query(None, description="Filtrar por estado"),
    tipo: CasoTipo | None = Query(None, description="Filtrar por tipo"),
    prioridad: CasoPrioridad | None = Query(None, description="Filtrar por prioridad"),
    cliente_id: uuid.UUID | None = Query(None, description="Filtrar por empresa cliente"),
    asignado_a: uuid.UUID | None = Query(None, description="Filtrar por usuario asignado"),
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
) -> list[CasoResponse]:
    """
    Lista todos los casos del tenant según filtros y permisos de usuario.
    """
    stmt = select(Caso)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Caso.tenant_id == current_user.tenant_id)

    # Si es usuario rol cliente, solo ve los casos de su empresa
    if current_user.rol == UserRole.cliente and current_user.cliente_id:
        stmt = stmt.where(Caso.cliente_id == current_user.cliente_id)

    if estado:
        stmt = stmt.where(Caso.estado == estado)
    if tipo:
        stmt = stmt.where(Caso.tipo == tipo)
    if prioridad:
        stmt = stmt.where(Caso.prioridad == prioridad)
    if cliente_id:
        stmt = stmt.where(Caso.cliente_id == cliente_id)
    if asignado_a:
        stmt = stmt.where(Caso.asignado_a == asignado_a)

    stmt = stmt.order_by(Caso.created_at.desc())
    result = await db.execute(stmt)
    casos = result.scalars().all()
    return [CasoResponse.model_validate(c) for c in casos]


@router.post("", response_model=CasoResponse, status_code=status.HTTP_201_CREATED)
async def create_caso(
    payload: CasoCreate,
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
) -> CasoResponse:
    """
    Registra un nuevo caso, asigna código correlativo CAS-YYYY-NNNN e inicia en estado 'abierto'.
    """
    if not current_user.tenant_id and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "NO_TENANT", "message": "Usuario no pertenece a un tenant válido"}
            },
        )

    tenant_id = current_user.tenant_id

    # Generación atómica del código correlativo CAS-YYYY-NNNN
    codigo = await generate_next_codigo(db, tenant_id, "CAS")

    caso = Caso(
        tenant_id=tenant_id,
        codigo=codigo,
        cliente_id=payload.cliente_id,
        proceso_id=payload.proceso_id,
        asignado_a=payload.asignado_a,
        titulo=payload.titulo,
        descripcion=payload.descripcion,
        tipo=payload.tipo,
        prioridad=payload.prioridad,
        estado=CasoEstado.abierto,
        fecha_limite=payload.fecha_limite,
        created_by=current_user.id,
    )
    db.add(caso)
    await db.flush()

    # Auditoría
    await log_audit(
        db=db,
        accion="CREATE",
        entidad="caso",
        entidad_id=caso.id,
        usuario=current_user,
        detalles={
            "codigo": caso.codigo,
            "tipo": caso.tipo.value,
            "prioridad": caso.prioridad.value,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(caso)

    return CasoResponse.model_validate(caso)


@router.get("/{caso_id}", response_model=CasoResponse)
async def get_caso(
    caso_id: uuid.UUID,
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
) -> CasoResponse:
    """
    Obtiene los datos detallados de un caso.
    """
    stmt = select(Caso).where(Caso.id == caso_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Caso.tenant_id == current_user.tenant_id)

    if current_user.rol == UserRole.cliente and current_user.cliente_id:
        stmt = stmt.where(Caso.cliente_id == current_user.cliente_id)

    result = await db.execute(stmt)
    caso = result.scalar_one_or_none()

    if not caso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASO_NOT_FOUND", "message": "Caso no encontrado"}},
        )

    return CasoResponse.model_validate(caso)


@router.patch("/{caso_id}", response_model=CasoResponse)
async def update_caso(
    caso_id: uuid.UUID,
    payload: CasoUpdate,
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
) -> CasoResponse:
    """
    Actualiza datos descriptivos de un caso (el cambio de estado se realiza vía /transicion).
    """
    stmt = select(Caso).where(Caso.id == caso_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Caso.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    caso = result.scalar_one_or_none()

    if not caso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASO_NOT_FOUND", "message": "Caso no encontrado"}},
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(caso, field, value)

    caso.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="UPDATE",
        entidad="caso",
        entidad_id=caso.id,
        usuario=current_user,
        detalles=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(caso)

    return CasoResponse.model_validate(caso)


@router.post("/{caso_id}/transicion", response_model=CasoResponse)
async def execute_caso_transition(
    caso_id: uuid.UUID,
    payload: CasoTransitionRequest,
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
) -> CasoResponse:
    """
    Ejecuta una transición de estado en el caso, validada mediante la máquina de estados 3.1.
    """
    stmt = select(Caso).where(Caso.id == caso_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Caso.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    caso = result.scalar_one_or_none()

    if not caso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASO_NOT_FOUND", "message": "Caso no encontrado"}},
        )

    # Validar transición según la máquina de estados
    estado_anterior = caso.estado
    validate_caso_transition(estado_anterior, payload.nuevo_estado)

    # Aplicar cambio de estado
    caso.estado = payload.nuevo_estado
    caso.updated_by = current_user.id

    now = datetime.datetime.now(datetime.UTC)
    if payload.nuevo_estado == CasoEstado.cerrado:
        caso.fecha_cierre = now
        if payload.resolucion:
            caso.resolucion = payload.resolucion
    elif payload.nuevo_estado == CasoEstado.reabierto:
        caso.fecha_cierre = None

    # Registrar en auditoría la transición y el motivo
    await log_audit(
        db=db,
        accion="TRANSICION_ESTADO",
        entidad="caso",
        entidad_id=caso.id,
        usuario=current_user,
        detalles={
            "codigo": caso.codigo,
            "estado_anterior": estado_anterior.value,
            "nuevo_estado": payload.nuevo_estado.value,
            "motivo": payload.motivo,
            "resolucion": payload.resolucion,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(caso)

    return CasoResponse.model_validate(caso)
