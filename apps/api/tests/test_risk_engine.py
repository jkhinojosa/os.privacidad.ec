"""
OS Privacidad — Tests del Motor de Riesgo y MTGE
================================================
Valida las fórmulas de derechos y libertades R = P * (I * V)
y los criterios de obligatoriedad de EIPD según la Guía SPDP 2026.
"""

from core.risk_engine import (
    calcular_puntaje_mtge,
    calcular_score_y_nivel_riesgo,
    evaluar_obligatoriedad_eipd,
)
from models.riesgo import RiesgoNivel


def test_calcular_score_y_nivel_riesgo_promedio():
    """Para titulares promedio (V=0.5), P=4, I=4 da Score=8.0 (Medio)."""
    score, nivel = calcular_score_y_nivel_riesgo(probabilidad=4, impacto=4, es_vulnerable=False)
    assert score == 8.0
    assert nivel == RiesgoNivel.medio


def test_calcular_score_y_nivel_riesgo_vulnerable():
    """Para titulares vulnerables (V=0.8), P=4, I=4 se eleva a Score=12.8 (Alto)."""
    score, nivel = calcular_score_y_nivel_riesgo(probabilidad=4, impacto=4, es_vulnerable=True)
    assert score == 12.8
    assert nivel == RiesgoNivel.alto


def test_calcular_score_extremo_critico():
    """P=5, I=5 con V=0.8 da Score=20.0 (Crítico)."""
    score, nivel = calcular_score_y_nivel_riesgo(probabilidad=5, impacto=5, es_vulnerable=True)
    assert score == 20.0
    assert nivel == RiesgoNivel.critico


def test_calcular_score_bajo():
    """P=1, I=2 con V=0.5 da Score=1.0 (Bajo)."""
    score, nivel = calcular_score_y_nivel_riesgo(probabilidad=1, impacto=2, es_vulnerable=False)
    assert score == 1.0
    assert nivel == RiesgoNivel.bajo


def test_mtge_gran_escala_triggers_eipd():
    """Tratamiento masivo de salud supera umbral MTGE >= 6.0 y requiere EIPD."""
    puntaje = calcular_puntaje_mtge(
        volumen_titulares=15000,
        frecuencia="continua",
        tipo_datos=["salud", "biométricos"],
        tiene_perfiles=True,
        transferencia_internacional=True,
    )
    assert puntaje >= 6.0

    req_eipd, motivo = evaluar_obligatoriedad_eipd(
        puntaje_mtge=puntaje,
        tipo_datos=["salud", "biométricos"],
        tiene_perfiles=True,
    )
    assert req_eipd is True
    assert (
        "salud" in motivo.lower() or "gran escala" in motivo.lower() or "perfiles" in motivo.lower()
    )


def test_mtge_bajo_impacto_no_eipd():
    """Tratamiento de bajo volumen con datos identificativos básicos no requiere EIPD."""
    puntaje = calcular_puntaje_mtge(
        volumen_titulares=200,
        frecuencia="unica",
        tipo_datos=["identificativos"],
        tiene_perfiles=False,
        transferencia_internacional=False,
    )
    assert puntaje < 6.0

    req_eipd, _ = evaluar_obligatoriedad_eipd(
        puntaje_mtge=puntaje,
        tipo_datos=["identificativos"],
        tiene_perfiles=False,
    )
    assert req_eipd is False
