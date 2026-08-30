"""
OS Privacidad — Tests del Motor de SLA en Días Hábiles
======================================================
Valida el cómputo de plazos perentorios de 15 días hábiles, prórrogas y semáforo preventivo.
"""

import datetime

from core.sla_engine import (
    calcular_fecha_limite_habiles,
    es_dia_habil,
    evaluar_semaforo_sla,
)


def test_es_dia_habil():
    """Lunes a viernes son hábiles; sábados, domingos y feriados no lo son."""
    lunes = datetime.date(2026, 9, 7)  # Lunes ordinario
    sabado = datetime.date(2026, 9, 12)  # Sábado
    domingo = datetime.date(2026, 9, 13)  # Domingo
    navidad = datetime.date(2026, 12, 25)  # Feriado oficial

    assert es_dia_habil(lunes) is True
    assert es_dia_habil(sabado) is False
    assert es_dia_habil(domingo) is False
    assert es_dia_habil(navidad) is False


def test_calcular_fecha_limite_habiles_15_dias():
    """Suma exactamente 15 días hábiles (aprox. 3 semanas cronológicas)."""
    # Lunes 7 de Septiembre 2026
    inicio = datetime.datetime(2026, 9, 7, 10, 0, 0, tzinfo=datetime.UTC)
    limite = calcular_fecha_limite_habiles(inicio, dias_habiles=15)

    # 15 días hábiles desde el lunes 7 de sep es el lunes 28 de sep de 2026
    assert limite.date() == datetime.date(2026, 9, 28)
    assert limite.hour == 10


def test_evaluar_semaforo_sla_en_tiempo():
    """Con 10 días restantes debe marcar 'en_tiempo'."""
    ahora = datetime.datetime(2026, 9, 7, 10, 0, 0, tzinfo=datetime.UTC)
    limite = datetime.datetime(2026, 9, 21, 10, 0, 0, tzinfo=datetime.UTC)

    diag = evaluar_semaforo_sla(limite, fecha_referencia=ahora)
    assert diag["estado_semaforo"] == "en_tiempo"
    assert diag["dias_restantes_habiles"] > 3
    assert diag["es_vencido"] is False


def test_evaluar_semaforo_sla_en_alerta():
    """Con 2 días restantes debe marcar 'en_alerta'."""
    ahora = datetime.datetime(2026, 9, 7, 10, 0, 0, tzinfo=datetime.UTC)
    limite = datetime.datetime(2026, 9, 9, 10, 0, 0, tzinfo=datetime.UTC)

    diag = evaluar_semaforo_sla(limite, fecha_referencia=ahora)
    assert diag["estado_semaforo"] == "en_alerta"
    assert diag["dias_restantes_habiles"] == 2


def test_evaluar_semaforo_sla_vencido():
    """Con fecha límite pasada debe marcar 'vencido'."""
    ahora = datetime.datetime(2026, 9, 15, 10, 0, 0, tzinfo=datetime.UTC)
    limite = datetime.datetime(2026, 9, 7, 10, 0, 0, tzinfo=datetime.UTC)

    diag = evaluar_semaforo_sla(limite, fecha_referencia=ahora)
    assert diag["estado_semaforo"] == "vencido"
    assert diag["dias_restantes_habiles"] < 0
    assert diag["es_vencido"] is True
