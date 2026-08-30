"""
OS Privacidad — Schemas de Medidas de Seguridad (Salvaguardas)
==============================================================
Validación y serialización del catálogo de controles de seguridad.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.medida_seguridad import MedidaEstado, MedidaTipo


class MedidaSeguridadBase(BaseModel):
    """Campos base de una medida de seguridad."""

    tipo: MedidaTipo
    nombre: str = Field(..., min_length=3, max_length=255)
    descripcion: str = Field(..., min_length=5)
    estado_implementacion: MedidaEstado = MedidaEstado.planificada
    responsable: str | None = Field(None, max_length=100)
    evidencia_url: str | None = None


class MedidaSeguridadCreate(MedidaSeguridadBase):
    """Payload para crear una nueva medida de seguridad."""

    pass


class MedidaSeguridadUpdate(BaseModel):
    """Payload para actualizar una medida de seguridad."""

    tipo: MedidaTipo | None = None
    nombre: str | None = Field(None, min_length=3, max_length=255)
    descripcion: str | None = Field(None, min_length=5)
    estado_implementacion: MedidaEstado | None = None
    responsable: str | None = None
    evidencia_url: str | None = None
    activo: bool | None = None


class MedidaSeguridadResponse(BaseModel):
    """Respuesta con datos de una medida de seguridad."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    tipo: MedidaTipo
    nombre: str
    descripcion: str
    estado_implementacion: MedidaEstado
    responsable: str | None = None
    evidencia_url: str | None = None
    activo: bool
    created_at: datetime
    updated_at: datetime
