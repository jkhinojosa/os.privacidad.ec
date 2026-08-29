"""
OS Privacidad — Tests de Expedientes
====================================
Verifica creación, vinculación a casos y consulta de expedientes documentales.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_expedientes(client: AsyncClient, tenant_admin_auth_headers: dict):
    """TenantAdmin puede crear y listar expedientes con código correlativo EXP-YYYY-NNNN."""
    payload = {
        "nombre": "Expediente de Cumplimiento Regulatorio 2026",
        "descripcion": "Compilación de dictámenes jurídicos y evidencias de auditoría",
        "estado": "activo",
    }
    resp = await client.post("/api/v1/expedientes", json=payload, headers=tenant_admin_auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["codigo"].startswith("EXP-")
    assert data["nombre"] == payload["nombre"]
    exp_id = data["id"]

    # Listar
    resp_list = await client.get("/api/v1/expedientes", headers=tenant_admin_auth_headers)
    assert resp_list.status_code == 200
    assert any(e["id"] == exp_id for e in resp_list.json())


@pytest.mark.asyncio
async def test_link_expediente_to_caso(client: AsyncClient, tenant_admin_auth_headers: dict):
    """Verifica vincular un expediente a un caso específico."""
    # 1. Crear caso
    caso_payload = {
        "titulo": "Investigación Brecha de Datos Servidor Web",
        "descripcion": "Análisis forense de logs",
        "tipo": "incidente_seguridad",
        "prioridad": "critica",
    }
    caso_resp = await client.post(
        "/api/v1/casos", json=caso_payload, headers=tenant_admin_auth_headers
    )
    caso_id = caso_resp.json()["id"]

    # 2. Crear expediente vinculado
    exp_payload = {
        "nombre": "Dossier Forense y Cadena de Custodia",
        "descripcion": "Imágenes de disco y volcados de memoria",
        "caso_id": caso_id,
        "estado": "activo",
    }
    exp_resp = await client.post(
        "/api/v1/expedientes", json=exp_payload, headers=tenant_admin_auth_headers
    )
    assert exp_resp.status_code == 201
    assert exp_resp.json()["caso_id"] == caso_id

    # 3. Filtrar expedientes por caso_id
    filter_resp = await client.get(
        f"/api/v1/expedientes?caso_id={caso_id}", headers=tenant_admin_auth_headers
    )
    assert filter_resp.status_code == 200
    assert len(filter_resp.json()) == 1
    assert filter_resp.json()[0]["id"] == exp_resp.json()["id"]
