"""
OS Privacidad — Tests de Notificaciones a Encargados del Tratamiento (Art. 23 RGLOPDP)
======================================================================================
Verifica la emisión de órdenes de réplica vinculantes hacia los proveedores y encargados.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_notificar_encargado_flow(client: AsyncClient, tenant_admin_auth_headers: dict):
    """
    1. Crear y aprobar solicitud de Supresión (Eliminación).
    2. Emitir notificación a encargado del tratamiento (Hosting / CRM).
    3. Verificar que la solicitud registre la notificación y actualice su estado a 'notificada_encargados'.
    """
    # 1. Crear solicitud de Eliminación
    sol_payload = {
        "tipo_derecho": "eliminacion",
        "titular_nombre": "Gabriel Salgado",
        "titular_identificacion": "0102030405",
        "titular_email": "gabriel.salgado@email.ec",
        "motivo_solicitud": "Solicito la supresión de mis datos tras darme de baja del servicio.",
    }
    resp_create = await client.post("/api/v1/solicitudes-derechos", json=sol_payload, headers=tenant_admin_auth_headers)
    solicitud_id = resp_create.json()["id"]

    # 1.1 Aprobar
    resp_resol = await client.post(
        f"/api/v1/solicitudes-derechos/{solicitud_id}/resolver",
        json={"aprobada": True, "dictamen_dpd": "DICTAMEN FAVORABLE: Procede la supresión."},
        headers=tenant_admin_auth_headers,
    )
    assert resp_resol.status_code == 200

    # 2. Notificar a Encargado
    notif_payload = {
        "encargado_nombre": "DataWarehouse Andina Cía. Ltda.",
        "encargado_email": "soporte-dpo@datawarehouse.ec",
        "tipo_accion_requerida": "suprimir",
        "instrucciones_tecnicas": "Ejecutar borrado criptográfico del registro titular_id 0102030405 en tablas de analytics.",
    }
    resp_notif = await client.post(
        f"/api/v1/solicitudes-derechos/{solicitud_id}/notificar-encargados",
        json=notif_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_notif.status_code == 201
    notif_data = resp_notif.json()
    assert notif_data["encargado_nombre"] == notif_payload["encargado_nombre"]
    assert notif_data["estado"] == "enviada"

    # 3. Verificar en solicitud
    resp_get = await client.get(f"/api/v1/solicitudes-derechos/{solicitud_id}", headers=tenant_admin_auth_headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["estado"] == "notificada_encargados"
    assert len(resp_get.json()["notificaciones_encargados"]) == 1
