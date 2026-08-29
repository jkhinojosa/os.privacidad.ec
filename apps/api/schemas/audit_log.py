"""
OS Privacidad — Schemas de Audit Log
====================================
Serialización de registros de bitácora de auditoría.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Respuesta con registro de auditoría."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID | None = None
    usuario_id: uuid.UUID | None = None
    accion: str
    entidad: str
    entidad_id: uuid.UUID | None = None
    detalles: dict[str, Any] | None = None
    ip_address: str | None = None
    created_at: datetime
