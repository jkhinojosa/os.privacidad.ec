"""
OS Privacidad — Tests de Portabilidad de Datos (Art. 17 LOPDP)
==============================================================
Verifica la exportación en formatos estándar e interoperables JSON y CSV.
"""

import json

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_exportar_portabilidad_json(client: AsyncClient, tenant_admin_auth_headers: dict):
    """Verifica descarga de paquete de portabilidad en formato JSON estructurado."""
    sol_payload = {
        "tipo_derecho": "portabilidad",
        "titular_nombre": "Dr. Esteban Cueva",
        "titular_identificacion": "1102938475",
        "titular_email": "esteban.cueva@medicos.ec",
        "motivo_solicitud": "Portabilidad de historial médico y consentimientos",
        "datos_a_modificar": {
            "perfil": {"nombre": "Esteban Cueva", "especialidad": "Cardiología"},
            "consentimientos": [
                {"finalidad": "Investigación", "otorgado": True, "fecha": "2026-01-15"}
            ],
        },
    }
    resp_create = await client.post(
        "/api/v1/solicitudes-derechos", json=sol_payload, headers=tenant_admin_auth_headers
    )
    solicitud_id = resp_create.json()["id"]

    # Descargar JSON
    resp_json = await client.get(
        f"/api/v1/solicitudes-derechos/{solicitud_id}/exportar-portabilidad?formato=json",
        headers=tenant_admin_auth_headers,
    )
    assert resp_json.status_code == 200
    assert "application/json" in resp_json.headers["content-type"]
    assert "attachment; filename=" in resp_json.headers["content-disposition"]
    data = json.loads(resp_json.content.decode("utf-8"))
    assert "metadata_lopdp" in data
    assert "datos_personales_portables" in data
    assert data["metadata_lopdp"]["titular"]["identificacion"] == "1102938475"


@pytest.mark.asyncio
async def test_exportar_portabilidad_csv(client: AsyncClient, tenant_admin_auth_headers: dict):
    """Verifica descarga de paquete de portabilidad en formato CSV."""
    sol_payload = {
        "tipo_derecho": "portabilidad",
        "titular_nombre": "Ing. Andrea Ruiz",
        "titular_identificacion": "1722334455",
        "titular_email": "andrea.ruiz@tecnologia.ec",
        "motivo_solicitud": "Portabilidad en CSV de mis transacciones",
        "datos_a_modificar": [
            {"transaccion_id": "TX-1", "monto": "150.00", "fecha": "2026-05-10"},
            {"transaccion_id": "TX-2", "monto": "230.50", "fecha": "2026-06-12"},
        ],
    }
    resp_create = await client.post(
        "/api/v1/solicitudes-derechos", json=sol_payload, headers=tenant_admin_auth_headers
    )
    solicitud_id = resp_create.json()["id"]

    # Descargar CSV
    resp_csv = await client.get(
        f"/api/v1/solicitudes-derechos/{solicitud_id}/exportar-portabilidad?formato=csv",
        headers=tenant_admin_auth_headers,
    )
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    content_str = resp_csv.content.decode("utf-8-sig")
    assert "transaccion_id" in content_str
    assert "TX-1" in content_str
