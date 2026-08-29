"""
OS Privacidad — Tests de Procesos (RAT)
=======================================
Verifica el registro, consulta y modificación de actividades de tratamiento.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_procesos(client: AsyncClient, tenant_admin_auth_headers: dict):
    """TenantAdmin puede registrar y consultar actividades de tratamiento."""
    payload = {
        "nombre": "Gestión de Nómina y Recursos Humanos",
        "descripcion": "Tratamiento de datos de empleados para pago de salarios y beneficios sociales",
        "area_responsable": "Talento Humano",
        "base_legal": "ejecucion_contrato",
        "finalidad": "Cumplimiento de obligaciones laborales y pago de remuneraciones",
        "tipo_datos": ["identificativos", "financieros", "laborales"],
    }
    # Crear proceso
    resp_create = await client.post(
        "/api/v1/procesos", json=payload, headers=tenant_admin_auth_headers
    )
    assert resp_create.status_code == 201
    data = resp_create.json()
    assert data["nombre"] == payload["nombre"]
    assert data["base_legal"] == payload["base_legal"]
    proceso_id = data["id"]

    # Listar procesos
    resp_list = await client.get("/api/v1/procesos", headers=tenant_admin_auth_headers)
    assert resp_list.status_code == 200
    procesos = resp_list.json()
    assert any(p["id"] == proceso_id for p in procesos)

    # Consultar por ID
    resp_get = await client.get(f"/api/v1/procesos/{proceso_id}", headers=tenant_admin_auth_headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["area_responsable"] == "Talento Humano"


@pytest.mark.asyncio
async def test_update_and_delete_proceso(client: AsyncClient, tenant_admin_auth_headers: dict):
    """TenantAdmin puede actualizar y dar de baja (soft delete) un proceso."""
    payload = {
        "nombre": "CCTV y Seguridad Física",
        "area_responsable": "Seguridad",
        "base_legal": "interes_legitimo",
        "finalidad": "Videovigilancia en instalaciones",
    }
    resp_create = await client.post(
        "/api/v1/procesos", json=payload, headers=tenant_admin_auth_headers
    )
    proceso_id = resp_create.json()["id"]

    # Update
    resp_update = await client.patch(
        f"/api/v1/procesos/{proceso_id}",
        json={"area_responsable": "Seguridad Corporativa"},
        headers=tenant_admin_auth_headers,
    )
    assert resp_update.status_code == 200
    assert resp_update.json()["area_responsable"] == "Seguridad Corporativa"

    # Soft Delete
    resp_delete = await client.delete(
        f"/api/v1/procesos/{proceso_id}", headers=tenant_admin_auth_headers
    )
    assert resp_delete.status_code == 204

    # Listar ya no lo incluye
    resp_list = await client.get("/api/v1/procesos", headers=tenant_admin_auth_headers)
    assert not any(p["id"] == proceso_id for p in resp_list.json())
