"""
OS Privacidad — Base de Datos: DeclarativeBase y Mixins
========================================================
Base común para todos los modelos SQLAlchemy.
Incluye naming convention para constraints y mixin de campos comunes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import MetaData, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ── Naming Convention para Alembic/PostgreSQL ────────────────
# Garantiza nombres predecibles para constraints, facilitando
# migraciones automáticas sin errores de nombres duplicados.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos de la aplicación."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """
    Mixin con campos comunes a TODAS las tablas de negocio:
    - id: UUID generado por PostgreSQL
    - tenant_id: UUID para multitenancy + RLS
    - created_at, updated_at: timestamps automáticos
    - created_by, updated_by: UUID del usuario que creó/modificó

    Según sección 2 del Build Prompt: "Todas las tablas incluyen
    id UUID PK, tenant_id UUID, created_at, updated_at, created_by, updated_by"
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,  # Crítico para rendimiento de RLS
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
