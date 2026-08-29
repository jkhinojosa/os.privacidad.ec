"""
OS Privacidad — Test Configuration (conftest.py)
==================================================
Fixtures compartidas para tests de API, autenticación, RBAC y aislamiento RLS.
"""

from __future__ import annotations

import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

# Forzar entorno testing antes de importar la app
os.environ["API_ENV"] = "testing"
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-characters-long-for-testing")

from core.security import create_access_token, hash_password
from db.session import async_session_maker
from main import app
from models.tenant import Tenant, TenantPlan
from models.usuario import UserRole, Usuario


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


@pytest.fixture
async def multi_tenant_setup(db_session):
    """
    Crea dos tenants independientes (Tenant Alpha y Tenant Beta)
    con sus respectivos administradores para probar el aislamiento RLS.
    """
    # ── Tenant Alpha ─────────────────────────────────────────────
    tenant_alpha = Tenant(
        id=uuid.uuid4(),
        nombre="Organización Alpha",
        slug=f"alpha-{uuid.uuid4().hex[:6]}",
        plan=TenantPlan.professional,
    )
    db_session.add(tenant_alpha)
    await db_session.flush()

    user_alpha = Usuario(
        id=uuid.uuid4(),
        tenant_id=tenant_alpha.id,
        email=f"admin@{tenant_alpha.slug}.ec",
        password_hash=hash_password("Password123!"),
        nombre="Admin",
        apellido="Alpha",
        rol=UserRole.tenant_admin,
    )
    db_session.add(user_alpha)

    # ── Tenant Beta ──────────────────────────────────────────────
    tenant_beta = Tenant(
        id=uuid.uuid4(),
        nombre="Organización Beta",
        slug=f"beta-{uuid.uuid4().hex[:6]}",
        plan=TenantPlan.enterprise,
    )
    db_session.add(tenant_beta)
    await db_session.flush()

    user_beta = Usuario(
        id=uuid.uuid4(),
        tenant_id=tenant_beta.id,
        email=f"admin@{tenant_beta.slug}.ec",
        password_hash=hash_password("Password123!"),
        nombre="Admin",
        apellido="Beta",
        rol=UserRole.tenant_admin,
    )
    db_session.add(user_beta)
    await db_session.commit()

    token_alpha = create_access_token(
        subject=user_alpha.id,
        extra_claims={
            "email": user_alpha.email,
            "rol": user_alpha.rol.value,
            "tenant_id": str(tenant_alpha.id),
        },
    )
    token_beta = create_access_token(
        subject=user_beta.id,
        extra_claims={
            "email": user_beta.email,
            "rol": user_beta.rol.value,
            "tenant_id": str(tenant_beta.id),
        },
    )

    return {
        "tenant_alpha": tenant_alpha,
        "user_alpha": user_alpha,
        "headers_alpha": {"Authorization": f"Bearer {token_alpha}"},
        "tenant_beta": tenant_beta,
        "user_beta": user_beta,
        "headers_beta": {"Authorization": f"Bearer {token_beta}"},
    }
