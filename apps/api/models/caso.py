"""
OS Privacidad — Modelo de Caso
==============================
Gestión de incidentes de seguridad, ejercicio de derechos ARCO y consultas normativas.
Incluye soporte para máquina de estados y código correlativo secuencial.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.cliente import Cliente
    from models.expediente import Expediente
    from models.proceso import Proceso
    from models.usuario import Usuario


class CasoTipo(enum.StrEnum):
    """Tipos de caso admitidos en la plataforma."""

    incidente_seguridad = "incidente_seguridad"
    derecho_arco = "derecho_arco"
    consulta_regulatoria = "consulta_regulatoria"
    auditoria = "auditoria"
    otro = "otro"


class CasoPrioridad(enum.StrEnum):
    """Niveles de prioridad de atención."""

    baja = "baja"
    media = "media"
    alta = "alta"
    critica = "critica"


class CasoEstado(enum.StrEnum):
    """Estados del ciclo de vida de un caso (Máquina de Estados 3.1)."""

    abierto = "abierto"
    en_investigacion = "en_investigacion"
    en_comite = "en_comite"
    cerrado = "cerrado"
    reabierto = "reabierto"


class Caso(Base, TimestampMixin):
    """
    Representa un caso operativo (incidente, derecho ARCO, etc.).
    Posee código correlativo único por tenant (ej. CAS-2026-0001).
    """

    __tablename__ = "casos"
    __table_args__ = (UniqueConstraint("tenant_id", "codigo", name="uq_casos_tenant_codigo"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    codigo: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    proceso_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procesos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    asignado_a: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    titulo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    descripcion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    tipo: Mapped[CasoTipo] = mapped_column(
        Enum(CasoTipo, name="caso_tipo", native_enum=False),
        default=CasoTipo.otro,
        nullable=False,
    )

    prioridad: Mapped[CasoPrioridad] = mapped_column(
        Enum(CasoPrioridad, name="caso_prioridad", native_enum=False),
        default=CasoPrioridad.media,
        nullable=False,
    )

    estado: Mapped[CasoEstado] = mapped_column(
        Enum(CasoEstado, name="caso_estado", native_enum=False),
        default=CasoEstado.abierto,
        nullable=False,
        index=True,
    )

    fecha_limite: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    fecha_cierre: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolucion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relaciones
    cliente: Mapped[Cliente | None] = relationship("Cliente")
    proceso: Mapped[Proceso | None] = relationship("Proceso", back_populates="casos")
    asignado: Mapped[Usuario | None] = relationship("Usuario")
    expedientes: Mapped[list[Expediente]] = relationship("Expediente", back_populates="caso")
