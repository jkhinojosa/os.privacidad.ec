"""
OS Privacidad — Tests de Tenants y RBAC SuperAdmin
===================================================
Verifica creación, listado y restricción de endpoints de Tenants solo a SuperAdmin.
"""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_superadmin_can_list_tenants(client: AsyncClient, superadmin_auth_headers: dict):
    """SuperAdmin puede listar todos los tenants."""
    response = await client.get("/api/v1/tenants", headers=superadmin_auth_headers)
    assert response.status_code == 200
    tenants = response.json()
    assert isinstance(tenants, list)
    assert len(tenants) >= 1


@pytest.mark.asyncio
async def test_superadmin_can_create_tenant(client: AsyncClient, superadmin_auth_headers: dict):
    """SuperAdmin puede crear un nuevo tenant."""
    unique_slug = f"tenant-test-{uuid.uuid4().hex[:6]}"
    payload = {
        "nombre": "Tenant Test Automático",
        "slug": unique_slug,
        "plan": "professional",
    }
    response = await client.post("/api/v1/tenants", json=payload, headers=superadmin_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == unique_slug
    assert data["nombre"] == payload["nombre"]


@pytest.mark.asyncio
async def test_tenant_admin_cannot_access_tenants(client: AsyncClient, tenant_admin_auth_headers: dict):
    """Un usuario con rol tenant_admin no puede acceder a /tenants (403 Forbidden)."""
    response = await client.get("/api/v1/tenants", headers=tenant_admin_auth_headers)
    assert response.status_code == 403
