"""
OS Privacidad — Modelo de Tenant (Organización)
===============================================
Entidad principal que representa un tenant u organización en el sistema SaaS.
"""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.audit_log import AuditLog
    from models.cliente import Cliente
    from models.usuario import Usuario


class TenantPlan(enum.StrEnum):
    """Planes disponibles para organizaciones en la plataforma."""
    community = "community"
    professional = "professional"
    enterprise = "enterprise"


class Tenant(Base):
    """
    Representa una organización / tenant independiente en la base de datos.
    El aislamiento de los datos se realiza a nivel de fila (RLS) usando tenant_id.
    """
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    plan: Mapped[TenantPlan] = mapped_column(
        Enum(TenantPlan, name="tenant_plan", native_enum=False),
        default=TenantPlan.community,
        nullable=False,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relaciones
    clientes: Mapped[list[Cliente]] = relationship(
        "Cliente",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    usuarios: Mapped[list[Usuario]] = relationship(
        "Usuario",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    audit_logs: Mapped[list[AuditLog]] = relationship(
        "AuditLog",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
