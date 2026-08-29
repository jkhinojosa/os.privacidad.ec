"""
OS Privacidad — Schemas de Usuario
==================================
Validación y serialización de usuarios del sistema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.usuario import UserRole


class UsuarioBase(BaseModel):
    """Campos base de un usuario."""
    email: EmailStr
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    rol: UserRole = UserRole.analista
    cliente_id: uuid.UUID | None = None


class UsuarioCreate(UsuarioBase):
    """Payload para registrar o invitar a un nuevo usuario."""
    password: str = Field(..., min_length=8, max_length=100)


class UsuarioUpdate(BaseModel):
    """Payload para actualizar datos de un usuario."""
    nombre: str | None = Field(None, min_length=2, max_length=100)
    apellido: str | None = Field(None, min_length=2, max_length=100)
    rol: UserRole | None = None
    cliente_id: uuid.UUID | None = None
    activo: bool | None = None


class UsuarioResponse(BaseModel):
    """Respuesta con datos de usuario."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID | None = None
    email: str
    nombre: str
    apellido: str
    rol: UserRole
    cliente_id: uuid.UUID | None = None
    activo: bool
    created_at: datetime
    updated_at: datetime


class PasswordChangeRequest(BaseModel):
    """Payload para cambio de contraseña."""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
