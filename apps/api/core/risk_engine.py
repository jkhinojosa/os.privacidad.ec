"""
OS Privacidad — Motor de Evaluación de Riesgos y Modelo Técnico de Gran Escala (MTGE)
=====================================================================================
Implementación de las fórmulas y algoritmos metodológicos conformes a:
- Guía de Gestión de Riesgos y Evaluación de Impacto SPDP (Versión 2026).
- Resolución N° SPDP-SPD-2026-0005-R (MTGE).
- Art. 42 de la Ley Orgánica de Protección de Datos Personales (LOPDP).
"""

from __future__ import annotations

from typing import Any

from models.proceso import FrecuenciaTratamiento
from models.riesgo import RiesgoNivel

# ── Coeficientes de Vulnerabilidad (Guía SPDP 2026) ─────────
COEF_VULNERABILIDAD_PROMEDIO: float = 0.5
COEF_VULNERABILIDAD_PRIORITARIA: float = 0.8  # Menores, salud, discapacidad, etc.


def calcular_score_y_nivel_riesgo(
    probabilidad: int,
    impacto: int,
    es_vulnerable: bool = False,
) -> tuple[float, RiesgoNivel]:
    """
    Calcula el puntaje y nivel de riesgo para la protección de derechos y libertades.
    Fórmula: R = P * (I * V)

    Escalas de entrada:
    - Probabilidad (P): 1 a 5
    - Impacto (I): 1 a 5
    - Vulnerabilidad (V): 0.5 (promedio) u 0.8 (grupos de atención prioritaria)

    Escala de salida (Score):
    - [0.5, 5.0)  -> Bajo
    - [5.0, 12.0) -> Medio
    - [12.0, 20.0) -> Alto
    - [20.0, 25.0] -> Crítico
    """
    prob = max(1, min(5, probabilidad))
    imp = max(1, min(5, impacto))
    coef = COEF_VULNERABILIDAD_PRIORITARIA if es_vulnerable else COEF_VULNERABILIDAD_PROMEDIO

    score = round(prob * (imp * coef), 2)

    if score < 5.0:
        nivel = RiesgoNivel.bajo
    elif score < 12.0:
        nivel = RiesgoNivel.medio
    elif score < 20.0:
        nivel = RiesgoNivel.alto
    else:
        nivel = RiesgoNivel.critico

    return score, nivel


def calcular_puntaje_mtge(
    volumen_titulares: int | None,
    frecuencia: str,
    tipo_datos: list[Any] | dict | None,
    tiene_perfiles: bool = False,
    transferencia_internacional: bool = False,
) -> float:
    """
    Calcula el puntaje de Gran Escala conforme a la Resolución N° SPDP-SPD-2026-0005-R.
    Umbral de obligatoriedad de EIPD: Puntaje >= 6.0 puntos.
    """
    puntaje = 0.0

    # 1. Volumen de Titulares únicos en 12 meses
    vol = volumen_titulares or 0
    if vol > 10000:
        puntaje += 3.0
    elif vol >= 1000:
        puntaje += 2.0
    elif vol > 0:
        puntaje += 1.0

    # 2. Categorías y Sensibilidad de Datos
    datos_str = str(tipo_datos or "").lower()
    sensibles_keywords = [
        "salud",
        "biom",
        "genet",
        "sexual",
        "religio",
        "polit",
        "etni",
        "menor",
        "nino",
        "discapacidad",
    ]
    if any(k in datos_str for k in sensibles_keywords):
        puntaje += 3.0
    elif any(
        k in datos_str for k in ["financier", "bancar", "credit", "laboral", "penal", "infraccion"]
    ):
        puntaje += 2.0
    else:
        puntaje += 1.0

    # 3. Frecuencia del tratamiento
    if frecuencia == FrecuenciaTratamiento.continua.value or frecuencia == "continua":
        puntaje += 2.0
    elif frecuencia == FrecuenciaTratamiento.periodica.value or frecuencia == "periodica":
        puntaje += 1.0

    # 4. Factores agravantes de riesgo
    if tiene_perfiles:
        puntaje += 2.0
    if transferencia_internacional:
        puntaje += 1.0

    return round(puntaje, 1)


def evaluar_obligatoriedad_eipd(
    puntaje_mtge: float,
    tipo_datos: list[Any] | dict | None,
    tiene_perfiles: bool = False,
) -> tuple[bool, str]:
    """
    Evalúa si una actividad de tratamiento requiere Evaluación de Impacto (EIPD / PIA) obligatoria
    según el Art. 42 LOPDP y la Resolución SPDP-SPD-2026-0005-R.
    """
    datos_str = str(tipo_datos or "").lower()
    es_salud_o_sensible = any(k in datos_str for k in ["salud", "biom", "genet", "menor", "nino"])

    if es_salud_o_sensible and puntaje_mtge >= 4.0:
        return (
            True,
            "Calificación directa obligatoria: Tratamiento de datos de salud / sensibles / menores de edad.",
        )

    if tiene_perfiles:
        return (
            True,
            "Mandato legal Art. 42 lit. a LOPDP: Evaluación sistemática y elaboración de perfiles.",
        )

    if puntaje_mtge >= 6.0:
        return True, f"Supera el umbral de Gran Escala MTGE ({puntaje_mtge} >= 6.0 puntos)."

    return False, "Tratamiento de riesgo ordinario (no supera umbrales obligatorios de EIPD)."
