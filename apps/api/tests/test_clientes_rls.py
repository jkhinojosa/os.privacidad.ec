"""
OS Privacidad — Tests de Aislamiento Multi-Tenant (RLS) en Clientes
====================================================================
Verifica que las políticas de Row-Level Security en PostgreSQL
aíslen completamente los datos entre diferentes organizaciones/tenants.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import create_access_token, hash_password
from models.tenant import Tenant, TenantPlan
from models.usuario import UserRole, Usuario


@pytest.fixture
async def multi_tenant_setup(db_session: AsyncSession):
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
        extra_claims={"email": user_alpha.email, "rol": user_alpha.rol.value, "tenant_id": str(tenant_alpha.id)},
    )
    token_beta = create_access_token(
        subject=user_beta.id,
        extra_claims={"email": user_beta.email, "rol": user_beta.rol.value, "tenant_id": str(tenant_beta.id)},
    )

    return {
        "tenant_alpha": tenant_alpha,
        "user_alpha": user_alpha,
        "headers_alpha": {"Authorization": f"Bearer {token_alpha}"},
        "tenant_beta": tenant_beta,
        "user_beta": user_beta,
        "headers_beta": {"Authorization": f"Bearer {token_beta}"},
    }


@pytest.mark.asyncio
async def test_cross_tenant_isolation_rls(client: AsyncClient, multi_tenant_setup: dict):
    """
    Test fundamental de RLS:
    1. Tenant Alpha crea un Cliente 'Cliente Alpha Confidencial'.
    2. Tenant Alpha puede verlo y consultarlo.
    3. Tenant Beta lista clientes y NO ve el cliente de Alpha.
    4. Tenant Beta intenta acceder directamente al ID de Alpha y recibe 404 (aislamiento RLS).
    """
    headers_alpha = multi_tenant_setup["headers_alpha"]
    headers_beta = multi_tenant_setup["headers_beta"]

    # 1. Tenant Alpha crea cliente
    payload_alpha = {
        "nombre_razon_social": "Cliente Alpha Confidencial S.A.",
        "ruc": "1791112223001",
        "sector": "Fintech",
        "contacto_principal_nombre": "Juan Pérez",
        "contacto_principal_email": "juan@alpha-confidencial.ec",
    }
    resp_create = await client.post("/api/v1/clientes", json=payload_alpha, headers=headers_alpha)
    assert resp_create.status_code == 201
    cliente_alpha_id = resp_create.json()["id"]

    # 2. Tenant Alpha lista clientes y lo ve
    resp_list_alpha = await client.get("/api/v1/clientes", headers=headers_alpha)
    assert resp_list_alpha.status_code == 200
    alpha_client_ids = [c["id"] for c in resp_list_alpha.json()]
    assert cliente_alpha_id in alpha_client_ids

    # 3. Tenant Beta lista clientes -> NO debe ver a Alpha
    resp_list_beta = await client.get("/api/v1/clientes", headers=headers_beta)
    assert resp_list_beta.status_code == 200
    beta_client_ids = [c["id"] for c in resp_list_beta.json()]
    assert cliente_alpha_id not in beta_client_ids

    # 4. Tenant Beta intenta acceder directamente al ID del cliente de Alpha -> 404 NOT FOUND
    resp_get_cross_tenant = await client.get(f"/api/v1/clientes/{cliente_alpha_id}", headers=headers_beta)
    assert resp_get_cross_tenant.status_code == 404
