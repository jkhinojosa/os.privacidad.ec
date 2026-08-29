"""
OS Privacidad — Modelo de Proceso (Actividad de Tratamiento)
============================================================
Registro de Actividades de Tratamiento (RAT) conforme a la LOPDP y RGPD.
Aislado por RLS mediante tenant_id.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.caso import Caso
    from models.cliente import Cliente


class BaseLegal(enum.StrEnum):
    """Bases legales de legitimación para el tratamiento de datos (Art. 7 LOPDP)."""

    consentimiento = "consentimiento"
    obligacion_legal = "obligacion_legal"
    ejecucion_contrato = "ejecucion_contrato"
    interes_legitimo = "interes_legitimo"
    mision_interes_publico = "mision_interes_publico"
    interes_vital = "interes_vital"


class Proceso(Base, TimestampMixin):
    """
    Representa una actividad de tratamiento de datos personales en una organización.
    """

    __tablename__ = "procesos"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
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

    area_responsable: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    base_legal: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=BaseLegal.consentimiento.value,
    )

    finalidad: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    tipo_datos: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relaciones
    cliente: Mapped[Cliente | None] = relationship(
        "Cliente",
    )

    casos: Mapped[list[Caso]] = relationship(
        "Caso",
        back_populates="proceso",
    )
