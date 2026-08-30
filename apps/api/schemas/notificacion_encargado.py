"""
OS Privacidad — Schemas de Notificación a Encargados (Art. 23 RGLOPDP)
======================================================================
Validación y serialización de comunicaciones vinculantes enviadas a proveedores tecnológicos.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.notificacion_encargado import NotificacionEstado


class NotificacionEncargadoBase(BaseModel):
    """Campos base de una orden de réplica a un encargado."""

    encargado_nombre: str = Field(..., min_length=2, max_length=255)
    encargado_email: EmailStr
    tipo_accion_requerida: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="rectificar, actualizar, suprimir, suspender, oponerse",
    )
    instrucciones_tecnicas: str = Field(..., min_length=10)


class NotificacionEncargadoCreate(NotificacionEncargadoBase):
    """Payload para enviar orden a un encargado."""

    pass


class NotificacionEncargadoConfirmacion(BaseModel):
    """Payload para registrar confirmación de ejecución del encargado."""

    estado: NotificacionEstado = NotificacionEstado.ejecutada
    evidencia_respuesta: str = Field(
        ..., min_length=5, description="Constancia o certificado de ejecución técnica"
    )


class NotificacionEncargadoResponse(BaseModel):
    """Respuesta con datos de la notificación al encargado."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    solicitud_id: uuid.UUID
    encargado_nombre: str
    encargado_email: str
    tipo_accion_requerida: str
    instrucciones_tecnicas: str
    estado: NotificacionEstado
    fecha_envio: datetime
    fecha_confirmacion: datetime | None = None
    evidencia_respuesta: str | None = None
    created_at: datetime
    updated_at: datetime
