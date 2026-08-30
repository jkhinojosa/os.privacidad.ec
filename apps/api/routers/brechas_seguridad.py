"""
OS Privacidad — Router de Gestión y Notificación de Brechas de Seguridad (LOPDP)
================================================================================
Endpoints para reporte de incidentes, control de plazos perentorios (5 días SPDP,
3 días Titulares), informe oficial Art. 26 RGLOPDP y calificación de impacto.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.breach_report_generator import generar_informe_oficial_spdp
from core.deps import get_tenant_db, log_audit, require_role
from core.sla_engine import (
    calcular_fecha_limite_habiles,
    evaluar_semaforo_sla,
)
from core.state_machine import generate_next_codigo, validate_brecha_transition
from models.brecha_seguridad import (
    BrechaEstado,
    BrechaSeguridad,
    BrechaSeveridad,
    VulnerabilidadTipo,
)
from models.tenant import Tenant
from models.usuario import UserRole, Usuario
from schemas.brecha_seguridad import (
    BrechaCalificacionRiesgoRequest,
    BrechaCierreRequest,
    BrechaInformeOficialSPDPResponse,
    BrechaNotificacionSPDPRequest,
    BrechaNotificacionTitularesRequest,
    BrechaResumenSLAResponse,
    BrechaSeguridadCreate,
    BrechaSeguridadResponse,
    BrechaSeguridadUpdate,
)

router = APIRouter(prefix="/brechas-seguridad", tags=["Brechas de Seguridad (SPDP / LOPDP)"])


def _enrich_brecha_response(brecha: BrechaSeguridad) -> BrechaSeguridadResponse:
    """Enriquece la respuesta de la brecha con el diagnóstico de plazos para SPDP y Titulares."""
    res = BrechaSeguridadResponse.model_validate(brecha)

    # Diagnóstico SLA SPDP (5 días hábiles)
    if not brecha.notificada_a_spdp:
        diag_spdp = evaluar_semaforo_sla(brecha.fecha_limite_spdp)
        res.dias_restantes_spdp = diag_spdp["dias_restantes_habiles"]
        res.estado_semaforo_spdp = diag_spdp["estado_semaforo"]
    else:
        res.estado_semaforo_spdp = "notificada"

    # Diagnóstico SLA Titulares (3 días hábiles si aplica)
    if brecha.requiere_notificacion_titulares and brecha.fecha_limite_titulares:
        if not brecha.notificada_a_titulares:
            diag_tit = evaluar_semaforo_sla(brecha.fecha_limite_titulares)
            res.dias_restantes_titulares = diag_tit["dias_restantes_habiles"]
            res.estado_semaforo_titulares = diag_tit["estado_semaforo"]
        else:
            res.estado_semaforo_titulares = "notificada"

    return res


@router.get("/resumen-sla", response_model=BrechaResumenSLAResponse)
async def get_resumen_sla_brechas(
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
) -> BrechaResumenSLAResponse:
    """
    Retorna las métricas cuantitativas de cumplimiento del plazo de 5 días ante la SPDP.
    """
    stmt = select(BrechaSeguridad)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(BrechaSeguridad.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    brechas = result.scalars().all()

    total = len(brechas)
    spdp_en_tiempo = 0
    spdp_en_alerta = 0
    spdp_vencidas = 0
    notificadas_a_spdp = 0
    notificadas_a_titulares = 0

    for b in brechas:
        if b.notificada_a_spdp:
            notificadas_a_spdp += 1
            if b.fecha_notificacion_spdp and b.fecha_notificacion_spdp <= b.fecha_limite_spdp:
                spdp_en_tiempo += 1
            else:
                spdp_vencidas += 1
        else:
            diag = evaluar_semaforo_sla(b.fecha_limite_spdp)
            if diag["estado_semaforo"] == "en_tiempo":
                spdp_en_tiempo += 1
            elif diag["estado_semaforo"] == "en_alerta":
                spdp_en_alerta += 1
            else:
                spdp_vencidas += 1

        if b.notificada_a_titulares:
            notificadas_a_titulares += 1

    pct = round((spdp_en_tiempo / total * 100), 1) if total > 0 else 100.0

    return BrechaResumenSLAResponse(
        total_brechas=total,
        spdp_en_tiempo=spdp_en_tiempo,
        spdp_en_alerta=spdp_en_alerta,
        spdp_vencidas=spdp_vencidas,
        notificadas_a_spdp=notificadas_a_spdp,
        notificadas_a_titulares=notificadas_a_titulares,
        porcentaje_cumplimiento_spdp=pct,
    )


@router.get("", response_model=list[BrechaSeguridadResponse])
async def list_brechas_seguridad(
    estado: BrechaEstado | None = Query(None, description="Filtrar por estado"),
    tipo: VulnerabilidadTipo | None = Query(None, description="Filtrar por tipología"),
    severidad: BrechaSeveridad | None = Query(None, description="Filtrar por severidad"),
    proceso_id: uuid.UUID | None = Query(None, description="Filtrar por proceso"),
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
) -> list[BrechaSeguridadResponse]:
    """
    Lista las vulneraciones de seguridad del tenant con semáforos de plazo ante la SPDP.
    """
    stmt = select(BrechaSeguridad)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(BrechaSeguridad.tenant_id == current_user.tenant_id)

    if estado:
        stmt = stmt.where(BrechaSeguridad.estado == estado)
    if tipo:
        stmt = stmt.where(BrechaSeguridad.tipo_vulneracion == tipo)
    if severidad:
        stmt = stmt.where(BrechaSeguridad.severidad == severidad)
    if proceso_id:
        stmt = stmt.where(BrechaSeguridad.proceso_id == proceso_id)

    stmt = stmt.order_by(BrechaSeguridad.fecha_limite_spdp.asc())
    result = await db.execute(stmt)
    brechas = result.scalars().all()

    return [_enrich_brecha_response(b) for b in brechas]


@router.post("", response_model=BrechaSeguridadResponse, status_code=status.HTTP_201_CREATED)
async def create_brecha_seguridad(
    payload: BrechaSeguridadCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> BrechaSeguridadResponse:
    """
    Registra formalmente una vulneración de seguridad e inicia el cómputo de 5 días hábiles ante la SPDP.
    """
    if not current_user.tenant_id and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "NO_TENANT", "message": "Usuario no pertenece a un tenant válido"}
            },
        )

    tenant_id = current_user.tenant_id
    codigo = await generate_next_codigo(db, tenant_id, "BRC")

    now = datetime.datetime.now(datetime.UTC)
    fecha_limite_spdp = calcular_fecha_limite_habiles(now, dias_habiles=5)

    brecha = BrechaSeguridad(
        tenant_id=tenant_id,
        codigo=codigo,
        caso_id=payload.caso_id,
        proceso_id=payload.proceso_id,
        titulo=payload.titulo,
        descripcion=payload.descripcion,
        tipo_vulneracion=payload.tipo_vulneracion,
        severidad=payload.severidad,
        estado=BrechaEstado.detectada,
        sistemas_afectados=payload.sistemas_afectados,
        causa_presunta=payload.causa_presunta,
        colectivos_afectados=payload.colectivos_afectados,
        volumen_titulares_estimado=payload.volumen_titulares_estimado,
        categorias_datos_expuestas=payload.categorias_datos_expuestas,
        fecha_deteccion=now,
        fecha_limite_spdp=fecha_limite_spdp,
        medidas_contencion_inmediatas=payload.medidas_contencion_inmediatas,
        medidas_remediacion_previstas=payload.medidas_remediacion_previstas,
        created_by=current_user.id,
    )
    db.add(brecha)
    await db.flush()

    # Auditoría
    await log_audit(
        db=db,
        accion="CREATE_BRECHA_SEGURIDAD",
        entidad="brecha_seguridad",
        entidad_id=brecha.id,
        usuario=current_user,
        detalles={
            "codigo": brecha.codigo,
            "tipo": brecha.tipo_vulneracion.value,
            "severidad": brecha.severidad.value,
            "fecha_limite_spdp": fecha_limite_spdp.isoformat(),
        },
        request=request,
    )
    await db.commit()
    await db.refresh(brecha)

    return _enrich_brecha_response(brecha)


@router.get("/{brecha_id}", response_model=BrechaSeguridadResponse)
async def get_brecha_seguridad(
    brecha_id: uuid.UUID,
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
) -> BrechaSeguridadResponse:
    """
    Obtiene los detalles de un incidente o brecha de seguridad por ID.
    """
    stmt = select(BrechaSeguridad).where(BrechaSeguridad.id == brecha_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(BrechaSeguridad.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    brecha = result.scalar_one_or_none()

    if not brecha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "BRECHA_NOT_FOUND",
                    "message": "Vulneración de seguridad no encontrada",
                }
            },
        )

    return _enrich_brecha_response(brecha)


@router.patch("/{brecha_id}", response_model=BrechaSeguridadResponse)
async def update_brecha_seguridad(
    brecha_id: uuid.UUID,
    payload: BrechaSeguridadUpdate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> BrechaSeguridadResponse:
    """
    Actualiza la información técnica, sistemas afectados o medidas de contención de la brecha.
    """
    stmt = select(BrechaSeguridad).where(BrechaSeguridad.id == brecha_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(BrechaSeguridad.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    brecha = result.scalar_one_or_none()

    if not brecha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "BRECHA_NOT_FOUND",
                    "message": "Vulneración de seguridad no encontrada",
                }
            },
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brecha, field, value)

    brecha.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="UPDATE_BRECHA",
        entidad="brecha_seguridad",
        entidad_id=brecha.id,
        usuario=current_user,
        detalles=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(brecha)

    return _enrich_brecha_response(brecha)


@router.post("/{brecha_id}/calificar-riesgo", response_model=BrechaSeguridadResponse)
async def calificar_riesgo_brecha(
    brecha_id: uuid.UUID,
    payload: BrechaCalificacionRiesgoRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.dpo, UserRole.tenant_admin)
    ),
) -> BrechaSeguridadResponse:
    """
    Dictamen vinculante del DPD evaluando si la brecha conlleva riesgo a derechos de titulares (Art. 46 LOPDP).
    Si conlleva riesgo, inicia automáticamente el término de 3 días hábiles para notificar al titular.
    """
    stmt = select(BrechaSeguridad).where(BrechaSeguridad.id == brecha_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(BrechaSeguridad.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    brecha = result.scalar_one_or_none()

    if not brecha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "BRECHA_NOT_FOUND",
                    "message": "Vulneración de seguridad no encontrada",
                }
            },
        )

    validate_brecha_transition(brecha.estado, BrechaEstado.evaluada_dpd)

    now = datetime.datetime.now(datetime.UTC)
    brecha.dictamen_dpd = payload.dictamen_dpd
    brecha.evaluacion_riesgo_titulares = payload.evaluacion_riesgo_titulares
    brecha.requiere_notificacion_titulares = payload.conlleva_riesgo_titulares
    brecha.fecha_calificacion_riesgo = now

    if payload.conlleva_riesgo_titulares:
        # Cómputo de 3 días hábiles para titulares conforme al Art. 46 LOPDP
        brecha.fecha_limite_titulares = calcular_fecha_limite_habiles(now, dias_habiles=3)

    brecha.estado = BrechaEstado.evaluada_dpd
    brecha.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="CALIFICAR_RIESGO_BRECHA",
        entidad="brecha_seguridad",
        entidad_id=brecha.id,
        usuario=current_user,
        detalles={
            "conlleva_riesgo": payload.conlleva_riesgo_titulares,
            "fecha_limite_titulares": brecha.fecha_limite_titulares.isoformat()
            if brecha.fecha_limite_titulares
            else None,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(brecha)

    return _enrich_brecha_response(brecha)


@router.post("/{brecha_id}/notificar-spdp", response_model=BrechaSeguridadResponse)
async def notificar_brecha_a_spdp(
    brecha_id: uuid.UUID,
    payload: BrechaNotificacionSPDPRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.dpo, UserRole.tenant_admin)
    ),
) -> BrechaSeguridadResponse:
    """
    Asienta la notificación formal de la vulneración ante la SPDP y la ARCOTEL (Art. 43 LOPDP).
    Si se notifica fuera del término de 5 días hábiles, exige justificación técnica de la dilación.
    """
    stmt = select(BrechaSeguridad).where(BrechaSeguridad.id == brecha_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(BrechaSeguridad.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    brecha = result.scalar_one_or_none()

    if not brecha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "BRECHA_NOT_FOUND",
                    "message": "Vulneración de seguridad no encontrada",
                }
            },
        )

    now = datetime.datetime.now(datetime.UTC)

    # Validar si es extemporánea (> 5 días hábiles)
    if now > brecha.fecha_limite_spdp and not payload.justificacion_dilacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "JUSTIFICACION_DILACION_REQUIRED",
                    "message": "La notificación se realiza fuera del término de 5 días hábiles. Es mandatorio adjuntar los motivos técnicos de la dilación conforme al Art. 43 LOPDP.",
                }
            },
        )

    validate_brecha_transition(brecha.estado, BrechaEstado.notificada_spdp)

    brecha.notificada_a_spdp = True
    brecha.fecha_notificacion_spdp = now
    brecha.numero_radicado_spdp = payload.numero_radicado_spdp
    brecha.notificada_a_arcotel = payload.notificada_a_arcotel
    brecha.justificacion_dilacion = payload.justificacion_dilacion
    brecha.estado = BrechaEstado.notificada_spdp
    brecha.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="NOTIFICAR_SPDP_BRECHA",
        entidad="brecha_seguridad",
        entidad_id=brecha.id,
        usuario=current_user,
        detalles={
            "radicado": payload.numero_radicado_spdp,
            "es_extemporanea": now > brecha.fecha_limite_spdp,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(brecha)

    return _enrich_brecha_response(brecha)


@router.post("/{brecha_id}/notificar-titulares", response_model=BrechaSeguridadResponse)
async def notificar_brecha_a_titulares(
    brecha_id: uuid.UUID,
    payload: BrechaNotificacionTitularesRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.dpo, UserRole.tenant_admin)
    ),
) -> BrechaSeguridadResponse:
    """
    Asienta la notificación a titulares afectados o el acogimiento a excepción calificada (Art. 46 LOPDP).
    """
    stmt = select(BrechaSeguridad).where(BrechaSeguridad.id == brecha_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(BrechaSeguridad.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    brecha = result.scalar_one_or_none()

    if not brecha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "BRECHA_NOT_FOUND",
                    "message": "Vulneración de seguridad no encontrada",
                }
            },
        )

    validate_brecha_transition(brecha.estado, BrechaEstado.notificada_titulares)

    now = datetime.datetime.now(datetime.UTC)
    brecha.notificada_a_titulares = True
    brecha.fecha_notificacion_titulares = now
    brecha.canal_notificacion_titulares = payload.canal_notificacion
    brecha.excepcion_titulares_aplicada = payload.excepcion_aplicada
    brecha.justificacion_excepcion_titulares = payload.justificacion_excepcion
    brecha.estado = BrechaEstado.notificada_titulares
    brecha.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="NOTIFICAR_TITULARES_BRECHA",
        entidad="brecha_seguridad",
        entidad_id=brecha.id,
        usuario=current_user,
        detalles={
            "canal": payload.canal_notificacion,
            "excepcion": payload.excepcion_aplicada,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(brecha)

    return _enrich_brecha_response(brecha)


@router.get("/{brecha_id}/informe-spdp", response_model=BrechaInformeOficialSPDPResponse)
async def generate_informe_spdp_oficial(
    brecha_id: uuid.UUID,
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
) -> BrechaInformeOficialSPDPResponse:
    """
    Genera el informe oficial de notificación conforme a los 7 numerales del Art. 26 del Reglamento General LOPDP.
    """
    stmt = select(BrechaSeguridad).where(BrechaSeguridad.id == brecha_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(BrechaSeguridad.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    brecha = result.scalar_one_or_none()

    if not brecha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "BRECHA_NOT_FOUND",
                    "message": "Vulneración de seguridad no encontrada",
                }
            },
        )

    # Cargar datos del tenant
    stmt_tenant = select(Tenant).where(Tenant.id == brecha.tenant_id)
    tenant_res = await db.execute(stmt_tenant)
    tenant = tenant_res.scalar_one()

    reporte_dict = generar_informe_oficial_spdp(
        brecha=brecha,
        organizacion_nombre=tenant.nombre,
        organizacion_ruc=tenant.slug,
    )

    return BrechaInformeOficialSPDPResponse.model_validate(reporte_dict)


@router.post("/{brecha_id}/cerrar", response_model=BrechaSeguridadResponse)
async def close_brecha_seguridad(
    brecha_id: uuid.UUID,
    payload: BrechaCierreRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.dpo, UserRole.tenant_admin)
    ),
) -> BrechaSeguridadResponse:
    """
    Registra las conclusiones de remediación y da por resuelto y cerrado el incidente de brecha.
    """
    stmt = select(BrechaSeguridad).where(BrechaSeguridad.id == brecha_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(BrechaSeguridad.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    brecha = result.scalar_one_or_none()

    if not brecha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "BRECHA_NOT_FOUND",
                    "message": "Vulneración de seguridad no encontrada",
                }
            },
        )

    validate_brecha_transition(brecha.estado, BrechaEstado.resuelta_cerrada)

    now = datetime.datetime.now(datetime.UTC)
    brecha.estado = BrechaEstado.resuelta_cerrada
    brecha.fecha_cierre = now
    brecha.medidas_remediacion_previstas += (
        f"\n[CIERRE FINAL - {now.isoformat()}]: {payload.resultado_final_remediacion}"
    )
    brecha.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="CERRAR_BRECHA_SEGURIDAD",
        entidad="brecha_seguridad",
        entidad_id=brecha.id,
        usuario=current_user,
        detalles={"resultado": payload.resultado_final_remediacion},
        request=request,
    )
    await db.commit()
    await db.refresh(brecha)

    return _enrich_brecha_response(brecha)
