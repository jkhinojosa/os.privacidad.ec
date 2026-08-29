"""
OS Privacidad — Router de Gestión de Riesgos y Matriz de Calor
==============================================================
Endpoints para análisis de riesgos de derechos y libertades, cálculo ponderado R = P * (I * V)
y matriz de calor 5x5 conforme a la Guía SPDP 2026.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.deps import get_tenant_db, log_audit, require_role
from core.risk_engine import calcular_score_y_nivel_riesgo
from core.state_machine import generate_next_codigo
from models.medida_seguridad import MedidaSeguridad
from models.riesgo import Riesgo, RiesgoDimension, RiesgoEstado, RiesgoNivel
from models.usuario import UserRole, Usuario
from schemas.riesgo import (
    MatrizCalorCelda,
    MatrizCalorResponse,
    RiesgoCreate,
    RiesgoMitigacionRequest,
    RiesgoResponse,
)

router = APIRouter(prefix="/riesgos", tags=["Riesgos & Matriz de Calor"])


@router.get("/matriz", response_model=MatrizCalorResponse)
async def get_matriz_calor(
    proceso_id: uuid.UUID | None = Query(None, description="Filtrar matriz por proceso"),
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
) -> MatrizCalorResponse:
    """
    Genera la matriz de calor 5x5 consolidando el estado del riesgo inherente y residual.
    """
    stmt = select(Riesgo)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Riesgo.tenant_id == current_user.tenant_id)
    if proceso_id:
        stmt = stmt.where(Riesgo.proceso_id == proceso_id)

    result = await db.execute(stmt)
    riesgos = result.scalars().all()

    # Inicializar cuadrícula 5x5 (Probabilidad 1..5, Impacto 1..5)
    celdas_map: dict[tuple[int, int], MatrizCalorCelda] = {}
    for p in range(1, 6):
        for i in range(1, 6):
            celdas_map[(p, i)] = MatrizCalorCelda(probabilidad=p, impacto=i, cantidad_inherente=0, cantidad_residual=0, riesgos_ids=[])

    resumen_inherente = {"bajo": 0, "medio": 0, "alto": 0, "critico": 0}
    resumen_residual = {"bajo": 0, "medio": 0, "alto": 0, "critico": 0}

    for r in riesgos:
        # Inherente
        p_inh = max(1, min(5, r.probabilidad_inherente))
        i_inh = max(1, min(5, r.impacto_inherente))
        celdas_map[(p_inh, i_inh)].cantidad_inherente += 1
        celdas_map[(p_inh, i_inh)].riesgos_ids.append(r.id)
        resumen_inherente[r.nivel_riesgo_inherente.value] += 1

        # Residual (si existe)
        if r.probabilidad_residual and r.impacto_residual and r.nivel_riesgo_residual:
            p_res = max(1, min(5, r.probabilidad_residual))
            i_res = max(1, min(5, r.impacto_residual))
            celdas_map[(p_res, i_res)].cantidad_residual += 1
            resumen_residual[r.nivel_riesgo_residual.value] += 1

    return MatrizCalorResponse(
        total_riesgos=len(riesgos),
        resumen_inherente=resumen_inherente,
        resumen_residual=resumen_residual,
        matriz=list(celdas_map.values()),
    )


@router.get("", response_model=list[RiesgoResponse])
async def list_riesgos(
    proceso_id: uuid.UUID | None = Query(None, description="Filtrar por proceso"),
    nivel: RiesgoNivel | None = Query(None, description="Filtrar por nivel inherente"),
    dimension: RiesgoDimension | None = Query(None, description="Filtrar por dimensión"),
    estado: RiesgoEstado | None = Query(None, description="Filtrar por estado"),
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
) -> list[RiesgoResponse]:
    """
    Lista todos los riesgos del tenant con sus medidas aplicadas.
    """
    stmt = select(Riesgo).options(selectinload(Riesgo.medidas))
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Riesgo.tenant_id == current_user.tenant_id)

    if proceso_id:
        stmt = stmt.where(Riesgo.proceso_id == proceso_id)
    if nivel:
        stmt = stmt.where(Riesgo.nivel_riesgo_inherente == nivel)
    if dimension:
        stmt = stmt.where(Riesgo.dimension_afectada == dimension)
    if estado:
        stmt = stmt.where(Riesgo.estado == estado)

    stmt = stmt.order_by(Riesgo.riesgo_inherente_score.desc())
    result = await db.execute(stmt)
    riesgos = result.scalars().all()
    return [RiesgoResponse.model_validate(r) for r in riesgos]


@router.post("", response_model=RiesgoResponse, status_code=status.HTTP_201_CREATED)
async def create_riesgo(
    payload: RiesgoCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> RiesgoResponse:
    """
    Registra un nuevo escenario de riesgo y calcula automáticamente su score y nivel inherente.
    """
    if not current_user.tenant_id and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "NO_TENANT", "message": "Usuario no pertenece a un tenant válido"}},
        )

    tenant_id = current_user.tenant_id
    codigo = await generate_next_codigo(db, tenant_id, "RSK")

    # ── Cálculo de Riesgo Inherente R = P * (I * V) ───────────
    score_inh, nivel_inh = calcular_score_y_nivel_riesgo(
        probabilidad=payload.probabilidad_inherente,
        impacto=payload.impacto_inherente,
        es_vulnerable=payload.es_grupo_vulnerable,
    )

    riesgo = Riesgo(
        tenant_id=tenant_id,
        codigo=codigo,
        proceso_id=payload.proceso_id,
        nombre=payload.nombre,
        descripcion_amenaza=payload.descripcion_amenaza,
        vulnerabilidad=payload.vulnerabilidad,
        dimension_afectada=payload.dimension_afectada,
        es_grupo_vulnerable=payload.es_grupo_vulnerable,
        probabilidad_inherente=payload.probabilidad_inherente,
        impacto_inherente=payload.impacto_inherente,
        riesgo_inherente_score=score_inh,
        nivel_riesgo_inherente=nivel_inh,
        estado=RiesgoEstado.identificado,
        created_by=current_user.id,
    )

    # Asociar medidas iniciales si fueron enviadas
    if payload.medidas_ids:
        stmt_medidas = select(MedidaSeguridad).where(
            MedidaSeguridad.tenant_id == tenant_id,
            MedidaSeguridad.id.in_(payload.medidas_ids),
        )
        medidas_res = await db.execute(stmt_medidas)
        riesgo.medidas = list(medidas_res.scalars().all())

    db.add(riesgo)
    await db.flush()

    # Auditoría
    await log_audit(
        db=db,
        accion="CREATE",
        entidad="riesgo",
        entidad_id=riesgo.id,
        usuario=current_user,
        detalles={
            "codigo": riesgo.codigo,
            "score_inherente": score_inh,
            "nivel_inherente": nivel_inh.value,
        },
        request=request,
    )
    await db.commit()

    # Cargar con relación
    stmt_reload = (
        select(Riesgo)
        .options(selectinload(Riesgo.medidas))
        .where(Riesgo.id == riesgo.id)
    )
    res_reload = await db.execute(stmt_reload)
    riesgo_loaded = res_reload.scalar_one()

    return RiesgoResponse.model_validate(riesgo_loaded)


@router.get("/{riesgo_id}", response_model=RiesgoResponse)
async def get_riesgo(
    riesgo_id: uuid.UUID,
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
) -> RiesgoResponse:
    """
    Obtiene los detalles completos de un riesgo y sus medidas mitigadoras.
    """
    stmt = (
        select(Riesgo)
        .options(selectinload(Riesgo.medidas))
        .where(Riesgo.id == riesgo_id)
    )
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Riesgo.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    riesgo = result.scalar_one_or_none()

    if not riesgo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RIESGO_NOT_FOUND", "message": "Riesgo no encontrado"}},
        )

    return RiesgoResponse.model_validate(riesgo)


@router.post("/{riesgo_id}/mitigacion", response_model=RiesgoResponse)
async def apply_riesgo_mitigacion(
    riesgo_id: uuid.UUID,
    payload: RiesgoMitigacionRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> RiesgoResponse:
    """
    Aplica salvaguardas de seguridad al riesgo y calcula el riesgo residual.
    """
    stmt = (
        select(Riesgo)
        .options(selectinload(Riesgo.medidas))
        .where(Riesgo.id == riesgo_id)
    )
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Riesgo.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    riesgo = result.scalar_one_or_none()

    if not riesgo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RIESGO_NOT_FOUND", "message": "Riesgo no encontrado"}},
        )

    # Cargar medidas de seguridad enviadas
    stmt_medidas = select(MedidaSeguridad).where(
        MedidaSeguridad.tenant_id == current_user.tenant_id,
        MedidaSeguridad.id.in_(payload.medidas_ids),
    )
    medidas_res = await db.execute(stmt_medidas)
    medidas = list(medidas_res.scalars().all())

    if not medidas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_MEDIDAS", "message": "Ninguna de las medidas de seguridad especificadas es válida"}},
        )

    # ── Cálculo de Riesgo Residual R = P * (I * V) ────────────
    score_res, nivel_res = calcular_score_y_nivel_riesgo(
        probabilidad=payload.probabilidad_residual,
        impacto=payload.impacto_residual,
        es_vulnerable=riesgo.es_grupo_vulnerable,
    )

    riesgo.medidas = medidas
    riesgo.probabilidad_residual = payload.probabilidad_residual
    riesgo.impacto_residual = payload.impacto_residual
    riesgo.riesgo_residual_score = score_res
    riesgo.nivel_riesgo_residual = nivel_res
    riesgo.estado = payload.estado
    riesgo.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="MITIGAR_RIESGO",
        entidad="riesgo",
        entidad_id=riesgo.id,
        usuario=current_user,
        detalles={
            "codigo": riesgo.codigo,
            "score_residual": score_res,
            "nivel_residual": nivel_res.value,
            "medidas_count": len(medidas),
        },
        request=request,
    )
    await db.commit()
    await db.refresh(riesgo)

    return RiesgoResponse.model_validate(riesgo)
