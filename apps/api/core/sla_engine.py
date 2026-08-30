"""
OS Privacidad — Motor de SLA y Cómputo de Plazos Legales en Días Hábiles (LOPDP)
=================================================================================
Calcula con exactitud matemática y jurídica los plazos perentorios de atención
conforme a la LOPDP y su Reglamento General:
- Plazo ordinario de atención: 15 días hábiles.
- Prórroga excepcional justificada: +15 días hábiles adicionales.
- Plazo de requerimiento de subsanación: 5 días hábiles (Art. 14 RGLOPDP).
- Plazo de atención de subsanación por el titular: 10 días hábiles.
- Suspensión operativa técnica: <= 3 días hábiles (Art. 16 RGLOPDP).
"""

from __future__ import annotations

import datetime
from typing import Any

# Feriados nacionales oficiales recurrentes de Ecuador (Mes, Día)
# Nota: Para días móviles de Carnaval o Viernes Santo se calculan dinámicamente o se incluyen fechas fijas.
FERIADOS_ECUADOR_FIJOS: set[tuple[int, int]] = {
    (1, 1),  # Año Nuevo
    (5, 1),  # Día del Trabajo
    (5, 24),  # Batalla de Pichincha
    (8, 10),  # Primer Grito de Independencia
    (10, 9),  # Independencia de Guayaquil
    (11, 2),  # Día de los Difuntos
    (11, 3),  # Independencia de Cuenca
    (12, 25),  # Navidad
}


def es_dia_habil(fecha: datetime.date) -> bool:
    """Verifica si una fecha corresponde a un día hábil (Lunes a Viernes no feriado)."""
    # 0 = Lunes, 6 = Domingo
    if fecha.weekday() >= 5:
        return False
    return (fecha.month, fecha.day) not in FERIADOS_ECUADOR_FIJOS


def calcular_fecha_limite_habiles(
    fecha_inicio: datetime.datetime,
    dias_habiles: int = 15,
) -> datetime.datetime:
    """
    Suma exactamente el número de días hábiles especificado a partir de una fecha dada.
    Conserva la zona horaria original (o UTC).
    """
    cur_date = fecha_inicio.date()
    dias_contados = 0

    while dias_contados < dias_habiles:
        cur_date += datetime.timedelta(days=1)
        if es_dia_habil(cur_date):
            dias_contados += 1

    # Retorna con la misma hora/minuto/segundo/tzinfo que la fecha original
    return datetime.datetime.combine(
        cur_date,
        fecha_inicio.timetz(),
    )


def calcular_dias_habiles_restantes(
    fecha_limite: datetime.datetime,
    fecha_referencia: datetime.datetime | None = None,
) -> int:
    """
    Calcula cuántos días hábiles quedan hasta la fecha límite.
    Retorna un valor positivo si está a tiempo, o negativo si está vencido.
    """
    ahora = fecha_referencia or datetime.datetime.now(datetime.UTC)
    cur_date = ahora.date()
    target_date = fecha_limite.date()

    if cur_date == target_date:
        return 0

    if cur_date < target_date:
        # A futuro
        count = 0
        d = cur_date + datetime.timedelta(days=1)
        while d <= target_date:
            if es_dia_habil(d):
                count += 1
            d += datetime.timedelta(days=1)
        return count
    else:
        # Vencido
        count = 0
        d = target_date + datetime.timedelta(days=1)
        while d <= cur_date:
            if es_dia_habil(d):
                count += 1
            d += datetime.timedelta(days=1)
        return -count


def evaluar_semaforo_sla(
    fecha_limite: datetime.datetime,
    fecha_referencia: datetime.datetime | None = None,
) -> dict[str, Any]:
    """
    Genera el semáforo y diagnóstico del SLA:
    - 'en_tiempo': > 3 días hábiles restantes.
    - 'en_alerta': 1 a 3 días hábiles restantes (riesgo inminente de incumplimiento).
    - 'vencido': <= 0 días hábiles restantes (infracción legal susceptible de tutela SPDP).
    """
    dias_restantes = calcular_dias_habiles_restantes(fecha_limite, fecha_referencia)

    if dias_restantes < 0:
        estado_semaforo = "vencido"
    elif dias_restantes <= 3:
        estado_semaforo = "en_alerta"
    else:
        estado_semaforo = "en_tiempo"

    return {
        "estado_semaforo": estado_semaforo,
        "dias_restantes_habiles": dias_restantes,
        "fecha_limite": fecha_limite,
        "es_vencido": dias_restantes < 0,
    }
