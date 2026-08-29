"""
OS Privacidad — Modelo de Expediente
====================================
Contenedor documental y probatorio asociado a un Caso o Cliente.
Aislado por RLS mediante tenant_id.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.caso import Caso
    from models.cliente import Cliente


class ExpedienteEstado(enum.StrEnum):
    """Estados del ciclo de vida de un expediente."""

    activo = "activo"
    archivado = "archivado"
    cerrado = "cerrado"


class Expediente(Base, TimestampMixin):
    """
    Representa un expediente documental/jurídico.
    Posee código correlativo único por tenant (ej. EXP-2026-0001).
    """

    __tablename__ = "expedientes"
    __table_args__ = (UniqueConstraint("tenant_id", "codigo", name="uq_expedientes_tenant_codigo"),)

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

    caso_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("casos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    descripcion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    estado: Mapped[ExpedienteEstado] = mapped_column(
        Enum(ExpedienteEstado, name="expediente_estado", native_enum=False),
        default=ExpedienteEstado.activo,
        nullable=False,
    )

    # Relaciones
    caso: Mapped[Caso | None] = relationship("Caso", back_populates="expedientes")
    cliente: Mapped[Cliente | None] = relationship("Cliente")
