"""
OS Privacidad — Tests de Casos y Máquina de Estados (3.1)
==========================================================
Verifica la creación de casos con numeración correlativa y el cumplimiento
estricto de las transiciones permitidas y prohibidas de la máquina de estados.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_caso_generates_sequential_code(
    client: AsyncClient, tenant_admin_auth_headers: dict
):
    """Verifica que al crear casos se genere código correlativo CAS-YYYY-NNNN."""
    payload1 = {
        "titulo": "Fuga de correos masivos sin CCO",
        "descripcion": "Un empleado envió un comunicado a 500 clientes con los correos visibles",
        "tipo": "incidente_seguridad",
        "prioridad": "alta",
    }
    resp1 = await client.post("/api/v1/casos", json=payload1, headers=tenant_admin_auth_headers)
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["codigo"].startswith("CAS-")
    assert data1["estado"] == "abierto"

    payload2 = {
        "titulo": "Solicitud de Supresión Derecho ARCO",
        "descripcion": "Titular solicita eliminación de datos de base de marketing",
        "tipo": "derecho_arco",
        "prioridad": "media",
    }
    resp2 = await client.post("/api/v1/casos", json=payload2, headers=tenant_admin_auth_headers)
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["codigo"].startswith("CAS-")
    assert data2["codigo"] != data1["codigo"]


@pytest.mark.asyncio
async def test_valid_state_transitions_flow(client: AsyncClient, tenant_admin_auth_headers: dict):
    """
    Flujo válido:
    abierto ➔ en_investigacion ➔ en_comite ➔ cerrado
    """
    # 1. Crear caso (inicia en 'abierto')
    payload = {
        "titulo": "Auditoría de Cumplimiento LOPDP Anual",
        "descripcion": "Revisión integral de medidas técnicas y organizativas",
        "tipo": "auditoria",
        "prioridad": "alta",
    }
    resp = await client.post("/api/v1/casos", json=payload, headers=tenant_admin_auth_headers)
    caso_id = resp.json()["id"]
    assert resp.json()["estado"] == "abierto"

    # 2. Transición: abierto -> en_investigacion
    resp_inv = await client.post(
        f"/api/v1/casos/{caso_id}/transicion",
        json={"nuevo_estado": "en_investigacion", "motivo": "Se inicia recopilación de evidencias"},
        headers=tenant_admin_auth_headers,
    )
    assert resp_inv.status_code == 200
    assert resp_inv.json()["estado"] == "en_investigacion"

    # 3. Transición: en_investigacion -> en_comite
    resp_comite = await client.post(
        f"/api/v1/casos/{caso_id}/transicion",
        json={
            "nuevo_estado": "en_comite",
            "motivo": "Presentación de informe ante el Comité de Privacidad",
        },
        headers=tenant_admin_auth_headers,
    )
    assert resp_comite.status_code == 200
    assert resp_comite.json()["estado"] == "en_comite"

    # 4. Transición: en_comite -> cerrado
    resp_cerrado = await client.post(
        f"/api/v1/casos/{caso_id}/transicion",
        json={
            "nuevo_estado": "cerrado",
            "motivo": "Comité aprobó el plan de remediación",
            "resolucion": "Se implementaron las salvaguardas requeridas y se cerró la auditoría con éxito",
        },
        headers=tenant_admin_auth_headers,
    )
    assert resp_cerrado.status_code == 200
    assert resp_cerrado.json()["estado"] == "cerrado"
    assert resp_cerrado.json()["fecha_cierre"] is not None
    assert "salvaguardas" in resp_cerrado.json()["resolucion"]


@pytest.mark.asyncio
async def test_invalid_state_transition_fails(client: AsyncClient, tenant_admin_auth_headers: dict):
    """
    Transición inválida:
    abierto ➔ en_comite (debe fallar con 400 Bad Request)
    """
    payload = {
        "titulo": "Consulta Legal Contrato Proveedor",
        "descripcion": "Verificación de cláusulas de encargado de tratamiento",
        "tipo": "consulta_regulatoria",
        "prioridad": "baja",
    }
    resp = await client.post("/api/v1/casos", json=payload, headers=tenant_admin_auth_headers)
    caso_id = resp.json()["id"]

    # Intentar saltar directamente a en_comite
    resp_bad = await client.post(
        f"/api/v1/casos/{caso_id}/transicion",
        json={"nuevo_estado": "en_comite", "motivo": "Salto directo no permitido"},
        headers=tenant_admin_auth_headers,
    )
    assert resp_bad.status_code == 400
    err = resp_bad.json()["error"]
    assert err["code"] == "INVALID_STATE_TRANSITION"


@pytest.mark.asyncio
async def test_reopen_closed_caso(client: AsyncClient, tenant_admin_auth_headers: dict):
    """
    Reapertura de caso cerrado:
    abierto ➔ cerrado ➔ reabierto
    """
    # 1. Crear caso y cerrar directamente (transición permitida)
    payload = {
        "titulo": "Incidente Menor Bloqueado",
        "descripcion": "Intento de acceso bloqueado por WAF",
        "tipo": "incidente_seguridad",
        "prioridad": "baja",
    }
    resp = await client.post("/api/v1/casos", json=payload, headers=tenant_admin_auth_headers)
    caso_id = resp.json()["id"]

    # Cerrar
    resp_close = await client.post(
        f"/api/v1/casos/{caso_id}/transicion",
        json={"nuevo_estado": "cerrado", "motivo": "Sin impacto comprobado"},
        headers=tenant_admin_auth_headers,
    )
    assert resp_close.status_code == 200
    assert resp_close.json()["estado"] == "cerrado"
    assert resp_close.json()["fecha_cierre"] is not None

    # Reabrir (cerrado -> reabierto)
    resp_reopen = await client.post(
        f"/api/v1/casos/{caso_id}/transicion",
        json={
            "nuevo_estado": "reabierto",
            "motivo": "Se descubrió nueva evidencia de persistencia",
        },
        headers=tenant_admin_auth_headers,
    )
    assert resp_reopen.status_code == 200
    assert resp_reopen.json()["estado"] == "reabierto"
    assert resp_reopen.json()["fecha_cierre"] is None
