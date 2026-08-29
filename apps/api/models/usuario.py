"""
OS Privacidad — Modelo de Usuario
=================================
Entidad Usuario con soporte de Roles (RBAC) y asignación a Tenant o Cliente.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.audit_log import AuditLog
    from models.cliente import Cliente
    from models.tenant import Tenant


class UserRole(enum.StrEnum):
    """Roles disponibles en el sistema con permisos jerárquicos (RBAC)."""

    super_admin = "super_admin"
    tenant_admin = "tenant_admin"
    dpo = "dpo"
    analista = "analista"
    auditor = "auditor"
    cliente = "cliente"


class Usuario(Base, TimestampMixin):
    """
    Usuario del sistema. Pertenece a un Tenant (o null si es SuperAdmin global).
    Puede estar asociado a un Cliente específico (ej. si su rol es 'cliente').
    """

    __tablename__ = "usuarios"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_usuarios_tenant_email"),)

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    apellido: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    rol: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
        default=UserRole.analista,
    )

    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relaciones
    tenant: Mapped[Tenant | None] = relationship(
        "Tenant",
        back_populates="usuarios",
    )

    cliente: Mapped[Cliente | None] = relationship(
        "Cliente",
        back_populates="usuarios",
    )

    audit_logs: Mapped[list[AuditLog]] = relationship(
        "AuditLog",
        back_populates="usuario",
    )
