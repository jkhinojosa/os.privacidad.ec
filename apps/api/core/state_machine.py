"""
OS Privacidad — Máquina de Estados y Secuenciador Correlativo
=============================================================
Control de transiciones del ciclo de vida de Casos, Solicitudes LOPDP,
Brechas de Seguridad y generación atómica de códigos únicos correlativos.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.brecha_seguridad import BrechaEstado, BrechaSeguridad
from models.caso import Caso, CasoEstado
from models.expediente import Expediente
from models.solicitud_derecho import SolicitudDerecho, SolicitudEstado

# ── 1. Matriz de Transiciones Permitidas para Casos ─────────
VALID_CASO_TRANSITIONS: dict[CasoEstado, list[CasoEstado]] = {
    CasoEstado.abierto: [
        CasoEstado.en_investigacion,
        CasoEstado.cerrado,
    ],
    CasoEstado.en_investigacion: [
        CasoEstado.en_comite,
        CasoEstado.cerrado,
    ],
    CasoEstado.en_comite: [
        CasoEstado.en_investigacion,
        CasoEstado.cerrado,
    ],
    CasoEstado.cerrado: [
        CasoEstado.reabierto,
    ],
    CasoEstado.reabierto: [
        CasoEstado.en_investigacion,
        CasoEstado.cerrado,
    ],
}


def validate_caso_transition(current_state: CasoEstado, target_state: CasoEstado) -> None:
    """
    Valida si la transición entre el estado actual y el estado destino es válida para un Caso.
    """
    if current_state == target_state:
        return

    allowed = VALID_CASO_TRANSITIONS.get(current_state, [])
    if target_state not in allowed:
        allowed_str = ", ".join(f"'{s.value}'" for s in allowed) or "ninguno"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_STATE_TRANSITION",
                    "message": f"Transición inválida: No es posible pasar de '{current_state.value}' a '{target_state.value}'. Transiciones permitidas desde este estado: [{allowed_str}].",
                }
            },
        )


# ── 2. Matriz de Transiciones para Solicitudes LOPDP ─────────
VALID_SOLICITUD_TRANSITIONS: dict[SolicitudEstado, list[SolicitudEstado]] = {
    SolicitudEstado.recibida: [
        SolicitudEstado.en_subsanacion,
        SolicitudEstado.en_analisis,
        SolicitudEstado.prorrogada,
        SolicitudEstado.aprobada,
        SolicitudEstado.denegada,
        SolicitudEstado.archivada,
    ],
    SolicitudEstado.en_subsanacion: [
        SolicitudEstado.en_analisis,
        SolicitudEstado.prorrogada,
        SolicitudEstado.aprobada,
        SolicitudEstado.denegada,
        SolicitudEstado.archivada,
    ],
    SolicitudEstado.en_analisis: [
        SolicitudEstado.prorrogada,
        SolicitudEstado.aprobada,
        SolicitudEstado.denegada,
    ],
    SolicitudEstado.prorrogada: [
        SolicitudEstado.aprobada,
        SolicitudEstado.denegada,
    ],
    SolicitudEstado.aprobada: [
        SolicitudEstado.en_ejecucion,
        SolicitudEstado.notificada_encargados,
        SolicitudEstado.atendida,
    ],
    SolicitudEstado.en_ejecucion: [
        SolicitudEstado.notificada_encargados,
        SolicitudEstado.atendida,
    ],
    SolicitudEstado.notificada_encargados: [
        SolicitudEstado.en_ejecucion,
        SolicitudEstado.atendida,
    ],
    SolicitudEstado.denegada: [],
    SolicitudEstado.atendida: [],
    SolicitudEstado.archivada: [],
}


def validate_solicitud_transition(
    current_state: SolicitudEstado, target_state: SolicitudEstado
) -> None:
    """
    Valida si la transición entre estados de la solicitud de derechos LOPDP es legalmente procedente.
    """
    if current_state == target_state:
        return

    allowed = VALID_SOLICITUD_TRANSITIONS.get(current_state, [])
    if target_state not in allowed:
        allowed_str = ", ".join(f"'{s.value}'" for s in allowed) or "ninguno (estado terminal)"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_STATE_TRANSITION",
                    "message": f"Transición procedimental inválida: No es posible pasar de '{current_state.value}' a '{target_state.value}'. Transiciones permitidas desde este estado: [{allowed_str}].",
                }
            },
        )


# ── 3. Matriz de Transiciones para Brechas de Seguridad ─────
VALID_BRECHA_TRANSITIONS: dict[BrechaEstado, list[BrechaEstado]] = {
    BrechaEstado.detectada: [
        BrechaEstado.en_contencion,
        BrechaEstado.evaluada_dpd,
        BrechaEstado.notificada_spdp,
        BrechaEstado.resuelta_cerrada,
    ],
    BrechaEstado.en_contencion: [
        BrechaEstado.evaluada_dpd,
        BrechaEstado.notificada_spdp,
        BrechaEstado.resuelta_cerrada,
    ],
    BrechaEstado.evaluada_dpd: [
        BrechaEstado.notificada_spdp,
        BrechaEstado.notificada_titulares,
        BrechaEstado.resuelta_cerrada,
    ],
    BrechaEstado.notificada_spdp: [
        BrechaEstado.notificada_titulares,
        BrechaEstado.resuelta_cerrada,
    ],
    BrechaEstado.notificada_titulares: [
        BrechaEstado.resuelta_cerrada,
    ],
    BrechaEstado.resuelta_cerrada: [],
}


def validate_brecha_transition(current_state: BrechaEstado, target_state: BrechaEstado) -> None:
    """
    Valida si la transición entre estados de gestión del incidente de seguridad es procedente.
    """
    if current_state == target_state:
        return

    allowed = VALID_BRECHA_TRANSITIONS.get(current_state, [])
    if target_state not in allowed:
        allowed_str = ", ".join(f"'{s.value}'" for s in allowed) or "ninguno (incidente cerrado)"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_STATE_TRANSITION",
                    "message": f"Transición de incidente inválida: No es posible pasar de '{current_state.value}' a '{target_state.value}'. Transiciones permitidas: [{allowed_str}].",
                }
            },
        )


# ── 4. Generador de Código Correlativo Secuencial ───────────
async def generate_next_codigo(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    prefix: str,
) -> str:
    """
    Genera un código correlativo con formato: {PREFIX}-{YYYY}-{0001}
    Ejemplos: CAS-2026-0001, EXP-2026-0001, SOL-2026-0001, BRC-2026-0001
    Garantiza unicidad por tenant y año.
    """
    year = datetime.datetime.now(datetime.UTC).year
    year_prefix = f"{prefix}-{year}-"

    if prefix == "CAS":
        stmt = select(func.count(Caso.id)).where(
            Caso.tenant_id == tenant_id,
            Caso.codigo.like(f"{year_prefix}%"),
        )
    elif prefix == "EXP":
        stmt = select(func.count(Expediente.id)).where(
            Expediente.tenant_id == tenant_id,
            Expediente.codigo.like(f"{year_prefix}%"),
        )
    elif prefix == "MED":
        from models.medida_seguridad import MedidaSeguridad

        stmt = select(func.count(MedidaSeguridad.id)).where(
            MedidaSeguridad.tenant_id == tenant_id,
            MedidaSeguridad.codigo.like(f"{year_prefix}%"),
        )
    elif prefix == "RSK":
        from models.riesgo import Riesgo

        stmt = select(func.count(Riesgo.id)).where(
            Riesgo.tenant_id == tenant_id,
            Riesgo.codigo.like(f"{year_prefix}%"),
        )
    elif prefix == "EIPD":
        from models.eipd import EvaluacionImpacto

        stmt = select(func.count(EvaluacionImpacto.id)).where(
            EvaluacionImpacto.tenant_id == tenant_id,
            EvaluacionImpacto.codigo.like(f"{year_prefix}%"),
        )
    elif prefix == "SOL":
        stmt = select(func.count(SolicitudDerecho.id)).where(
            SolicitudDerecho.tenant_id == tenant_id,
            SolicitudDerecho.codigo.like(f"{year_prefix}%"),
        )
    elif prefix == "BRC":
        stmt = select(func.count(BrechaSeguridad.id)).where(
            BrechaSeguridad.tenant_id == tenant_id,
            BrechaSeguridad.codigo.like(f"{year_prefix}%"),
        )
    else:
        raise ValueError(f"Prefijo no soportado: {prefix}")

    res = await db.execute(stmt)
    count = res.scalar() or 0
    next_seq = count + 1

    return f"{year_prefix}{next_seq:04d}"
