"""
OS Privacidad — Modelo de Proceso (Registro de Actividades de Tratamiento - RAT)
================================================================================
Registro de Actividades de Tratamiento (RAT) conforme a:
- Art. 47 num. 12 LOPDP y Art. 38 RGLOPDP (9 Atributos Obligatorios).
- Resolución N° SPDP-SPD-2026-0005-R (Modelo Técnico de Gran Escala - MTGE).
Aislado por RLS mediante tenant_id.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.caso import Caso
    from models.cliente import Cliente
    from models.eipd import EvaluacionImpacto
    from models.riesgo import Riesgo


class BaseLegal(enum.StrEnum):
    """Bases legales de legitimación para el tratamiento de datos (Art. 7 LOPDP)."""
    consentimiento = "consentimiento"
    obligacion_legal = "obligacion_legal"
    ejecucion_contrato = "ejecucion_contrato"
    interes_legitimo = "interes_legitimo"
    mision_interes_publico = "mision_interes_publico"
    interes_vital = "interes_vital"


class FrecuenciaTratamiento(enum.StrEnum):
    """Frecuencia del tratamiento según el Modelo Técnico de Gran Escala (MTGE)."""
    unica = "unica"
    periodica = "periodica"
    continua = "continua"


class Proceso(Base, TimestampMixin):
    """
    Representa una actividad de tratamiento de datos personales en una organización (RAT).
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

    # ── Atributos Obligatorios RGLOPDP Art. 38 y MTGE ───────────
    destinatarios: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Encargados y terceros cesionarios de los datos",
    )

    colectivos_titulares: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Categorías de personas afectadas: empleados, clientes, pacientes, etc.",
    )

    tiene_perfiles: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Indica si se realiza elaboración de perfiles o decisiones automatizadas",
    )

    transferencia_internacional: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    paises_transferencia: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    garantias_transferencia: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Garantías jurídicas: Cláusulas Contractuales Tipo (CTM), BCR, etc.",
    )

    plazo_conservacion: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Plazos previstos para la supresión o criterios de conservación",
    )

    frecuencia_tratamiento: Mapped[str] = mapped_column(
        String(50),
        default=FrecuenciaTratamiento.continua.value,
        nullable=False,
    )

    permanencia_tratamiento: Mapped[str] = mapped_column(
        String(50),
        default="indefinida",
        nullable=False,
    )

    volumen_titulares_estimado: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Cantidad total única de titulares en un período de 12 meses",
    )

    puntaje_mtge: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Puntaje obtenido según el Modelo Técnico de Gran Escala de la SPDP",
    )

    requiere_eipd: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Indica si por MTGE (>=6 pts) o mandato legal (Art. 42 LOPDP) requiere EIPD obligatoria",
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relaciones
    cliente: Mapped[Cliente | None] = relationship("Cliente")
    casos: Mapped[list[Caso]] = relationship("Caso", back_populates="proceso")
    riesgos: Mapped[list[Riesgo]] = relationship("Riesgo", back_populates="proceso")
    evaluaciones_impacto: Mapped[list[EvaluacionImpacto]] = relationship(
        "EvaluacionImpacto", back_populates="proceso"
    )
