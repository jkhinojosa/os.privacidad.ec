"""
OS Privacidad — Tests de Usuarios y Prevención de Escalamiento RBAC
===================================================================
Verifica creación de usuarios dentro del tenant y restricción contra escalamiento a SuperAdmin.
"""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tenant_admin_can_create_user(client: AsyncClient, tenant_admin_auth_headers: dict):
    """TenantAdmin puede crear un usuario dentro de su propio tenant."""
    unique_email = f"user-{uuid.uuid4().hex[:6]}@demo.ec"
    payload = {
        "email": unique_email,
        "password": "UserPass123!",
        "nombre": "Nuevo",
        "apellido": "Usuario",
        "rol": "analista",
    }
    response = await client.post(
        "/api/v1/usuarios", json=payload, headers=tenant_admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert data["rol"] == "analista"


@pytest.mark.asyncio
async def test_tenant_admin_cannot_create_superadmin(
    client: AsyncClient, tenant_admin_auth_headers: dict
):
    """TenantAdmin no puede crear un usuario con rol super_admin (403 Forbidden)."""
    payload = {
        "email": f"hacker-{uuid.uuid4().hex[:6]}@demo.ec",
        "password": "HackerPass123!",
        "nombre": "Escalation",
        "apellido": "Attempt",
        "rol": "super_admin",
    }
    response = await client.post(
        "/api/v1/usuarios", json=payload, headers=tenant_admin_auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_analista_cannot_create_users(client: AsyncClient, analista_auth_headers: dict):
    """Un Analista no tiene permisos para crear usuarios (403 Forbidden)."""
    payload = {
        "email": f"test-{uuid.uuid4().hex[:6]}@demo.ec",
        "password": "SomePass123!",
        "nombre": "Test",
        "apellido": "User",
        "rol": "analista",
    }
    response = await client.post("/api/v1/usuarios", json=payload, headers=analista_auth_headers)
    assert response.status_code == 403
