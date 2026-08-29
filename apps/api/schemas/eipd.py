"""
OS Privacidad — Schemas de Evaluación de Impacto (EIPD / PIA)
=============================================================
Validación y serialización de informes oficiales EIPD conforme al Art. 32 RGLOPDP.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.eipd import EIPDEstado
from schemas.proceso import ProcesoResponse
from schemas.riesgo import RiesgoResponse


class EIPDBase(BaseModel):
    """Campos base de un informe EIPD."""
    proceso_id: uuid.UUID
    titulo: str = Field(..., min_length=5, max_length=255)
    descripcion_sistematica: str = Field(
        ..., min_length=20, description="Descripción sistemática de operaciones y finalidades"
    )
    justificacion_necesidad_proporcionalidad: str = Field(
        ..., min_length=20, description="Evaluación de necesidad y proporcionalidad de los datos"
    )
    opinion_titulares_consultados: str | None = None


class EIPDCreate(EIPDBase):
    """Payload para crear un borrador de EIPD."""
    pass


class EIPDUpdate(BaseModel):
    """Payload para actualizar el borrador de una EIPD."""
    titulo: str | None = Field(None, min_length=5, max_length=255)
    descripcion_sistematica: str | None = Field(None, min_length=20)
    justificacion_necesidad_proporcionalidad: str | None = Field(None, min_length=20)
    opinion_titulares_consultados: str | None = None


class EIPDAprobacionRequest(BaseModel):
    """Payload para emitir dictamen y aprobar la EIPD por el DPD."""
    dictamen_dpd: str = Field(..., min_length=10, description="Criterio técnico vinculante del DPD")
    nuevo_estado: EIPDEstado = EIPDEstado.aprobada


class EIPDResponse(BaseModel):
    """Respuesta con datos de la evaluación de impacto."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    proceso_id: uuid.UUID
    titulo: str
    descripcion_sistematica: str
    justificacion_necesidad_proporcionalidad: str
    dictamen_dpd: str | None = None
    opinion_titulares_consultados: str | None = None
    estado: EIPDEstado
    fecha_aprobacion: datetime | None = None
    aprobado_por: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class EIPDReporteOficialResponse(BaseModel):
    """Informe consolidado de EIPD listo para presentación ante la SPDP."""
    eipd: EIPDResponse
    proceso: ProcesoResponse
    riesgos_asociados: list[RiesgoResponse]
    resumen_cumplimiento_lopdp: str
    fecha_generacion: datetime
