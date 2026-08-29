"""
OS Privacidad — Router de Evaluaciones de Impacto en la Protección de Datos (EIPD / PIA)
========================================================================================
Endpoints para el ciclo de vida de la EIPD conforme al Art. 42 LOPDP y Art. 32 RGLOPDP.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.deps import get_tenant_db, log_audit, require_role
from core.state_machine import generate_next_codigo
from models.eipd import EIPDEstado, EvaluacionImpacto
from models.proceso import Proceso
from models.riesgo import Riesgo
from models.usuario import UserRole, Usuario
from schemas.eipd import (
    EIPDAprobacionRequest,
    EIPDCreate,
    EIPDReporteOficialResponse,
    EIPDResponse,
    EIPDUpdate,
)
from schemas.proceso import ProcesoResponse
from schemas.riesgo import RiesgoResponse

router = APIRouter(prefix="/eipds", tags=["Evaluaciones de Impacto (EIPD / PIA)"])


@router.get("", response_model=list[EIPDResponse])
async def list_eipds(
    proceso_id: uuid.UUID | None = Query(None, description="Filtrar por proceso"),
    estado: EIPDEstado | None = Query(None, description="Filtrar por estado"),
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
) -> list[EIPDResponse]:
    """
    Lista las Evaluaciones de Impacto (EIPD) del tenant.
    """
    stmt = select(EvaluacionImpacto)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(EvaluacionImpacto.tenant_id == current_user.tenant_id)

    if proceso_id:
        stmt = stmt.where(EvaluacionImpacto.proceso_id == proceso_id)
    if estado:
        stmt = stmt.where(EvaluacionImpacto.estado == estado)

    stmt = stmt.order_by(EvaluacionImpacto.created_at.desc())
    result = await db.execute(stmt)
    eipds = result.scalars().all()
    return [EIPDResponse.model_validate(e) for e in eipds]


@router.post("", response_model=EIPDResponse, status_code=status.HTTP_201_CREATED)
async def create_eipd(
    payload: EIPDCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> EIPDResponse:
    """
    Crea un nuevo borrador de Evaluación de Impacto con código correlativo EIPD-YYYY-NNNN.
    """
    if not current_user.tenant_id and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "NO_TENANT", "message": "Usuario no pertenece a un tenant válido"}},
        )

    tenant_id = current_user.tenant_id

    # Validar que el proceso existe en el tenant
    stmt_proc = select(Proceso).where(Proceso.id == payload.proceso_id, Proceso.tenant_id == tenant_id)
    proc_res = await db.execute(stmt_proc)
    if not proc_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PROCESO_NOT_FOUND", "message": "El proceso asociado no existe en este tenant"}},
        )

    codigo = await generate_next_codigo(db, tenant_id, "EIPD")

    eipd = EvaluacionImpacto(
        tenant_id=tenant_id,
        codigo=codigo,
        proceso_id=payload.proceso_id,
        titulo=payload.titulo,
        descripcion_sistematica=payload.descripcion_sistematica,
        justificacion_necesidad_proporcionalidad=payload.justificacion_necesidad_proporcionalidad,
        opinion_titulares_consultados=payload.opinion_titulares_consultados,
        estado=EIPDEstado.borrador,
        created_by=current_user.id,
    )
    db.add(eipd)
    await db.flush()

    # Auditoría
    await log_audit(
        db=db,
        accion="CREATE",
        entidad="evaluacion_impacto",
        entidad_id=eipd.id,
        usuario=current_user,
        detalles={"codigo": eipd.codigo, "titulo": eipd.titulo},
        request=request,
    )
    await db.commit()
    await db.refresh(eipd)

    return EIPDResponse.model_validate(eipd)


@router.get("/{eipd_id}", response_model=EIPDResponse)
async def get_eipd(
    eipd_id: uuid.UUID,
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
) -> EIPDResponse:
    """
    Obtiene los datos de una Evaluación de Impacto por ID.
    """
    stmt = select(EvaluacionImpacto).where(EvaluacionImpacto.id == eipd_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(EvaluacionImpacto.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    eipd = result.scalar_one_or_none()

    if not eipd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EIPD_NOT_FOUND", "message": "Evaluación de Impacto no encontrada"}},
        )

    return EIPDResponse.model_validate(eipd)


@router.patch("/{eipd_id}", response_model=EIPDResponse)
async def update_eipd(
    eipd_id: uuid.UUID,
    payload: EIPDUpdate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> EIPDResponse:
    """
    Actualiza la narrativa o justificación del borrador de una EIPD.
    """
    stmt = select(EvaluacionImpacto).where(EvaluacionImpacto.id == eipd_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(EvaluacionImpacto.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    eipd = result.scalar_one_or_none()

    if not eipd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EIPD_NOT_FOUND", "message": "Evaluación de Impacto no encontrada"}},
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(eipd, field, value)

    eipd.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="UPDATE",
        entidad="evaluacion_impacto",
        entidad_id=eipd.id,
        usuario=current_user,
        detalles=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(eipd)

    return EIPDResponse.model_validate(eipd)


@router.post("/{eipd_id}/aprobar", response_model=EIPDResponse)
async def approve_eipd(
    eipd_id: uuid.UUID,
    payload: EIPDAprobacionRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.dpo, UserRole.tenant_admin)
    ),
) -> EIPDResponse:
    """
    Emite el dictamen vinculante del DPD y aprueba la Evaluación de Impacto (EIPD).
    """
    stmt = select(EvaluacionImpacto).where(EvaluacionImpacto.id == eipd_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(EvaluacionImpacto.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    eipd = result.scalar_one_or_none()

    if not eipd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EIPD_NOT_FOUND", "message": "Evaluación de Impacto no encontrada"}},
        )

    eipd.dictamen_dpd = payload.dictamen_dpd
    eipd.estado = payload.nuevo_estado
    eipd.fecha_aprobacion = datetime.datetime.now(datetime.UTC)
    eipd.aprobado_por = current_user.id
    eipd.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="APROBAR_EIPD",
        entidad="evaluacion_impacto",
        entidad_id=eipd.id,
        usuario=current_user,
        detalles={"codigo": eipd.codigo, "estado": eipd.estado.value},
        request=request,
    )
    await db.commit()
    await db.refresh(eipd)

    return EIPDResponse.model_validate(eipd)


@router.get("/{eipd_id}/reporte", response_model=EIPDReporteOficialResponse)
async def generate_eipd_official_report(
    eipd_id: uuid.UUID,
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
) -> EIPDReporteOficialResponse:
    """
    Genera el informe técnico-jurídico consolidado conforme al Art. 32 RGLOPDP.
    """
    stmt = select(EvaluacionImpacto).where(EvaluacionImpacto.id == eipd_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(EvaluacionImpacto.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    eipd = result.scalar_one_or_none()

    if not eipd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EIPD_NOT_FOUND", "message": "Evaluación de Impacto no encontrada"}},
        )

    # Cargar Proceso RAT
    stmt_proc = select(Proceso).where(Proceso.id == eipd.proceso_id)
    proc_res = await db.execute(stmt_proc)
    proceso = proc_res.scalar_one()

    # Cargar Riesgos asociados con sus medidas
    stmt_riesgos = (
        select(Riesgo)
        .options(selectinload(Riesgo.medidas))
        .where(Riesgo.proceso_id == eipd.proceso_id, Riesgo.tenant_id == eipd.tenant_id)
    )
    riesgos_res = await db.execute(stmt_riesgos)
    riesgos = list(riesgos_res.scalars().all())

    # Resumen de cumplimiento
    resumen = (
        f"Informe de Evaluación de Impacto {eipd.codigo} para el proceso '{proceso.nombre}'. "
        f"Base Legal: {proceso.base_legal}. Puntaje MTGE: {proceso.puntaje_mtge} puntos. "
        f"Total de escenarios de riesgo evaluados: {len(riesgos)}. "
        f"Estado: {eipd.estado.value.upper()}."
    )

    return EIPDReporteOficialResponse(
        eipd=EIPDResponse.model_validate(eipd),
        proceso=ProcesoResponse.model_validate(proceso),
        riesgos_asociados=[RiesgoResponse.model_validate(r) for r in riesgos],
        resumen_cumplimiento_lopdp=resumen,
        fecha_generacion=datetime.datetime.now(datetime.UTC),
    )
