"""
OS Privacidad — Tests del Ciclo de Vida de Solicitudes de Derechos (LOPDP)
==========================================================================
Verifica el registro, cómputo de SLA, requerimiento de subsanación,
prórroga legal, dictamen del DPD, resolución y ejecución técnica.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_solicitud_derecho_full_lifecycle(
    client: AsyncClient, tenant_admin_auth_headers: dict
):
    """
    Flujo completo de atención:
    1. Registro de solicitud de Rectificación y Actualización (SOL-YYYY-NNNN) con SLA de 15 días hábiles.
    2. Aplicación de prórroga de 15 días por complejidad técnica.
    3. Resolución favorable con dictamen técnico del DPD.
    4. Ejecución técnica y cierre como 'atendida'.
    """
    # 1. Crear solicitud
    sol_payload = {
        "tipo_derecho": "rectificacion_actualizacion",
        "canal_recepcion": "formulario_web",
        "titular_nombre": "Carlos Vinicio Zambrano",
        "titular_identificacion": "1720304050",
        "titular_email": "carlos.zambrano@empresa.ec",
        "titular_telefono": "0987654321",
        "motivo_solicitud": "Solicito corregir mi dirección domiciliaria y número de teléfono celular registrados.",
        "datos_a_modificar": {"direccion_nueva": "Av. Amazonas y Colón, Quito", "celular_nuevo": "0987654321"},
    }
    resp_create = await client.post("/api/v1/solicitudes-derechos", json=sol_payload, headers=tenant_admin_auth_headers)
    assert resp_create.status_code == 201
    sol_data = resp_create.json()
    assert sol_data["codigo"].startswith("SOL-")
    assert sol_data["estado"] == "recibida"
    assert sol_data["dias_restantes_habiles"] >= 14
    assert sol_data["estado_semaforo"] == "en_tiempo"
    solicitud_id = sol_data["id"]

    # 2. Requerir prórroga de 15 días hábiles
    prorr_payload = {
        "motivo_prorroga": "Complejidad técnica debido a la necesidad de sincronizar 4 sistemas legacy distribuidos.",
        "dias_prorroga_habiles": 15,
    }
    resp_prorr = await client.post(
        f"/api/v1/solicitudes-derechos/{solicitud_id}/prorrogar",
        json=prorr_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_prorr.status_code == 200
    prorr_data = resp_prorr.json()
    assert prorr_data["estado"] == "prorrogada"
    assert prorr_data["prorroga_aplicada"] is True
    assert prorr_data["dias_prorroga"] == 15

    # 2.1 Intentar segunda prórroga debe fallar (máximo 1 prórroga por ley)
    resp_prorr_fail = await client.post(
        f"/api/v1/solicitudes-derechos/{solicitud_id}/prorrogar",
        json=prorr_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_prorr_fail.status_code == 400

    # 3. Resolver favorablemente con dictamen DPD
    resol_payload = {
        "aprobada": True,
        "dictamen_dpd": "DICTAMEN FAVORABLE: Se constató la legitimidad del titular y la veracidad de los nuevos datos.",
    }
    resp_resol = await client.post(
        f"/api/v1/solicitudes-derechos/{solicitud_id}/resolver",
        json=resol_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_resol.status_code == 200
    resol_data = resp_resol.json()
    assert resol_data["estado"] == "aprobada"
    assert resol_data["dictamen_dpd"] == resol_payload["dictamen_dpd"]

    # 4. Ejecución técnica y cierre
    exec_payload = {
        "resultado_ejecucion": "Datos actualizados exitosamente en CRM y base de datos central.",
        "marcar_atendida": True,
    }
    resp_exec = await client.post(
        f"/api/v1/solicitudes-derechos/{solicitud_id}/ejecutar",
        json=exec_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_exec.status_code == 200
    exec_data = resp_exec.json()
    assert exec_data["estado"] == "atendida"
    assert exec_data["ejecucion_tecnica_completada"] is True
    assert exec_data["fecha_cierre"] is not None


@pytest.mark.asyncio
async def test_solicitud_subsanacion_flow(
    client: AsyncClient, tenant_admin_auth_headers: dict
):
    """Verifica el flujo de requerimiento de subsanación de 10 días al titular."""
    sol_payload = {
        "tipo_derecho": "eliminacion",
        "titular_nombre": "Paola Paredes",
        "titular_identificacion": "1801234567",
        "titular_email": "paola.paredes@email.ec",
        "motivo_solicitud": "Quiero que borren mis datos.",
    }
    resp = await client.post("/api/v1/solicitudes-derechos", json=sol_payload, headers=tenant_admin_auth_headers)
    solicitud_id = resp.json()["id"]

    sub_payload = {
        "motivo_subsanacion": "Por favor adjunte copia de cédula legible y especifique de qué servicio solicita la supresión.",
        "dias_plazo_titular": 10,
    }
    resp_sub = await client.post(
        f"/api/v1/solicitudes-derechos/{solicitud_id}/subsanar",
        json=sub_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_sub.status_code == 200
    assert resp_sub.json()["estado"] == "en_subsanacion"
    assert resp_sub.json()["fecha_subsanacion_limite"] is not None


@pytest.mark.asyncio
async def test_resumen_sla_metrics(
    client: AsyncClient, tenant_admin_auth_headers: dict
):
    """Verifica que el endpoint de resumen SLA retorne las métricas cuantitativas."""
    resp = await client.get("/api/v1/solicitudes-derechos/resumen-sla", headers=tenant_admin_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_solicitudes" in data
    assert "en_tiempo" in data
    assert "porcentaje_cumplimiento" in data
