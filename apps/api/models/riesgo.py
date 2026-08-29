"""
OS Privacidad — Modelo de Riesgo (Gestión de Riesgos de Derechos y Libertades)
=============================================================================
Modelo para la identificación, análisis y mitigación de riesgos sobre derechos
conforme a la Guía SPDP 2026 y la fórmula ponderada R = P * (I * V).
Aislado por RLS mediante tenant_id.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.medida_seguridad import MedidaSeguridad
    from models.proceso import Proceso

# ── Tabla Intermedia Riesgo <-> Medidas de Seguridad ─────────
riesgo_medidas = Table(
    "riesgo_medidas",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column(
        "tenant_id",
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    ),
    Column(
        "riesgo_id",
        UUID(as_uuid=True),
        ForeignKey("riesgos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "medida_id",
        UUID(as_uuid=True),
        ForeignKey("medidas_seguridad.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    UniqueConstraint("tenant_id", "riesgo_id", "medida_id", name="uq_riesgo_medida"),
)


class RiesgoDimension(enum.StrEnum):
    """Dimensiones de seguridad de la información afectadas."""
    confidencialidad = "confidencialidad"
    integridad = "integridad"
    disponibilidad = "disponibilidad"
    todas = "todas"


class RiesgoNivel(enum.StrEnum):
    """Niveles de riesgo según la matriz de impacto y probabilidad."""
    bajo = "bajo"
    medio = "medio"
    alto = "alto"
    critico = "critico"


class RiesgoEstado(enum.StrEnum):
    """Estado del tratamiento del riesgo."""
    identificado = "identificado"
    en_tratamiento = "en_tratamiento"
    mitigado = "mitigado"
    aceptado = "aceptado"


class Riesgo(Base, TimestampMixin):
    """
    Representa un escenario de riesgo que amenaza derechos y libertades de titulares.
    """
    __tablename__ = "riesgos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_riesgos_tenant_codigo"),
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
        doc="Ej. RSK-2026-0001",
    )

    proceso_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procesos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    descripcion_amenaza: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    vulnerabilidad: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    dimension_afectada: Mapped[RiesgoDimension] = mapped_column(
        Enum(RiesgoDimension, name="riesgo_dimension", native_enum=False),
        default=RiesgoDimension.confidencialidad,
        nullable=False,
    )

    es_grupo_vulnerable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Si True, V=0.8 (grupos prioritarios/salud/niños), si False, V=0.5 (promedio)",
    )

    # ── Riesgo Inherente (Pre-mitigación) ─────────────────────
    probabilidad_inherente: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        doc="Escala 1 a 5",
    )

    impacto_inherente: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        doc="Escala 1 a 5",
    )

    riesgo_inherente_score: Mapped[float] = mapped_column(
        Float,
        default=4.5,
        nullable=False,
        doc="Calculado: P * (I * V)",
    )

    nivel_riesgo_inherente: Mapped[RiesgoNivel] = mapped_column(
        Enum(RiesgoNivel, name="riesgo_nivel_inherente", native_enum=False),
        default=RiesgoNivel.medio,
        nullable=False,
        index=True,
    )

    # ── Riesgo Residual (Post-mitigación con medidas) ──────────
    probabilidad_residual: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    impacto_residual: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    riesgo_residual_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    nivel_riesgo_residual: Mapped[RiesgoNivel | None] = mapped_column(
        Enum(RiesgoNivel, name="riesgo_nivel_residual", native_enum=False),
        nullable=True,
        index=True,
    )

    estado: Mapped[RiesgoEstado] = mapped_column(
        Enum(RiesgoEstado, name="riesgo_estado", native_enum=False),
        default=RiesgoEstado.identificado,
        nullable=False,
        index=True,
    )

    # Relaciones
    proceso: Mapped[Proceso | None] = relationship("Proceso", back_populates="riesgos")
    medidas: Mapped[list[MedidaSeguridad]] = relationship(
        "MedidaSeguridad",
        secondary=riesgo_medidas,
        back_populates="riesgos",
    )
