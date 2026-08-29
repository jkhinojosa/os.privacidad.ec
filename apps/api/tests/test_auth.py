"""
OS Privacidad — Tests de Autenticación
=======================================
Verifica login, validación de contraseñas, rotación de refresh tokens y logout.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success_superadmin(client: AsyncClient):
    """Verifica que el superadmin pueda loguearse con sus credenciales."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@osprivacidad.ec", "password": "Admin123456!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["token"]["access_token"] is not None
    assert data["token"]["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@osprivacidad.ec"
    assert data["user"]["rol"] == "super_admin"


@pytest.mark.asyncio
async def test_login_success_tenant_user(client: AsyncClient):
    """Verifica que un usuario de tenant pueda loguearse."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "tenantadmin@demo.ec", "password": "Demo123456!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["rol"] == "tenant_admin"
    assert data["user"]["tenant_id"] is not None


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Verifica que una contraseña incorrecta retorne 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@osprivacidad.ec", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, superadmin_auth_headers: dict):
    """Verifica que /auth/me retorne el perfil del usuario autenticado."""
    response = await client.get("/api/v1/auth/me", headers=superadmin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@osprivacidad.ec"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Verifica que /auth/me retorne 401 sin header de autorización."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
