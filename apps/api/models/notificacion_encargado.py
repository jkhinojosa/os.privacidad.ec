"""
OS Privacidad — Modelo de Notificación a Encargados del Tratamiento (Art. 23 RGLOPDP)
======================================================================================
Permite registrar y auditar la réplica obligatoria de las solicitudes de derechos
(rectificación, actualización, oposición, supresión o suspensión) hacia los encargados.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.solicitud_derecho import SolicitudDerecho


class NotificacionEstado(enum.StrEnum):
    """Estados del proceso de notificación y confirmación del encargado."""
    enviada = "enviada"
    confirmada_recibida = "confirmada_recibida"
    ejecutada = "ejecutada"


class NotificacionEncargado(Base, TimestampMixin):
    """
    Representa una orden formal de replicación enviada a un encargado del tratamiento.
    """
    __tablename__ = "notificaciones_encargados"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    solicitud_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("solicitudes_derechos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    encargado_nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Nombre o razón social del encargado o proveedor tecnológico",
    )

    encargado_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    tipo_accion_requerida: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Ej. rectificar, actualizar, suprimir, suspender, oponerse",
    )

    instrucciones_tecnicas: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Instrucciones precisas para la réplica en las bases de datos del encargado",
    )

    estado: Mapped[NotificacionEstado] = mapped_column(
        Enum(NotificacionEstado, name="notificacion_estado", native_enum=False),
        default=NotificacionEstado.enviada,
        nullable=False,
        index=True,
    )

    fecha_envio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    fecha_confirmacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    evidencia_respuesta: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Confirmación o certificado de ejecución emitido por el encargado",
    )

    # Relación
    solicitud: Mapped[SolicitudDerecho] = relationship("SolicitudDerecho", back_populates="notificaciones_encargados")
