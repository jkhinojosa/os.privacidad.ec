"""
OS Privacidad — Schemas de Autenticación
========================================
Modelos Pydantic para login, refresh, profile y tokens.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from models.usuario import UserRole


class LoginRequest(BaseModel):
    """Payload para iniciar sesión."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Respuesta con token de acceso JWT."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfileResponse(BaseModel):
    """Perfil del usuario autenticado."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    nombre: str
    apellido: str
    rol: UserRole
    tenant_id: uuid.UUID | None = None
    cliente_id: uuid.UUID | None = None
    activo: bool


class AuthResponse(BaseModel):
    """Respuesta completa de login conteniendo token y perfil de usuario."""
    token: TokenResponse
    user: UserProfileResponse


class RefreshTokenRequest(BaseModel):
    """Opcional si no se usan cookies (para clientes API directos)."""
    refresh_token: str | None = None
