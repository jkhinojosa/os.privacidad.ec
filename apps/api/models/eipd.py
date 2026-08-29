"""
OS Privacidad — Modelo de Evaluación de Impacto en la Protección de Datos (EIPD / PIA)
======================================================================================
Gestión del ciclo de vida del informe de evaluación de impacto conforme a:
- Art. 42 LOPDP y Art. 31-32 RGLOPDP.
- Guía de Evaluación de Impacto SPDP 2026.
Aislado por RLS mediante tenant_id.
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
    from models.proceso import Proceso
    from models.usuario import Usuario


class EIPDEstado(enum.StrEnum):
    """Estados del ciclo de vida de una EIPD."""
    borrador = "borrador"
    en_revision_dpd = "en_revision_dpd"
    aprobada = "aprobada"
    notificada_spdp = "notificada_spdp"


class EvaluacionImpacto(Base, TimestampMixin):
    """
    Representa una Evaluación de Impacto relativa a la Protección de Datos (EIPD / PIA).
    """
    __tablename__ = "evaluaciones_impacto"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_eipd_tenant_codigo"),
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
        doc="Ej. EIPD-2026-0001",
    )

    proceso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procesos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    titulo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    descripcion_sistematica: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Descripción sistemática de las operaciones de tratamiento y sus finalidades (Art. 32 RGLOPDP)",
    )

    justificacion_necesidad_proporcionalidad: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Evaluación de la necesidad y proporcionalidad de las operaciones",
    )

    dictamen_dpd: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Criterio u opinión técnica vinculante emitida por el Delegado de Protección de Datos",
    )

    opinion_titulares_consultados: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Resultados del proceso de consulta a los titulares o sus representantes, si aplica",
    )

    estado: Mapped[EIPDEstado] = mapped_column(
        Enum(EIPDEstado, name="eipd_estado", native_enum=False),
        default=EIPDEstado.borrador,
        nullable=False,
        index=True,
    )

    fecha_aprobacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    aprobado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relaciones
    proceso: Mapped[Proceso] = relationship("Proceso", back_populates="evaluaciones_impacto")
    aprobador: Mapped[Usuario | None] = relationship("Usuario")
