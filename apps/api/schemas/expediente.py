"""
OS Privacidad — Schemas de Expediente
=====================================
Validación y serialización de expedientes documentales y probatorios.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.expediente import ExpedienteEstado


class ExpedienteBase(BaseModel):
    """Campos base de un expediente."""

    nombre: str = Field(..., min_length=3, max_length=255)
    descripcion: str | None = None
    caso_id: uuid.UUID | None = None
    cliente_id: uuid.UUID | None = None
    estado: ExpedienteEstado = ExpedienteEstado.activo


class ExpedienteCreate(ExpedienteBase):
    """Payload para crear un nuevo expediente."""

    pass


class ExpedienteUpdate(BaseModel):
    """Payload para actualizar un expediente."""

    nombre: str | None = Field(None, min_length=3, max_length=255)
    descripcion: str | None = None
    caso_id: uuid.UUID | None = None
    cliente_id: uuid.UUID | None = None
    estado: ExpedienteEstado | None = None


class ExpedienteResponse(BaseModel):
    """Respuesta con datos de un expediente."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    caso_id: uuid.UUID | None = None
    cliente_id: uuid.UUID | None = None
    nombre: str
    descripcion: str | None = None
    estado: ExpedienteEstado
    created_at: datetime
    updated_at: datetime
