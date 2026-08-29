"""
OS Privacidad — Exportación de Schemas Pydantic
===============================================
"""

from schemas.audit_log import AuditLogResponse
from schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserProfileResponse,
)
from schemas.caso import (
    CasoCreate,
    CasoResponse,
    CasoTransitionRequest,
    CasoUpdate,
)
from schemas.cliente import ClienteCreate, ClienteResponse, ClienteUpdate
from schemas.expediente import (
    ExpedienteCreate,
    ExpedienteResponse,
    ExpedienteUpdate,
)
from schemas.proceso import ProcesoCreate, ProcesoResponse, ProcesoUpdate
from schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from schemas.usuario import (
    PasswordChangeRequest,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "UserProfileResponse",
    "AuthResponse",
    "RefreshTokenRequest",
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "ClienteCreate",
    "ClienteUpdate",
    "ClienteResponse",
    "UsuarioCreate",
    "UsuarioUpdate",
    "UsuarioResponse",
    "PasswordChangeRequest",
    "AuditLogResponse",
    "ProcesoCreate",
    "ProcesoUpdate",
    "ProcesoResponse",
    "CasoCreate",
    "CasoUpdate",
    "CasoTransitionRequest",
    "CasoResponse",
    "ExpedienteCreate",
    "ExpedienteUpdate",
    "ExpedienteResponse",
]
