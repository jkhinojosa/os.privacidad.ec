"""
OS Privacidad — Schemas de Vulneración de Seguridad (Brechas de Datos LOPDP)
============================================================================
Validación y serialización de incidentes, notificación oficial a SPDP/ARCOTEL y titulares.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from models.brecha_seguridad import BrechaEstado, BrechaSeveridad, VulnerabilidadTipo


class BrechaSeguridadBase(BaseModel):
    """Campos base de un incidente o vulneración de seguridad."""

    caso_id: uuid.UUID | None = None
    proceso_id: uuid.UUID | None = None
    titulo: str = Field(..., min_length=5, max_length=255)
    descripcion: str = Field(..., min_length=15)
    tipo_vulneracion: VulnerabilidadTipo = VulnerabilidadTipo.confidencialidad
    severidad: BrechaSeveridad = BrechaSeveridad.alta

    sistemas_afectados: str = Field(
        ..., min_length=5, description="Servidores, bases de datos o plataformas"
    )
    causa_presunta: str = Field(
        ..., min_length=5, description="Hipótesis técnica de la explotación"
    )
    colectivos_afectados: dict[str, Any] | list[Any] | None = None
    volumen_titulares_estimado: int = Field(0, ge=0)
    categorias_datos_expuestas: dict[str, Any] | list[Any] | None = None

    medidas_contencion_inmediatas: str = Field(..., min_length=10)
    medidas_remediacion_previstas: str = Field(..., min_length=10)


class BrechaSeguridadCreate(BrechaSeguridadBase):
    """Payload para registrar una nueva vulneración de seguridad."""

    pass


class BrechaSeguridadUpdate(BaseModel):
    """Payload para actualizar datos descriptivos o técnicos del incidente."""

    titulo: str | None = Field(None, min_length=5, max_length=255)
    descripcion: str | None = Field(None, min_length=15)
    tipo_vulneracion: VulnerabilidadTipo | None = None
    severidad: BrechaSeveridad | None = None
    sistemas_afectados: str | None = None
    causa_presunta: str | None = None
    colectivos_afectados: dict[str, Any] | list[Any] | None = None
    volumen_titulares_estimado: int | None = None
    categorias_datos_expuestas: dict[str, Any] | list[Any] | None = None
    medidas_contencion_inmediatas: str | None = None
    medidas_remediacion_previstas: str | None = None


class BrechaCalificacionRiesgoRequest(BaseModel):
    """Dictamen técnico del DPD sobre impacto a derechos y libertades de titulares."""

    evaluacion_riesgo_titulares: str = Field(..., min_length=15)
    dictamen_dpd: str = Field(..., min_length=15)
    conlleva_riesgo_titulares: bool = Field(
        ..., description="Si es True, activa plazo perentorio de 3 días para notificar titulares"
    )


class BrechaNotificacionSPDPRequest(BaseModel):
    """Payload para asentar la notificación formal a la SPDP y ARCOTEL (Art. 43 LOPDP)."""

    numero_radicado_spdp: str | None = Field(
        None, max_length=100, description="Número de trámite o radicado oficial"
    )
    notificada_a_arcotel: bool = True
    justificacion_dilacion: str | None = Field(
        None,
        description="Obligatoria si la notificación se efectúa fuera del término de 5 días hábiles",
    )


class BrechaNotificacionTitularesRequest(BaseModel):
    """Payload para asentar la notificación a los titulares afectados (Art. 46 LOPDP)."""

    canal_notificacion: str = Field(..., description="correo_individual, portal_web_masivo, prensa")
    excepcion_aplicada: str | None = Field(
        None, description="cifrado_previo, mitigacion_inmediata, esfuerzo_desproporcionado"
    )
    justificacion_excepcion: str | None = Field(
        None, description="Motivación para informe ante SPDP"
    )


class BrechaCierreRequest(BaseModel):
    """Payload para dar por resuelto y cerrado el incidente de brecha."""

    resultado_final_remediacion: str = Field(..., min_length=15)


class BrechaSeguridadResponse(BaseModel):
    """Respuesta con datos completos de la brecha y estado de SLA ante SPDP y Titulares."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    caso_id: uuid.UUID | None = None
    proceso_id: uuid.UUID | None = None

    titulo: str
    descripcion: str
    tipo_vulneracion: VulnerabilidadTipo
    severidad: BrechaSeveridad
    estado: BrechaEstado

    sistemas_afectados: str
    causa_presunta: str
    colectivos_afectados: dict[str, Any] | list[Any] | None = None
    volumen_titulares_estimado: int
    categorias_datos_expuestas: dict[str, Any] | list[Any] | None = None

    # Plazos SPDP (5d)
    fecha_deteccion: datetime
    fecha_limite_spdp: datetime
    notificada_a_spdp: bool
    fecha_notificacion_spdp: datetime | None = None
    numero_radicado_spdp: str | None = None
    notificada_a_arcotel: bool
    justificacion_dilacion: str | None = None

    # Plazos Titulares (3d)
    requiere_notificacion_titulares: bool
    fecha_calificacion_riesgo: datetime | None = None
    fecha_limite_titulares: datetime | None = None
    notificada_a_titulares: bool
    fecha_notificacion_titulares: datetime | None = None
    canal_notificacion_titulares: str | None = None
    excepcion_titulares_aplicada: str | None = None
    justificacion_excepcion_titulares: str | None = None

    # Medidas y Dictamen
    medidas_contencion_inmediatas: str
    medidas_remediacion_previstas: str
    dictamen_dpd: str | None = None
    evaluacion_riesgo_titulares: str | None = None
    fecha_cierre: datetime | None = None

    # Diagnóstico dinámico
    dias_restantes_spdp: int | None = None
    estado_semaforo_spdp: str | None = None
    dias_restantes_titulares: int | None = None
    estado_semaforo_titulares: str | None = None

    created_at: datetime
    updated_at: datetime


class BrechaInformeOficialSPDPResponse(BaseModel):
    """Informe oficial estructurado conforme al Art. 26 del Reglamento General LOPDP."""

    codigo: str
    titulo: str
    tipo_vulneracion: str
    severidad: str
    volumen_titulares: int
    fecha_deteccion: str
    fecha_limite_spdp: str
    notificada_a_spdp: bool
    informe_markdown: str
    generado_en: str


class BrechaResumenSLAResponse(BaseModel):
    """Métricas de cumplimiento de los plazos perentorios de brechas ante la SPDP."""

    total_brechas: int
    spdp_en_tiempo: int
    spdp_en_alerta: int
    spdp_vencidas: int
    notificadas_a_spdp: int
    notificadas_a_titulares: int
    porcentaje_cumplimiento_spdp: float
