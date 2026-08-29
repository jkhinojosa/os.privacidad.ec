"""
OS Privacidad — Schemas de Caso
===============================
Validación y serialización de incidentes, consultas y solicitudes ARCO.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.caso import CasoEstado, CasoPrioridad, CasoTipo


class CasoBase(BaseModel):
    """Campos base para la creación de un caso."""

    titulo: str = Field(..., min_length=3, max_length=255)
    descripcion: str = Field(..., min_length=5)
    tipo: CasoTipo = CasoTipo.otro
    prioridad: CasoPrioridad = CasoPrioridad.media
    cliente_id: uuid.UUID | None = None
    proceso_id: uuid.UUID | None = None
    asignado_a: uuid.UUID | None = None
    fecha_limite: datetime | None = None


class CasoCreate(CasoBase):
    """Payload para crear un nuevo caso."""

    pass


class CasoUpdate(BaseModel):
    """Payload para actualizar datos generales de un caso (no cambia estado)."""

    titulo: str | None = Field(None, min_length=3, max_length=255)
    descripcion: str | None = Field(None, min_length=5)
    tipo: CasoTipo | None = None
    prioridad: CasoPrioridad | None = None
    cliente_id: uuid.UUID | None = None
    proceso_id: uuid.UUID | None = None
    asignado_a: uuid.UUID | None = None
    fecha_limite: datetime | None = None
    resolucion: str | None = None


class CasoTransitionRequest(BaseModel):
    """Payload para ejecutar una transición en la máquina de estados."""

    nuevo_estado: CasoEstado
    motivo: str = Field(
        ..., min_length=3, max_length=500, description="Justificación del cambio de estado"
    )
    resolucion: str | None = Field(None, description="Resolución final en caso de cierre")


class CasoResponse(BaseModel):
    """Respuesta completa con datos de un caso."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    cliente_id: uuid.UUID | None = None
    proceso_id: uuid.UUID | None = None
    asignado_a: uuid.UUID | None = None
    titulo: str
    descripcion: str
    tipo: CasoTipo
    prioridad: CasoPrioridad
    estado: CasoEstado
    fecha_limite: datetime | None = None
    fecha_cierre: datetime | None = None
    resolucion: str | None = None
    created_at: datetime
    updated_at: datetime
