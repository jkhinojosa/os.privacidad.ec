"""
OS Privacidad — Modelo de Cliente
=================================
Entidad Cliente dentro de un Tenant.
Aislado por RLS mediante tenant_id.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.tenant import Tenant
    from models.usuario import Usuario


class Cliente(Base, TimestampMixin):
    """
    Representa una empresa o cliente gestionado dentro del Tenant.
    Posee constraint único de (tenant_id, ruc).
    """

    __tablename__ = "clientes"
    __table_args__ = (UniqueConstraint("tenant_id", "ruc", name="uq_clientes_tenant_ruc"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nombre_razon_social: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ruc: Mapped[str] = mapped_column(
        String(13),
        nullable=False,
        index=True,
    )

    sector: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    contacto_principal_nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    contacto_principal_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relaciones
    tenant: Mapped[Tenant] = relationship(
        "Tenant",
        back_populates="clientes",
    )

    usuarios: Mapped[list[Usuario]] = relationship(
        "Usuario",
        back_populates="cliente",
    )
