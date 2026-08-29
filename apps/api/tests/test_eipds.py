"""
OS Privacidad — Tests de Evaluaciones de Impacto (EIPD / PIA)
=============================================================
Verifica el ciclo de vida de la EIPD, dictamen del DPD y generación del informe oficial.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_eipd_creation_approval_and_report_flow(
    client: AsyncClient, tenant_admin_auth_headers: dict
):
    """
    Flujo completo de EIPD:
    1. Crear un proceso RAT.
    2. Crear borrador de EIPD vinculado al proceso.
    3. DPO emite dictamen técnico y aprueba la EIPD.
    4. Generar informe técnico-jurídico consolidado (Art. 32 RGLOPDP).
    """
    # 1. Crear proceso
    proc_payload = {
        "nombre": "Analítica Predictiva y Perfilamiento de Clientes",
        "descripcion": "Modelos de scoring crediticio automatizado",
        "area_responsable": "Riesgo Financiero",
        "base_legal": "consentimiento",
        "finalidad": "Evaluación crediticia algorítmica",
        "tiene_perfiles": True,
        "frecuencia_tratamiento": "continua",
        "volumen_titulares_estimado": 50000,
    }
    resp_proc = await client.post("/api/v1/procesos", json=proc_payload, headers=tenant_admin_auth_headers)
    assert resp_proc.status_code == 201
    proceso_id = resp_proc.json()["id"]
    assert resp_proc.json()["requiere_eipd"] is True

    # 2. Crear borrador de EIPD
    eipd_payload = {
        "proceso_id": proceso_id,
        "titulo": "EIPD sobre Modelos de Scoring Crediticio Automatizado",
        "descripcion_sistematica": "Flujo de ingesta de variables financieras, procesamiento mediante algoritmos de Machine Learning y emisión de dictamen automatizado.",
        "justificacion_necesidad_proporcionalidad": "El tratamiento es necesario para el otorgamiento responsable de crédito. Se minimizan las variables no indispensables.",
    }
    resp_eipd = await client.post("/api/v1/eipds", json=eipd_payload, headers=tenant_admin_auth_headers)
    assert resp_eipd.status_code == 201
    eipd_data = resp_eipd.json()
    assert eipd_data["codigo"].startswith("EIPD-")
    assert eipd_data["estado"] == "borrador"
    eipd_id = eipd_data["id"]

    # 3. DPO emite dictamen y aprueba
    aprob_payload = {
        "dictamen_dpd": "DICTAMEN FAVORABLE CONDICIONADO: Se validaron las medidas de explicabilidad algorítmica y los mecanismos de intervención humana en apelaciones.",
        "nuevo_estado": "aprobada",
    }
    resp_aprob = await client.post(
        f"/api/v1/eipds/{eipd_id}/aprobar",
        json=aprob_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_aprob.status_code == 200
    assert resp_aprob.json()["estado"] == "aprobada"
    assert resp_aprob.json()["fecha_aprobacion"] is not None

    # 4. Generar reporte consolidado oficial
    resp_rep = await client.get(f"/api/v1/eipds/{eipd_id}/reporte", headers=tenant_admin_auth_headers)
    assert resp_rep.status_code == 200
    rep_data = resp_rep.json()
    assert rep_data["eipd"]["id"] == eipd_id
    assert rep_data["proceso"]["id"] == proceso_id
    assert "Informe de Evaluación de Impacto" in rep_data["resumen_cumplimiento_lopdp"]
