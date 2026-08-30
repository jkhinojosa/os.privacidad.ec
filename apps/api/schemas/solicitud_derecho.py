"""
OS Privacidad — Schemas de Solicitud de Derechos del Titular (LOPDP)
====================================================================
Validación y serialización de requerimientos de ejercicio de derechos, SLA y resolución.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.solicitud_derecho import CanalRecepcion, DerechoTipo, SolicitudEstado
from schemas.notificacion_encargado import NotificacionEncargadoResponse


class SolicitudDerechoBase(BaseModel):
    """Campos base para la recepción de una solicitud de derechos."""

    cliente_id: uuid.UUID | None = None
    proceso_id: uuid.UUID | None = None
    tipo_derecho: DerechoTipo
    canal_recepcion: CanalRecepcion = CanalRecepcion.formulario_web

    # Datos del Titular
    titular_nombre: str = Field(..., min_length=3, max_length=255)
    titular_identificacion: str = Field(
        ..., min_length=5, max_length=50, description="Cédula / RUC / Pasaporte"
    )
    titular_email: EmailStr
    titular_telefono: str | None = None

    # Representación
    es_representante: bool = False
    representante_nombre: str | None = None
    representante_identificacion: str | None = None
    documento_acreditacion_url: str | None = None

    # Contenido
    motivo_solicitud: str = Field(..., min_length=10)
    especificacion_datos: str | None = None
    datos_a_modificar: dict[str, Any] | list[Any] | None = None


class SolicitudDerechoCreate(SolicitudDerechoBase):
    """Payload para registrar una nueva solicitud de ejercicio de derechos."""

    pass


class SolicitudDerechoUpdate(BaseModel):
    """Payload para actualizar datos administrativos de una solicitud."""

    asignado_a: uuid.UUID | None = None
    proceso_id: uuid.UUID | None = None
    cliente_id: uuid.UUID | None = None
    especificacion_datos: str | None = None
    datos_a_modificar: dict[str, Any] | list[Any] | None = None


class SolicitudSubsanacionRequest(BaseModel):
    """Payload para requerir subsanación al titular (Art. 14 RGLOPDP)."""

    motivo_subsanacion: str = Field(
        ...,
        min_length=10,
        description="Motivo por el cual la solicitud está incompleta o imprecisa",
    )
    dias_plazo_titular: int = Field(
        10, ge=1, le=15, description="Plazo otorgado al titular para subsanar (máx 10d)"
    )


class SolicitudProrrogaRequest(BaseModel):
    """Payload para aplicar prórroga excepcional de 15 días hábiles."""

    motivo_prorroga: str = Field(
        ..., min_length=15, description="Justificación técnica de la complejidad de la solicitud"
    )
    dias_prorroga_habiles: int = Field(15, ge=1, le=15)


class SolicitudResolucionRequest(BaseModel):
    """Payload para resolver la solicitud (Aprobar o Denegar motivadamente)."""

    aprobada: bool = Field(..., description="True si procede el derecho, False si se deniega")
    dictamen_dpd: str = Field(
        ..., min_length=10, description="Criterio técnico-jurídico vinculante emitido por el DPD"
    )
    excepcion_legal_aplicada: str | None = Field(
        None, description="En caso de negativa, especificar excepción del Art. 18 LOPDP"
    )
    motivo_negativa: str | None = Field(
        None, description="Fundamentación jurídica en caso de denegación total o parcial"
    )


class SolicitudEjecucionRequest(BaseModel):
    """Payload para registrar la ejecución técnica y cierre de la solicitud."""

    resultado_ejecucion: str = Field(
        ..., min_length=10, description="Detalle del borrado, rectificación, bloqueo o entrega"
    )
    marcar_atendida: bool = True


class SolicitudDerechoResponse(BaseModel):
    """Respuesta con datos completos de la solicitud y estado de SLA."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    cliente_id: uuid.UUID | None = None
    proceso_id: uuid.UUID | None = None
    asignado_a: uuid.UUID | None = None

    tipo_derecho: DerechoTipo
    canal_recepcion: CanalRecepcion
    estado: SolicitudEstado

    titular_nombre: str
    titular_identificacion: str
    titular_email: str
    titular_telefono: str | None = None
    es_representante: bool
    representante_nombre: str | None = None
    representante_identificacion: str | None = None
    documento_acreditacion_url: str | None = None

    motivo_solicitud: str
    especificacion_datos: str | None = None
    datos_a_modificar: dict[str, Any] | list[Any] | None = None

    fecha_recepcion: datetime
    fecha_limite_sla: datetime
    fecha_subsanacion_limite: datetime | None = None
    prorroga_aplicada: bool
    fecha_prorroga: datetime | None = None
    dias_prorroga: int
    motivo_prorroga: str | None = None

    dictamen_dpd: str | None = None
    excepcion_legal_aplicada: str | None = None
    motivo_negativa: str | None = None
    fecha_resolucion: datetime | None = None
    resuelto_por: uuid.UUID | None = None

    ejecucion_tecnica_completada: bool
    fecha_ejecucion: datetime | None = None
    resultado_ejecucion: str | None = None
    fecha_cierre: datetime | None = None

    # Diagnóstico SLA dinámico
    dias_restantes_habiles: int | None = None
    estado_semaforo: str | None = None

    notificaciones_encargados: list[NotificacionEncargadoResponse] = []
    created_at: datetime
    updated_at: datetime


class SolicitudResumenSLAResponse(BaseModel):
    """Métricas consolidadas de cumplimiento de plazos LOPDP."""

    total_solicitudes: int
    en_tiempo: int
    en_alerta: int
    vencidas: int
    atendidas_a_tiempo: int
    porcentaje_cumplimiento: float
