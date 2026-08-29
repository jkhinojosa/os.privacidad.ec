"""
OS Privacidad — Máquina de Estados y Secuenciador Correlativo
=============================================================
Control de transiciones del ciclo de vida de Casos y generación atómica de códigos únicos.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.caso import Caso, CasoEstado
from models.expediente import Expediente

# ── 1. Matriz de Transiciones Permitidas para Casos ─────────
# Especificada en la sección 3.1 del Build Prompt
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
    Valida si la transición entre el estado actual y el estado destino es válida.
    Lanza HTTPException 400 con mensaje explicativo si es inválida.
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


# ── 2. Generador de Código Correlativo Secuencial ───────────
async def generate_next_codigo(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    prefix: str,
) -> str:
    """
    Genera un código correlativo con formato: {PREFIX}-{YYYY}-{0001}
    Ejemplos: CAS-2026-0001, EXP-2026-0001
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
    else:
        raise ValueError(f"Prefijo no soportado: {prefix}")

    res = await db.execute(stmt)
    count = res.scalar() or 0
    next_seq = count + 1

    return f"{year_prefix}{next_seq:04d}"
