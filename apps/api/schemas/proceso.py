"""
OS Privacidad — Schemas de Proceso (RAT)
========================================
Validación y serialización de actividades de tratamiento con los 9 atributos del RGLOPDP Art. 38 y MTGE.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from models.proceso import FrecuenciaTratamiento


class ProcesoBase(BaseModel):
    """Campos base de una actividad de tratamiento (RAT)."""
    nombre: str = Field(..., min_length=2, max_length=255)
    descripcion: str | None = None
    area_responsable: str = Field(..., min_length=2, max_length=100)
    base_legal: str = Field(..., min_length=2, max_length=100)
    finalidad: str = Field(..., min_length=5)
    tipo_datos: dict[str, Any] | list[Any] | None = None
    cliente_id: uuid.UUID | None = None

    # Atributos RAT / MTGE
    destinatarios: dict[str, Any] | list[Any] | None = None
    colectivos_titulares: dict[str, Any] | list[Any] | None = None
    tiene_perfiles: bool = False
    transferencia_internacional: bool = False
    paises_transferencia: dict[str, Any] | list[Any] | None = None
    garantias_transferencia: str | None = None
    plazo_conservacion: str | None = None
    frecuencia_tratamiento: FrecuenciaTratamiento = FrecuenciaTratamiento.continua
    permanencia_tratamiento: str = "indefinida"
    volumen_titulares_estimado: int | None = None


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
    destinatarios: dict[str, Any] | list[Any] | None = None
    colectivos_titulares: dict[str, Any] | list[Any] | None = None
    tiene_perfiles: bool | None = None
    transferencia_internacional: bool | None = None
    paises_transferencia: dict[str, Any] | list[Any] | None = None
    garantias_transferencia: str | None = None
    plazo_conservacion: str | None = None
    frecuencia_tratamiento: FrecuenciaTratamiento | None = None
    permanencia_tratamiento: str | None = None
    volumen_titulares_estimado: int | None = None
    activo: bool | None = None


class ProcesoResponse(BaseModel):
    """Respuesta con datos completos del proceso RAT y evaluación de Gran Escala."""
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
    destinatarios: dict[str, Any] | list[Any] | None = None
    colectivos_titulares: dict[str, Any] | list[Any] | None = None
    tiene_perfiles: bool
    transferencia_internacional: bool
    paises_transferencia: dict[str, Any] | list[Any] | None = None
    garantias_transferencia: str | None = None
    plazo_conservacion: str | None = None
    frecuencia_tratamiento: str
    permanencia_tratamiento: str
    volumen_titulares_estimado: int | None = None
    puntaje_mtge: float
    requiere_eipd: bool
    activo: bool
    created_at: datetime
    updated_at: datetime
