"""
OS Privacidad — Schemas de Riesgo
=================================
Validación y serialización de riesgos y matriz de calor de derechos y libertades.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.riesgo import RiesgoDimension, RiesgoEstado, RiesgoNivel
from schemas.medida_seguridad import MedidaSeguridadResponse


class RiesgoBase(BaseModel):
    """Campos base de un escenario de riesgo."""

    proceso_id: uuid.UUID | None = None
    nombre: str = Field(..., min_length=3, max_length=255)
    descripcion_amenaza: str = Field(..., min_length=5)
    vulnerabilidad: str = Field(..., min_length=5)
    dimension_afectada: RiesgoDimension = RiesgoDimension.confidencialidad
    es_grupo_vulnerable: bool = False
    probabilidad_inherente: int = Field(3, ge=1, le=5, description="Escala de probabilidad 1 a 5")
    impacto_inherente: int = Field(3, ge=1, le=5, description="Escala de impacto 1 a 5")


class RiesgoCreate(RiesgoBase):
    """Payload para crear un nuevo riesgo."""

    medidas_ids: list[uuid.UUID] | None = None


class RiesgoUpdate(BaseModel):
    """Payload para actualizar datos descriptivos de un riesgo."""

    proceso_id: uuid.UUID | None = None
    nombre: str | None = Field(None, min_length=3, max_length=255)
    descripcion_amenaza: str | None = Field(None, min_length=5)
    vulnerabilidad: str | None = Field(None, min_length=5)
    dimension_afectada: RiesgoDimension | None = None
    es_grupo_vulnerable: bool | None = None
    probabilidad_inherente: int | None = Field(None, ge=1, le=5)
    impacto_inherente: int | None = Field(None, ge=1, le=5)
    estado: RiesgoEstado | None = None


class RiesgoMitigacionRequest(BaseModel):
    """Payload para aplicar salvaguardas y recalcular riesgo residual."""

    medidas_ids: list[uuid.UUID] = Field(
        ..., min_length=1, description="Lista de IDs de medidas aplicadas"
    )
    probabilidad_residual: int = Field(..., ge=1, le=5)
    impacto_residual: int = Field(..., ge=1, le=5)
    estado: RiesgoEstado = RiesgoEstado.mitigado


class RiesgoResponse(BaseModel):
    """Respuesta con datos completos del riesgo y medidas asociadas."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    proceso_id: uuid.UUID | None = None
    nombre: str
    descripcion_amenaza: str
    vulnerabilidad: str
    dimension_afectada: RiesgoDimension
    es_grupo_vulnerable: bool

    # Riesgo Inherente
    probabilidad_inherente: int
    impacto_inherente: int
    riesgo_inherente_score: float
    nivel_riesgo_inherente: RiesgoNivel

    # Riesgo Residual
    probabilidad_residual: int | None = None
    impacto_residual: int | None = None
    riesgo_residual_score: float | None = None
    nivel_riesgo_residual: RiesgoNivel | None = None

    estado: RiesgoEstado
    medidas: list[MedidaSeguridadResponse] = []
    created_at: datetime
    updated_at: datetime


class MatrizCalorCelda(BaseModel):
    """Celda de la matriz 5x5 de calor de riesgos."""

    probabilidad: int
    impacto: int
    cantidad_inherente: int = 0
    cantidad_residual: int = 0
    riesgos_ids: list[uuid.UUID] = []


class MatrizCalorResponse(BaseModel):
    """Estructura completa de la matriz de calor para visualización en frontend."""

    total_riesgos: int
    resumen_inherente: dict[str, int]
    resumen_residual: dict[str, int]
    matriz: list[MatrizCalorCelda]
