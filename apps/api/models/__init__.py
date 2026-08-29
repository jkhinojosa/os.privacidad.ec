"""
OS Privacidad — Exportación de Modelos de Base de Datos
=======================================================
Importa todos los modelos para que Alembic y SQLAlchemy registren sus metadatos.
"""

from db.base import Base, TimestampMixin
from models.audit_log import AuditLog
from models.caso import Caso, CasoEstado, CasoPrioridad, CasoTipo
from models.cliente import Cliente
from models.eipd import EIPDEstado, EvaluacionImpacto
from models.expediente import Expediente, ExpedienteEstado
from models.medida_seguridad import MedidaEstado, MedidaSeguridad, MedidaTipo
from models.proceso import BaseLegal, FrecuenciaTratamiento, Proceso
from models.riesgo import (
    Riesgo,
    RiesgoDimension,
    RiesgoEstado,
    RiesgoNivel,
    riesgo_medidas,
)
from models.tenant import Tenant, TenantPlan
from models.usuario import UserRole, Usuario

__all__ = [
    "Base",
    "TimestampMixin",
    "Tenant",
    "TenantPlan",
    "Cliente",
    "Usuario",
    "UserRole",
    "AuditLog",
    "Proceso",
    "BaseLegal",
    "FrecuenciaTratamiento",
    "Caso",
    "CasoTipo",
    "CasoPrioridad",
    "CasoEstado",
    "Expediente",
    "ExpedienteEstado",
    "MedidaSeguridad",
    "MedidaTipo",
    "MedidaEstado",
    "Riesgo",
    "RiesgoDimension",
    "RiesgoNivel",
    "RiesgoEstado",
    "riesgo_medidas",
    "EvaluacionImpacto",
    "EIPDEstado",
]
