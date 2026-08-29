"""
OS Privacidad — Schemas de Cliente
==================================
Validación y serialización de empresas/clientes.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClienteBase(BaseModel):
    """Campos base de un cliente."""

    nombre_razon_social: str = Field(..., min_length=2, max_length=255)
    ruc: str = Field(..., min_length=10, max_length=13, pattern=r"^\d{10,13}$")
    sector: str | None = Field(None, max_length=100)
    contacto_principal_nombre: str = Field(..., min_length=2, max_length=255)
    contacto_principal_email: EmailStr


class ClienteCreate(ClienteBase):
    """Payload para crear un nuevo cliente."""

    pass


class ClienteUpdate(BaseModel):
    """Payload para actualizar datos de un cliente."""

    nombre_razon_social: str | None = Field(None, min_length=2, max_length=255)
    sector: str | None = Field(None, max_length=100)
    contacto_principal_nombre: str | None = Field(None, min_length=2, max_length=255)
    contacto_principal_email: EmailStr | None = None
    activo: bool | None = None


class ClienteResponse(BaseModel):
    """Respuesta con datos de cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    nombre_razon_social: str
    ruc: str
    sector: str | None = None
    contacto_principal_nombre: str
    contacto_principal_email: str
    activo: bool
    created_at: datetime
    updated_at: datetime
