"""
OS Privacidad — Modelo de Audit Log
===================================
Registro inmutable de auditoría para trazabilidad de acciones y cumplimiento normativo.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.tenant import Tenant
    from models.usuario import Usuario


class AuditLog(Base):
    """
    Bitácora de auditoría inmutable de todas las acciones críticas en la plataforma.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    accion: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    entidad: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    entidad_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    detalles: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        default=lambda: datetime.now(UTC),
        index=True,
    )

    # Relaciones
    tenant: Mapped[Tenant | None] = relationship(
        "Tenant",
        back_populates="audit_logs",
    )

    usuario: Mapped[Usuario | None] = relationship(
        "Usuario",
        back_populates="audit_logs",
    )
