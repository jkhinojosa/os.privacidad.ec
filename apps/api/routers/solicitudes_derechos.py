"""
OS Privacidad — Router de Solicitudes de Derechos de los Titulares (LOPDP)
==========================================================================
Endpoints para el ciclo de vida, cómputo de SLA en días hábiles, prórrogas,
notificación a encargados (Art. 23 RGLOPDP) y exportación de portabilidad (Art. 17).
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.deps import get_tenant_db, log_audit, require_role
from core.portability_exporter import generar_paquete_portabilidad
from core.sla_engine import (
    calcular_fecha_limite_habiles,
    evaluar_semaforo_sla,
)
from core.state_machine import generate_next_codigo, validate_solicitud_transition
from models.notificacion_encargado import NotificacionEncargado, NotificacionEstado
from models.solicitud_derecho import DerechoTipo, SolicitudDerecho, SolicitudEstado
from models.usuario import UserRole, Usuario
from schemas.notificacion_encargado import (
    NotificacionEncargadoCreate,
    NotificacionEncargadoResponse,
)
from schemas.solicitud_derecho import (
    SolicitudDerechoCreate,
    SolicitudDerechoResponse,
    SolicitudDerechoUpdate,
    SolicitudEjecucionRequest,
    SolicitudProrrogaRequest,
    SolicitudResolucionRequest,
    SolicitudResumenSLAResponse,
    SolicitudSubsanacionRequest,
)

router = APIRouter(prefix="/solicitudes-derechos", tags=["Derechos de los Titulares (LOPDP)"])


def _enrich_solicitud_response(sol: SolicitudDerecho) -> SolicitudDerechoResponse:
    """Enriquece la respuesta de la solicitud con el diagnóstico dinámico de SLA."""
    diag = evaluar_semaforo_sla(sol.fecha_limite_sla)
    res = SolicitudDerechoResponse.model_validate(sol)
    res.dias_restantes_habiles = diag["dias_restantes_habiles"]
    res.estado_semaforo = diag["estado_semaforo"]
    return res


@router.get("/resumen-sla", response_model=SolicitudResumenSLAResponse)
async def get_resumen_sla(
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
) -> SolicitudResumenSLAResponse:
    """
    Retorna métricas consolidadas del cumplimiento de plazos legales (SLA) del tenant.
    """
    stmt = select(SolicitudDerecho)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(SolicitudDerecho.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    solicitudes = result.scalars().all()

    total = len(solicitudes)
    en_tiempo = 0
    en_alerta = 0
    vencidas = 0
    atendidas_a_tiempo = 0

    for s in solicitudes:
        if s.estado == SolicitudEstado.atendida:
            if s.fecha_cierre and s.fecha_cierre <= s.fecha_limite_sla:
                atendidas_a_tiempo += 1
            else:
                vencidas += 1
        elif s.estado == SolicitudEstado.archivada:
            continue
        else:
            diag = evaluar_semaforo_sla(s.fecha_limite_sla)
            if diag["estado_semaforo"] == "en_tiempo":
                en_tiempo += 1
            elif diag["estado_semaforo"] == "en_alerta":
                en_alerta += 1
            else:
                vencidas += 1

    pct = round((atendidas_a_tiempo + en_tiempo) / total * 100, 1) if total > 0 else 100.0

    return SolicitudResumenSLAResponse(
        total_solicitudes=total,
        en_tiempo=en_tiempo,
        en_alerta=en_alerta,
        vencidas=vencidas,
        atendidas_a_tiempo=atendidas_a_tiempo,
        porcentaje_cumplimiento=pct,
    )


@router.get("", response_model=list[SolicitudDerechoResponse])
async def list_solicitudes_derechos(
    estado: SolicitudEstado | None = Query(None, description="Filtrar por estado"),
    tipo_derecho: DerechoTipo | None = Query(None, description="Filtrar por tipo de derecho"),
    cliente_id: uuid.UUID | None = Query(None, description="Filtrar por cliente"),
    asignado_a: uuid.UUID | None = Query(None, description="Filtrar por responsable asignado"),
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
) -> list[SolicitudDerechoResponse]:
    """
    Lista las solicitudes de ejercicio de derechos del tenant con estado de SLA en tiempo real.
    """
    stmt = select(SolicitudDerecho).options(
        selectinload(SolicitudDerecho.notificaciones_encargados)
    )
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(SolicitudDerecho.tenant_id == current_user.tenant_id)

    if estado:
        stmt = stmt.where(SolicitudDerecho.estado == estado)
    if tipo_derecho:
        stmt = stmt.where(SolicitudDerecho.tipo_derecho == tipo_derecho)
    if cliente_id:
        stmt = stmt.where(SolicitudDerecho.cliente_id == cliente_id)
    if asignado_a:
        stmt = stmt.where(SolicitudDerecho.asignado_a == asignado_a)

    stmt = stmt.order_by(SolicitudDerecho.fecha_limite_sla.asc())
    result = await db.execute(stmt)
    solicitudes = result.scalars().all()

    return [_enrich_solicitud_response(s) for s in solicitudes]


@router.post("", response_model=SolicitudDerechoResponse, status_code=status.HTTP_201_CREATED)
async def create_solicitud_derecho(
    payload: SolicitudDerechoCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> SolicitudDerechoResponse:
    """
    Registra formalmente una solicitud de ejercicio de derechos e inicia el cómputo de SLA (15 días hábiles).
    """
    if not current_user.tenant_id and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "NO_TENANT", "message": "Usuario no pertenece a un tenant válido"}
            },
        )

    tenant_id = current_user.tenant_id
    codigo = await generate_next_codigo(db, tenant_id, "SOL")

    now = datetime.datetime.now(datetime.UTC)
    # Cálculo legal perentorio de 15 días hábiles
    fecha_limite = calcular_fecha_limite_habiles(now, dias_habiles=15)

    solicitud = SolicitudDerecho(
        tenant_id=tenant_id,
        codigo=codigo,
        cliente_id=payload.cliente_id,
        proceso_id=payload.proceso_id,
        asignado_a=current_user.id,
        tipo_derecho=payload.tipo_derecho,
        canal_recepcion=payload.canal_recepcion,
        estado=SolicitudEstado.recibida,
        titular_nombre=payload.titular_nombre,
        titular_identificacion=payload.titular_identificacion,
        titular_email=payload.titular_email,
        titular_telefono=payload.titular_telefono,
        es_representante=payload.es_representante,
        representante_nombre=payload.representante_nombre,
        representante_identificacion=payload.representante_identificacion,
        documento_acreditacion_url=payload.documento_acreditacion_url,
        motivo_solicitud=payload.motivo_solicitud,
        especificacion_datos=payload.especificacion_datos,
        datos_a_modificar=payload.datos_a_modificar,
        fecha_recepcion=now,
        fecha_limite_sla=fecha_limite,
        created_by=current_user.id,
    )
    db.add(solicitud)
    await db.flush()

    # Auditoría
    await log_audit(
        db=db,
        accion="CREATE_SOLICITUD_DERECHO",
        entidad="solicitud_derecho",
        entidad_id=solicitud.id,
        usuario=current_user,
        detalles={
            "codigo": solicitud.codigo,
            "tipo_derecho": solicitud.tipo_derecho.value,
            "titular": solicitud.titular_identificacion,
            "fecha_limite_sla": fecha_limite.isoformat(),
        },
        request=request,
    )
    await db.commit()

    # Recargar con relaciones
    stmt_reload = (
        select(SolicitudDerecho)
        .options(selectinload(SolicitudDerecho.notificaciones_encargados))
        .where(SolicitudDerecho.id == solicitud.id)
    )
    res_reload = await db.execute(stmt_reload)
    solicitud_loaded = res_reload.scalar_one()

    return _enrich_solicitud_response(solicitud_loaded)


@router.get("/{solicitud_id}", response_model=SolicitudDerechoResponse)
async def get_solicitud_derecho(
    solicitud_id: uuid.UUID,
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
) -> SolicitudDerechoResponse:
    """
    Obtiene los detalles de una solicitud de derechos y sus notificaciones a encargados.
    """
    stmt = (
        select(SolicitudDerecho)
        .options(selectinload(SolicitudDerecho.notificaciones_encargados))
        .where(SolicitudDerecho.id == solicitud_id)
    )
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(SolicitudDerecho.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()

    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SOLICITUD_NOT_FOUND",
                    "message": "Solicitud de derechos no encontrada",
                }
            },
        )

    return _enrich_solicitud_response(solicitud)


@router.patch("/{solicitud_id}", response_model=SolicitudDerechoResponse)
async def update_solicitud_derecho(
    solicitud_id: uuid.UUID,
    payload: SolicitudDerechoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> SolicitudDerechoResponse:
    """
    Actualiza datos administrativos de una solicitud de derechos.
    """
    stmt = (
        select(SolicitudDerecho)
        .options(selectinload(SolicitudDerecho.notificaciones_encargados))
        .where(SolicitudDerecho.id == solicitud_id)
    )
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(SolicitudDerecho.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()

    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SOLICITUD_NOT_FOUND",
                    "message": "Solicitud de derechos no encontrada",
                }
            },
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(solicitud, field, value)

    solicitud.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="UPDATE_SOLICITUD",
        entidad="solicitud_derecho",
        entidad_id=solicitud.id,
        usuario=current_user,
        detalles=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(solicitud)

    return _enrich_solicitud_response(solicitud)


@router.post("/{solicitud_id}/subsanar", response_model=SolicitudDerechoResponse)
async def request_solicitud_subsanacion(
    solicitud_id: uuid.UUID,
    payload: SolicitudSubsanacionRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> SolicitudDerechoResponse:
    """
    Requiere subsanación o aclaración al titular (Art. 14 RGLOPDP).
    Otorga hasta 10 días al titular y transiciona a 'en_subsanacion'.
    """
    stmt = (
        select(SolicitudDerecho)
        .options(selectinload(SolicitudDerecho.notificaciones_encargados))
        .where(SolicitudDerecho.id == solicitud_id)
    )
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(SolicitudDerecho.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()

    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SOLICITUD_NOT_FOUND",
                    "message": "Solicitud de derechos no encontrada",
                }
            },
        )

    validate_solicitud_transition(solicitud.estado, SolicitudEstado.en_subsanacion)

    now = datetime.datetime.now(datetime.UTC)
    fecha_lim_sub = now + datetime.timedelta(days=payload.dias_plazo_titular)

    solicitud.estado = SolicitudEstado.en_subsanacion
    solicitud.fecha_subsanacion_limite = fecha_lim_sub
    solicitud.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="REQUERIR_SUBSANACION",
        entidad="solicitud_derecho",
        entidad_id=solicitud.id,
        usuario=current_user,
        detalles={"motivo": payload.motivo_subsanacion, "fecha_limite": fecha_lim_sub.isoformat()},
        request=request,
    )
    await db.commit()
    await db.refresh(solicitud)

    return _enrich_solicitud_response(solicitud)


@router.post("/{solicitud_id}/prorrogar", response_model=SolicitudDerechoResponse)
async def apply_solicitud_prorroga(
    solicitud_id: uuid.UUID,
    payload: SolicitudProrrogaRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.dpo, UserRole.tenant_admin)
    ),
) -> SolicitudDerechoResponse:
    """
    Aplica una prórroga excepcional de 15 días hábiles justificando la complejidad técnica.
    """
    stmt = (
        select(SolicitudDerecho)
        .options(selectinload(SolicitudDerecho.notificaciones_encargados))
        .where(SolicitudDerecho.id == solicitud_id)
    )
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(SolicitudDerecho.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()

    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SOLICITUD_NOT_FOUND",
                    "message": "Solicitud de derechos no encontrada",
                }
            },
        )

    if solicitud.prorroga_aplicada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "ALREADY_PRORROGADA",
                    "message": "La solicitud ya fue objeto de prórroga legal previa (máximo 1 prórroga)",
                }
            },
        )

    validate_solicitud_transition(solicitud.estado, SolicitudEstado.prorrogada)

    now = datetime.datetime.now(datetime.UTC)
    # Sumar 15 días hábiles adicionales a la fecha límite original
    nueva_fecha_limite = calcular_fecha_limite_habiles(
        solicitud.fecha_limite_sla, dias_habiles=payload.dias_prorroga_habiles
    )

    solicitud.estado = SolicitudEstado.prorrogada
    solicitud.prorroga_aplicada = True
    solicitud.fecha_prorroga = now
    solicitud.dias_prorroga = payload.dias_prorroga_habiles
    solicitud.motivo_prorroga = payload.motivo_prorroga
    solicitud.fecha_limite_sla = nueva_fecha_limite
    solicitud.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="PRORROGAR_SOLICITUD",
        entidad="solicitud_derecho",
        entidad_id=solicitud.id,
        usuario=current_user,
        detalles={
            "motivo": payload.motivo_prorroga,
            "nueva_fecha_limite": nueva_fecha_limite.isoformat(),
        },
        request=request,
    )
    await db.commit()
    await db.refresh(solicitud)

    return _enrich_solicitud_response(solicitud)


@router.post("/{solicitud_id}/resolver", response_model=SolicitudDerechoResponse)
async def resolve_solicitud_derecho(
    solicitud_id: uuid.UUID,
    payload: SolicitudResolucionRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.dpo, UserRole.tenant_admin)
    ),
) -> SolicitudDerechoResponse:
    """
    Emite la resolución formal y motivada (Aceptada o Denegada) con dictamen vinculante del DPD.
    """
    stmt = (
        select(SolicitudDerecho)
        .options(selectinload(SolicitudDerecho.notificaciones_encargados))
        .where(SolicitudDerecho.id == solicitud_id)
    )
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(SolicitudDerecho.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()

    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SOLICITUD_NOT_FOUND",
                    "message": "Solicitud de derechos no encontrada",
                }
            },
        )

    target_estado = SolicitudEstado.aprobada if payload.aprobada else SolicitudEstado.denegada
    validate_solicitud_transition(solicitud.estado, target_estado)

    if not payload.aprobada and not payload.motivo_negativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "MOTIVO_NEGATIVA_REQUIRED",
                    "message": "Es legalmente obligatorio fundamentar el motivo de la negativa",
                }
            },
        )

    now = datetime.datetime.now(datetime.UTC)
    solicitud.estado = target_estado
    solicitud.dictamen_dpd = payload.dictamen_dpd
    solicitud.excepcion_legal_aplicada = payload.excepcion_legal_aplicada
    solicitud.motivo_negativa = payload.motivo_negativa
    solicitud.fecha_resolucion = now
    solicitud.resuelto_por = current_user.id
    solicitud.updated_by = current_user.id

    if not payload.aprobada:
        # Si se deniega, la solicitud queda cerrada
        solicitud.fecha_cierre = now

    await log_audit(
        db=db,
        accion="RESOLVER_SOLICITUD",
        entidad="solicitud_derecho",
        entidad_id=solicitud.id,
        usuario=current_user,
        detalles={
            "aprobada": payload.aprobada,
            "estado": target_estado.value,
            "excepcion": payload.excepcion_legal_aplicada,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(solicitud)

    return _enrich_solicitud_response(solicitud)


@router.post("/{solicitud_id}/ejecutar", response_model=SolicitudDerechoResponse)
async def execute_solicitud_derecho(
    solicitud_id: uuid.UUID,
    payload: SolicitudEjecucionRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> SolicitudDerechoResponse:
    """
    Registra la ejecución técnica (bloqueo en 3d, borrado o rectificación) y concluye la atención.
    """
    stmt = (
        select(SolicitudDerecho)
        .options(selectinload(SolicitudDerecho.notificaciones_encargados))
        .where(SolicitudDerecho.id == solicitud_id)
    )
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(SolicitudDerecho.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()

    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SOLICITUD_NOT_FOUND",
                    "message": "Solicitud de derechos no encontrada",
                }
            },
        )

    now = datetime.datetime.now(datetime.UTC)
    solicitud.ejecucion_tecnica_completada = True
    solicitud.fecha_ejecucion = now
    solicitud.resultado_ejecucion = payload.resultado_ejecucion

    if payload.marcar_atendida:
        validate_solicitud_transition(solicitud.estado, SolicitudEstado.atendida)
        solicitud.estado = SolicitudEstado.atendida
        solicitud.fecha_cierre = now

    solicitud.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="EJECUTAR_SOLICITUD",
        entidad="solicitud_derecho",
        entidad_id=solicitud.id,
        usuario=current_user,
        detalles={"resultado": payload.resultado_ejecucion, "estado": solicitud.estado.value},
        request=request,
    )
    await db.commit()
    await db.refresh(solicitud)

    return _enrich_solicitud_response(solicitud)


@router.post(
    "/{solicitud_id}/notificar-encargados",
    response_model=NotificacionEncargadoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def notify_encargado(
    solicitud_id: uuid.UUID,
    payload: NotificacionEncargadoCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> NotificacionEncargadoResponse:
    """
    Emite una orden formal de replicación a un encargado del tratamiento (Art. 23 RGLOPDP).
    """
    stmt = select(SolicitudDerecho).where(SolicitudDerecho.id == solicitud_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(SolicitudDerecho.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()

    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SOLICITUD_NOT_FOUND",
                    "message": "Solicitud de derechos no encontrada",
                }
            },
        )

    now = datetime.datetime.now(datetime.UTC)
    notificacion = NotificacionEncargado(
        tenant_id=current_user.tenant_id,
        solicitud_id=solicitud.id,
        encargado_nombre=payload.encargado_nombre,
        encargado_email=payload.encargado_email,
        tipo_accion_requerida=payload.tipo_accion_requerida,
        instrucciones_tecnicas=payload.instrucciones_tecnicas,
        estado=NotificacionEstado.enviada,
        fecha_envio=now,
        created_by=current_user.id,
    )
    db.add(notificacion)

    if (
        solicitud.estado == SolicitudEstado.aprobada
        or solicitud.estado == SolicitudEstado.en_ejecucion
    ):
        solicitud.estado = SolicitudEstado.notificada_encargados

    await db.flush()

    await log_audit(
        db=db,
        accion="NOTIFICAR_ENCARGADO",
        entidad="notificacion_encargado",
        entidad_id=notificacion.id,
        usuario=current_user,
        detalles={"encargado": payload.encargado_nombre, "accion": payload.tipo_accion_requerida},
        request=request,
    )
    await db.commit()
    await db.refresh(notificacion)

    return NotificacionEncargadoResponse.model_validate(notificacion)


@router.get("/{solicitud_id}/exportar-portabilidad")
async def export_portabilidad_package(
    solicitud_id: uuid.UUID,
    formato: str = Query("json", description="Formato del archivo: 'json' o 'csv'"),
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
):
    """
    Genera y descarga el paquete estructurado y de lectura mecánica conforme al Art. 17 LOPDP.
    """
    stmt = select(SolicitudDerecho).where(SolicitudDerecho.id == solicitud_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(SolicitudDerecho.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()

    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SOLICITUD_NOT_FOUND",
                    "message": "Solicitud de derechos no encontrada",
                }
            },
        )

    datos = solicitud.datos_a_modificar or {
        "titular_nombre": solicitud.titular_nombre,
        "titular_identificacion": solicitud.titular_identificacion,
        "titular_email": solicitud.titular_email,
        "especificacion": solicitud.especificacion_datos,
    }

    filename, content_bytes, media_type = generar_paquete_portabilidad(solicitud, datos, formato)

    return Response(
        content=content_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
