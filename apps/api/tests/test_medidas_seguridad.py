"""
OS Privacidad — Tests de Medidas de Seguridad
=============================================
Verifica la creación y actualización de controles de seguridad técnicos, organizativos, jurídicos y físicos.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_medidas_seguridad(
    client: AsyncClient, tenant_admin_auth_headers: dict
):
    """TenantAdmin puede registrar salvaguardas y listarlas con código MED-YYYY-NNNN."""
    payload = {
        "tipo": "tecnica",
        "nombre": "Seudonimización de Bases de Datos de Pacientes",
        "descripcion": "Reemplazo de identificadores directos por tokens criptográficos",
        "estado_implementacion": "implementada",
        "responsable": "Ing. Seguridad",
    }
    resp = await client.post(
        "/api/v1/medidas-seguridad", json=payload, headers=tenant_admin_auth_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["codigo"].startswith("MED-")
    assert data["tipo"] == "tecnica"
    medida_id = data["id"]

    # Listar
    resp_list = await client.get("/api/v1/medidas-seguridad", headers=tenant_admin_auth_headers)
    assert resp_list.status_code == 200
    assert any(m["id"] == medida_id for m in resp_list.json())

    # Consultar por ID
    resp_get = await client.get(
        f"/api/v1/medidas-seguridad/{medida_id}", headers=tenant_admin_auth_headers
    )
    assert resp_get.status_code == 200
    assert resp_get.json()["nombre"] == payload["nombre"]


@pytest.mark.asyncio
async def test_update_medida_seguridad(client: AsyncClient, tenant_admin_auth_headers: dict):
    """Verifica actualización del estado de implementación de una medida."""
    payload = {
        "tipo": "organizativa",
        "nombre": "Plan de Capacitación LOPDP Anual",
        "descripcion": "Talleres para empleados sobre protección de datos",
        "estado_implementacion": "planificada",
    }
    resp_create = await client.post(
        "/api/v1/medidas-seguridad", json=payload, headers=tenant_admin_auth_headers
    )
    medida_id = resp_create.json()["id"]

    # Actualizar a 'verificada'
    resp_update = await client.patch(
        f"/api/v1/medidas-seguridad/{medida_id}",
        json={"estado_implementacion": "verificada"},
        headers=tenant_admin_auth_headers,
    )
    assert resp_update.status_code == 200
    assert resp_update.json()["estado_implementacion"] == "verificada"
