"""
OS Privacidad — Schemas de Proceso (RAT)
========================================
Validación y serialización de actividades de tratamiento de datos personales.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProcesoBase(BaseModel):
    """Campos base de una actividad de tratamiento."""

    nombre: str = Field(..., min_length=2, max_length=255)
    descripcion: str | None = None
    area_responsable: str = Field(..., min_length=2, max_length=100)
    base_legal: str = Field(..., min_length=2, max_length=100)
    finalidad: str = Field(..., min_length=5)
    tipo_datos: dict[str, Any] | list[Any] | None = None
    cliente_id: uuid.UUID | None = None


class ProcesoCreate(ProcesoBase):
    """Payload para crear un nuevo proceso / RAT."""

    pass


class ProcesoUpdate(BaseModel):
    """Payload para actualizar datos de un proceso."""

    nombre: str | None = Field(None, min_length=2, max_length=255)
    descripcion: str | None = None
    area_responsable: str | None = Field(None, min_length=2, max_length=100)
    base_legal: str | None = Field(None, min_length=2, max_length=100)
    finalidad: str | None = Field(None, min_length=5)
    tipo_datos: dict[str, Any] | list[Any] | None = None
    cliente_id: uuid.UUID | None = None
    activo: bool | None = None


class ProcesoResponse(BaseModel):
    """Respuesta con datos de proceso."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    cliente_id: uuid.UUID | None = None
    nombre: str
    descripcion: str | None = None
    area_responsable: str
    base_legal: str
    finalidad: str
    tipo_datos: dict[str, Any] | list[Any] | None = None
    activo: bool
    created_at: datetime
    updated_at: datetime
