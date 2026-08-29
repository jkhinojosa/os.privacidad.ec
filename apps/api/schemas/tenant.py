"""
OS Privacidad — Schemas de Tenant
=================================
Validación y serialización de organizaciones.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.tenant import TenantPlan


class TenantBase(BaseModel):
    """Campos base de una organización."""
    nombre: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    plan: TenantPlan = TenantPlan.community


class TenantCreate(TenantBase):
    """Payload para crear un nuevo tenant."""
    pass


class TenantUpdate(BaseModel):
    """Payload para actualizar datos de un tenant existente."""
    nombre: str | None = Field(None, min_length=2, max_length=255)
    plan: TenantPlan | None = None
    activo: bool | None = None


class TenantResponse(BaseModel):
    """Respuesta con datos completos del tenant."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    slug: str
    plan: TenantPlan
    activo: bool
    created_at: datetime
    updated_at: datetime
