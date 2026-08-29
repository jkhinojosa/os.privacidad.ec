"""
OS Privacidad — Tests de Riesgos y Matriz de Calor
==================================================
Verifica el análisis de riesgos, la mitigación con salvaguardas y la matriz 5x5.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_riesgo_and_mitigation_flow(client: AsyncClient, tenant_admin_auth_headers: dict):
    """
    1. Registra un riesgo con Probabilidad=4, Impacto=4, Vulnerable=True -> Score=12.8 (Alto).
    2. Crea una medida de seguridad.
    3. Aplica mitigación reduciendo a Probabilidad=2, Impacto=3 -> Score=4.8 (Bajo).
    """
    # 1. Crear riesgo
    riesgo_payload = {
        "nombre": "Acceso no autorizado a historias clínicas por credenciales débiles",
        "descripcion_amenaza": "Fuerza bruta sobre portal de empleados",
        "vulnerabilidad": "Ausencia de MFA en autenticación web",
        "dimension_afectada": "confidencialidad",
        "es_grupo_vulnerable": True,
        "probabilidad_inherente": 4,
        "impacto_inherente": 4,
    }
    resp_rsk = await client.post("/api/v1/riesgos", json=riesgo_payload, headers=tenant_admin_auth_headers)
    assert resp_rsk.status_code == 201
    rsk_data = resp_rsk.json()
    assert rsk_data["codigo"].startswith("RSK-")
    assert rsk_data["riesgo_inherente_score"] == 12.8
    assert rsk_data["nivel_riesgo_inherente"] == "alto"
    riesgo_id = rsk_data["id"]

    # 2. Crear medida de seguridad
    medida_payload = {
        "tipo": "tecnica",
        "nombre": "MFA Obligatorio con WebAuthn",
        "descripcion": "Segundo factor de autenticación resistente al phishing",
        "estado_implementacion": "implementada",
    }
    resp_med = await client.post("/api/v1/medidas-seguridad", json=medida_payload, headers=tenant_admin_auth_headers)
    medida_id = resp_med.json()["id"]

    # 3. Aplicar mitigación
    mitigacion_payload = {
        "medidas_ids": [medida_id],
        "probabilidad_residual": 2,
        "impacto_residual": 3,
        "estado": "mitigado",
    }
    resp_mit = await client.post(
        f"/api/v1/riesgos/{riesgo_id}/mitigacion",
        json=mitigacion_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_mit.status_code == 200
    mit_data = resp_mit.json()
    assert mit_data["probabilidad_residual"] == 2
    assert mit_data["impacto_residual"] == 3
    assert mit_data["riesgo_residual_score"] == 4.8
    assert mit_data["nivel_riesgo_residual"] == "bajo"
    assert mit_data["estado"] == "mitigado"
    assert len(mit_data["medidas"]) == 1


@pytest.mark.asyncio
async def test_matriz_calor_endpoint(client: AsyncClient, tenant_admin_auth_headers: dict):
    """Verifica la generación de la matriz de calor 5x5."""
    resp = await client.get("/api/v1/riesgos/matriz", headers=tenant_admin_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_riesgos" in data
    assert "resumen_inherente" in data
    assert "resumen_residual" in data
    assert len(data["matriz"]) == 25  # Cuadrícula 5x5
