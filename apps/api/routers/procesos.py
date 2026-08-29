"""
OS Privacidad — Router de Procesos (Registro de Actividades de Tratamiento - RAT)
================================================================================
Endpoints CRUD para actividades de tratamiento (RAT) conforme a la LOPDP y MTGE.
Calcula automáticamente el puntaje MTGE y determina si requiere EIPD previa.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_tenant_db, log_audit, require_role
from core.risk_engine import calcular_puntaje_mtge, evaluar_obligatoriedad_eipd
from models.proceso import Proceso
from models.usuario import UserRole, Usuario
from schemas.proceso import ProcesoCreate, ProcesoResponse, ProcesoUpdate

router = APIRouter(prefix="/procesos", tags=["Procesos (RAT)"])


@router.get("", response_model=list[ProcesoResponse])
async def list_procesos(
    cliente_id: uuid.UUID | None = Query(None, description="Filtrar por empresa cliente"),
    requiere_eipd: bool | None = Query(None, description="Filtrar por obligatoriedad de EIPD"),
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
) -> list[ProcesoResponse]:
    """
    Lista las actividades de tratamiento del tenant (RLS + filtros opcionales).
    """
    stmt = select(Proceso).where(Proceso.activo.is_(True))
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Proceso.tenant_id == current_user.tenant_id)

    if cliente_id:
        stmt = stmt.where(Proceso.cliente_id == cliente_id)
    if requiere_eipd is not None:
        stmt = stmt.where(Proceso.requiere_eipd == requiere_eipd)

    stmt = stmt.order_by(Proceso.nombre.asc())
    result = await db.execute(stmt)
    procesos = result.scalars().all()
    return [ProcesoResponse.model_validate(p) for p in procesos]


@router.post("", response_model=ProcesoResponse, status_code=status.HTTP_201_CREATED)
async def create_proceso(
    payload: ProcesoCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> ProcesoResponse:
    """
    Registra una nueva actividad de tratamiento RAT en el tenant.
    Calcula automáticamente el puntaje MTGE y evalúa la obligatoriedad de EIPD.
    """
    if not current_user.tenant_id and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "NO_TENANT", "message": "Usuario no pertenece a un tenant válido"}},
        )

    tenant_id = current_user.tenant_id

    # ── Cálculo MTGE y Evaluación de EIPD Obligatoria ─────────
    puntaje_mtge = calcular_puntaje_mtge(
        volumen_titulares=payload.volumen_titulares_estimado,
        frecuencia=payload.frecuencia_tratamiento.value,
        tipo_datos=payload.tipo_datos,
        tiene_perfiles=payload.tiene_perfiles,
        transferencia_internacional=payload.transferencia_internacional,
    )
    req_eipd, _ = evaluar_obligatoriedad_eipd(
        puntaje_mtge=puntaje_mtge,
        tipo_datos=payload.tipo_datos,
        tiene_perfiles=payload.tiene_perfiles,
    )

    proceso = Proceso(
        tenant_id=tenant_id,
        cliente_id=payload.cliente_id,
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        area_responsable=payload.area_responsable,
        base_legal=payload.base_legal,
        finalidad=payload.finalidad,
        tipo_datos=payload.tipo_datos,
        destinatarios=payload.destinatarios,
        colectivos_titulares=payload.colectivos_titulares,
        tiene_perfiles=payload.tiene_perfiles,
        transferencia_internacional=payload.transferencia_internacional,
        paises_transferencia=payload.paises_transferencia,
        garantias_transferencia=payload.garantias_transferencia,
        plazo_conservacion=payload.plazo_conservacion,
        frecuencia_tratamiento=payload.frecuencia_tratamiento.value,
        permanencia_tratamiento=payload.permanencia_tratamiento,
        volumen_titulares_estimado=payload.volumen_titulares_estimado,
        puntaje_mtge=puntaje_mtge,
        requiere_eipd=req_eipd,
        created_by=current_user.id,
    )
    db.add(proceso)
    await db.flush()

    # Auditoría
    await log_audit(
        db=db,
        accion="CREATE",
        entidad="proceso",
        entidad_id=proceso.id,
        usuario=current_user,
        detalles={
            "nombre": proceso.nombre,
            "base_legal": proceso.base_legal,
            "puntaje_mtge": puntaje_mtge,
            "requiere_eipd": req_eipd,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(proceso)

    return ProcesoResponse.model_validate(proceso)


@router.get("/{proceso_id}", response_model=ProcesoResponse)
async def get_proceso(
    proceso_id: uuid.UUID,
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
) -> ProcesoResponse:
    """
    Obtiene los detalles de un proceso RAT por ID.
    """
    stmt = select(Proceso).where(Proceso.id == proceso_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Proceso.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    proceso = result.scalar_one_or_none()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PROCESO_NOT_FOUND", "message": "Actividad de tratamiento no encontrada"}},
        )

    return ProcesoResponse.model_validate(proceso)


@router.patch("/{proceso_id}", response_model=ProcesoResponse)
async def update_proceso(
    proceso_id: uuid.UUID,
    payload: ProcesoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> ProcesoResponse:
    """
    Actualiza la información de un proceso RAT y recalcula el puntaje MTGE.
    """
    stmt = select(Proceso).where(Proceso.id == proceso_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Proceso.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    proceso = result.scalar_one_or_none()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PROCESO_NOT_FOUND", "message": "Actividad de tratamiento no encontrada"}},
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "frecuencia_tratamiento" in update_data and update_data["frecuencia_tratamiento"]:
        update_data["frecuencia_tratamiento"] = update_data["frecuencia_tratamiento"].value

    for field, value in update_data.items():
        setattr(proceso, field, value)

    # Recalcular MTGE y EIPD
    proceso.puntaje_mtge = calcular_puntaje_mtge(
        volumen_titulares=proceso.volumen_titulares_estimado,
        frecuencia=proceso.frecuencia_tratamiento,
        tipo_datos=proceso.tipo_datos,
        tiene_perfiles=proceso.tiene_perfiles,
        transferencia_internacional=proceso.transferencia_internacional,
    )
    req_eipd, _ = evaluar_obligatoriedad_eipd(
        puntaje_mtge=proceso.puntaje_mtge,
        tipo_datos=proceso.tipo_datos,
        tiene_perfiles=proceso.tiene_perfiles,
    )
    proceso.requiere_eipd = req_eipd
    proceso.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="UPDATE",
        entidad="proceso",
        entidad_id=proceso.id,
        usuario=current_user,
        detalles=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(proceso)

    return ProcesoResponse.model_validate(proceso)


@router.delete("/{proceso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proceso(
    proceso_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo)
    ),
):
    """
    Desactiva (soft-delete) una actividad de tratamiento.
    """
    stmt = select(Proceso).where(Proceso.id == proceso_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Proceso.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    proceso = result.scalar_one_or_none()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PROCESO_NOT_FOUND", "message": "Actividad de tratamiento no encontrada"}},
        )

    proceso.activo = False
    proceso.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="DELETE",
        entidad="proceso",
        entidad_id=proceso.id,
        usuario=current_user,
        detalles={"soft_delete": True},
        request=request,
    )
    await db.commit()
