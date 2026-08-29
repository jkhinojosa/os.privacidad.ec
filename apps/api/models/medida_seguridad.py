"""
OS Privacidad — Modelo de Medidas de Seguridad (Salvaguardas / Controles)
========================================================================
Catálogo de medidas técnicas, organizativas, jurídicas, físicas e informativas
conforme a la Guía SPDP 2026 y Art. 47 LOPDP.
Aislado por RLS mediante tenant_id.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.riesgo import Riesgo


class MedidaTipo(enum.StrEnum):
    """Clasificación de medidas de seguridad según la Guía SPDP 2026."""
    tecnica = "tecnica"
    organizativa = "organizativa"
    juridica = "juridica"
    fisica = "fisica"
    informativa = "informativa"


class MedidaEstado(enum.StrEnum):
    """Estado de implementación de la salvaguarda."""
    planificada = "planificada"
    en_proceso = "en_proceso"
    implementada = "implementada"
    verificada = "verificada"


class MedidaSeguridad(Base, TimestampMixin):
    """
    Representa una medida o control de seguridad implementado para mitigar riesgos.
    """
    __tablename__ = "medidas_seguridad"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_medidas_tenant_codigo"),
    )

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
        doc="Ej. MED-2026-0001",
    )

    tipo: Mapped[MedidaTipo] = mapped_column(
        Enum(MedidaTipo, name="medida_tipo", native_enum=False),
        nullable=False,
        index=True,
    )

    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    descripcion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    estado_implementacion: Mapped[MedidaEstado] = mapped_column(
        Enum(MedidaEstado, name="medida_estado", native_enum=False),
        default=MedidaEstado.planificada,
        nullable=False,
        index=True,
    )

    responsable: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    evidencia_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Enlace o ruta al documento/política de evidencia probatoria",
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relación N:M con riesgos
    riesgos: Mapped[list[Riesgo]] = relationship(
        "Riesgo",
        secondary="riesgo_medidas",
        back_populates="medidas",
    )
