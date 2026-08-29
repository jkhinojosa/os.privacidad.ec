"""
OS Privacidad — Test Configuration (conftest.py)
==================================================
Fixtures compartidas para tests de API, autenticación, RBAC y aislamiento RLS.
"""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

# Forzar entorno testing antes de importar la app
os.environ["API_ENV"] = "testing"
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-characters-long-for-testing")

from db.session import async_session_maker
from main import app


@pytest.fixture
async def client():
    """Cliente HTTP async con ASGITransport para testear endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def db_session():
    """Sesión de base de datos para setup de fixtures."""
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def superadmin_auth_headers(client: AsyncClient) -> dict:
    """Header de autorización obtenido vía login real para SuperAdmin."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@osprivacidad.ec", "password": "Admin123456!"},
    )
    data = response.json()
    token = data["token"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def tenant_admin_auth_headers(client: AsyncClient) -> dict:
    """Header de autorización obtenido vía login real para TenantAdmin del Tenant Demo."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "tenantadmin@demo.ec", "password": "Demo123456!"},
    )
    data = response.json()
    token = data["token"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def analista_auth_headers(client: AsyncClient) -> dict:
    """Header de autorización obtenido vía login real para Analista del Tenant Demo."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "analista@demo.ec", "password": "Demo123456!"},
    )
    data = response.json()
    token = data["token"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
