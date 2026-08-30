"""
OS Privacidad — Modelo de Solicitud de Ejercicio de Derechos del Titular (LOPDP)
================================================================================
Implementación del ciclo de vida y control de plazos legales conforme a:
- LOPDP Capítulo III: Arts. 12 al 24 (Catálogo de Derechos de los Titulares).
- Reglamento General LOPDP: Arts. 14 (Subsanación), 16 (Suspensión 3d), 21 (Eliminación),
  22 (Portabilidad) y 23 (Notificación a Encargados).
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
    from models.cliente import Cliente
    from models.notificacion_encargado import NotificacionEncargado
    from models.proceso import Proceso
    from models.usuario import Usuario


class DerechoTipo(enum.StrEnum):
    """Catálogo Oficial de Derechos de los Titulares conforme a la LOPDP."""

    informacion = "informacion"  # Art. 12
    acceso = "acceso"  # Art. 13
    rectificacion_actualizacion = "rectificacion_actualizacion"  # Art. 14
    eliminacion = "eliminacion"  # Art. 15
    oposicion = "oposicion"  # Art. 16
    portabilidad = "portabilidad"  # Art. 17
    suspension = "suspension"  # Art. 19
    no_decision_automatizada = "no_decision_automatizada"  # Art. 20
    consulta = "consulta"  # Art. 22
    educacion_digital = "educacion_digital"  # Art. 23


class SolicitudEstado(enum.StrEnum):
    """Estados del flujo procedimental de atención a solicitudes LOPDP."""

    recibida = "recibida"
    en_subsanacion = "en_subsanacion"
    en_analisis = "en_analisis"
    prorrogada = "prorrogada"
    aprobada = "aprobada"
    denegada = "denegada"
    en_ejecucion = "en_ejecucion"
    notificada_encargados = "notificada_encargados"
    atendida = "atendida"
    archivada = "archivada"


class CanalRecepcion(enum.StrEnum):
    """Canal por el cual ingresó la solicitud."""

    formulario_web = "formulario_web"
    correo_electronico = "correo_electronico"
    presencial_ventanilla = "presencial_ventanilla"
    oficio_fisico = "oficio_fisico"


class SolicitudDerecho(Base, TimestampMixin):
    """
    Representa una solicitud de ejercicio de derechos presentada por un titular de datos.
    """

    __tablename__ = "solicitudes_derechos"
    __table_args__ = (UniqueConstraint("tenant_id", "codigo", name="uq_solicitud_tenant_codigo"),)

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
        doc="Ej. SOL-2026-0001",
    )

    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    proceso_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procesos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    asignado_a: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Usuario (DPO / Analista) encargado de tramitar la solicitud",
    )

    # ── Datos del Titular y Representante ─────────────────────
    titular_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    titular_identificacion: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, doc="Cédula, RUC o Pasaporte del titular"
    )
    titular_email: Mapped[str] = mapped_column(String(255), nullable=False)
    titular_telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)

    es_representante: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    representante_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    representante_identificacion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    documento_acreditacion_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Tipología y Canal ─────────────────────────────────────
    tipo_derecho: Mapped[DerechoTipo] = mapped_column(
        Enum(DerechoTipo, name="derecho_tipo", native_enum=False),
        nullable=False,
        index=True,
    )

    canal_recepcion: Mapped[CanalRecepcion] = mapped_column(
        Enum(CanalRecepcion, name="canal_recepcion", native_enum=False),
        default=CanalRecepcion.formulario_web,
        nullable=False,
    )

    estado: Mapped[SolicitudEstado] = mapped_column(
        Enum(SolicitudEstado, name="solicitud_estado", native_enum=False),
        default=SolicitudEstado.recibida,
        nullable=False,
        index=True,
    )

    # ── Contenido de la Solicitud ─────────────────────────────
    motivo_solicitud: Mapped[str] = mapped_column(Text, nullable=False)
    especificacion_datos: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Detalle de los datos que desea consultar, rectificar o suprimir"
    )
    datos_a_modificar: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True, doc="Objeto estructurado con los valores nuevos o campos a actualizar"
    )

    # ── Cómputo de Plazos Legales y SLA (Días Hábiles) ────────
    fecha_recepcion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Fecha formal de ingreso de la solicitud",
    )

    fecha_limite_sla: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Fecha límite de 15 días hábiles para emitir resolución",
    )

    fecha_subsanacion_limite: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Fecha máxima de 10 días para que el titular complete información (Art. 14 RGLOPDP)",
    )

    prorroga_aplicada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_prorroga: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dias_prorroga: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    motivo_prorroga: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Dictamen y Resolución ─────────────────────────────────
    dictamen_dpd: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Criterio técnico-jurídico vinculante emitido por el DPD"
    )
    excepcion_legal_aplicada: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Base de excepción conforme al Art. 18 LOPDP (ej. obligación legal o contractual)",
    )
    motivo_negativa: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Fundamentación jurídica en caso de negativa total o parcial"
    )
    fecha_resolucion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resuelto_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )

    # ── Ejecución Técnica y Notificación a Encargados ─────────
    ejecucion_tecnica_completada: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    fecha_ejecucion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resultado_ejecucion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Evidencia o confirmación del cambio/bloqueo/borrado en los sistemas",
    )
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relaciones ───────────────────────────────────────────
    cliente: Mapped[Cliente | None] = relationship("Cliente")
    proceso: Mapped[Proceso | None] = relationship("Proceso")
    asignado: Mapped[Usuario | None] = relationship("Usuario", foreign_keys=[asignado_a])
    resolutor: Mapped[Usuario | None] = relationship("Usuario", foreign_keys=[resuelto_por])
    notificaciones_encargados: Mapped[list[NotificacionEncargado]] = relationship(
        "NotificacionEncargado", back_populates="solicitud", cascade="all, delete-orphan"
    )
