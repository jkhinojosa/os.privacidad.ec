"""
OS Privacidad — Modelo de Vulneración de Seguridad de Datos Personales (Brecha / Incidente)
==========================================================================================
Implementación conforme a la LOPDP (Arts. 43, 44 y 46) y Reglamento General (Arts. 24-28).
Gestiona la línea de tiempo perentoria (5 días SPDP, 3 días Titulares) e informe oficial.
Aislado por RLS mediante tenant_id.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.caso import Caso
    from models.proceso import Proceso


class VulnerabilidadTipo(enum.StrEnum):
    """Tipología de la vulneración conforme a la tríada de seguridad."""

    confidencialidad = "confidencialidad"  # Acceso no autorizado o filtración
    integridad = "integridad"  # Alteración no autorizada de datos
    disponibilidad = "disponibilidad"  # Secuestro ransomware, pérdida o destrucción
    mixta = "mixta"


class BrechaSeveridad(enum.StrEnum):
    """Severidad del impacto en la organización y titulares."""

    baja = "baja"
    media = "media"
    alta = "alta"
    critica = "critica"


class BrechaEstado(enum.StrEnum):
    """Estados del ciclo de vida de gestión y reporte de la brecha."""

    detectada = "detectada"
    en_contencion = "en_contencion"
    evaluada_dpd = "evaluada_dpd"
    notificada_spdp = "notificada_spdp"
    notificada_titulares = "notificada_titulares"
    resuelta_cerrada = "resuelta_cerrada"


class BrechaSeguridad(Base, TimestampMixin):
    """
    Representa un incidente o vulneración de seguridad que compromete datos personales.
    """

    __tablename__ = "brechas_seguridad"
    __table_args__ = (UniqueConstraint("tenant_id", "codigo", name="uq_brecha_tenant_codigo"),)

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
        doc="Ej. BRC-2026-0001",
    )

    caso_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("casos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    proceso_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procesos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Descripción Técnica (Art. 26 RGLOPDP Num. 1, 3, 4) ────
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_vulneracion: Mapped[VulnerabilidadTipo] = mapped_column(
        Enum(VulnerabilidadTipo, name="vulnerabilidad_tipo", native_enum=False),
        default=VulnerabilidadTipo.confidencialidad,
        nullable=False,
        index=True,
    )
    severidad: Mapped[BrechaSeveridad] = mapped_column(
        Enum(BrechaSeveridad, name="brecha_severidad", native_enum=False),
        default=BrechaSeveridad.alta,
        nullable=False,
        index=True,
    )
    estado: Mapped[BrechaEstado] = mapped_column(
        Enum(BrechaEstado, name="brecha_estado", native_enum=False),
        default=BrechaEstado.detectada,
        nullable=False,
        index=True,
    )

    sistemas_afectados: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Detalle de sistemas, servidores, bases de datos o plataformas"
    )
    causa_presunta: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Hipótesis técnica de la explotación de la vulnerabilidad"
    )

    # ── Titulares y Volumen Expuesto (Art. 26 Num. 2, 5) ──────
    colectivos_afectados: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, doc="Clientes, pacientes, empleados, menores, etc."
    )
    volumen_titulares_estimado: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    categorias_datos_expuestas: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, doc="Identificativos, financieros, salud, biométricos, etc."
    )

    # ── Línea de Tiempo y SLA SPDP (Art. 43 LOPDP - 5 Días Término) ─
    fecha_deteccion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Fecha y hora en que la organización tuvo constancia de la vulneración",
    )
    fecha_limite_spdp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Fecha límite de 5 días hábiles para notificar a SPDP y ARCOTEL",
    )
    notificada_a_spdp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_notificacion_spdp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    numero_radicado_spdp: Mapped[str | None] = mapped_column(
        String(100), nullable=True, doc="Número de ingreso formal o trámite ante la SPDP"
    )
    notificada_a_arcotel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    justificacion_dilacion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Obligatoria si la notificación se realiza fuera del término de 5 días",
    )

    # ── Notificación a Titulares (Art. 46 LOPDP - 3 Días Término) ──
    requiere_notificacion_titulares: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    fecha_calificacion_riesgo: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fecha_limite_titulares: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Fecha límite de 3 días hábiles desde que se constata riesgo para derechos",
    )
    notificada_a_titulares: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_notificacion_titulares: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    canal_notificacion_titulares: Mapped[str | None] = mapped_column(
        String(100), nullable=True, doc="correo_individual, portal_web_masivo, prensa"
    )
    excepcion_titulares_aplicada: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="cifrado_previo (Art. 46.1), mitigacion_inmediata (Art. 46.2), esfuerzo_desproporcionado (Art. 46.3)",
    )
    justificacion_excepcion_titulares: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Medidas de Mitigación y Dictamen DPD (Art. 26 Num. 6, 7) ─
    medidas_contencion_inmediatas: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Acciones ya implementadas (aislamiento, reseteo de claves, etc.)"
    )
    medidas_remediacion_previstas: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Acciones posteriores para mitigar consecuencias y parchar vulnerabilidad",
    )
    dictamen_dpd: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Criterio técnico vinculante del Delegado de Protección de Datos"
    )
    evaluacion_riesgo_titulares: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Evaluación del impacto en derechos y libertades conforme a metodología SPDP",
    )
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relaciones ───────────────────────────────────────────
    caso: Mapped[Caso | None] = relationship("Caso")
    proceso: Mapped[Proceso | None] = relationship("Proceso")
