"""
OS Privacidad — Tests de Aislamiento Multi-Tenant (RLS) en Clientes
====================================================================
Verifica que las políticas de Row-Level Security en PostgreSQL
aíslen completamente los datos entre diferentes organizaciones/tenants.
"""

import pytest
from httpx import AsyncClient


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
    resp_get_cross_tenant = await client.get(
        f"/api/v1/clientes/{cliente_alpha_id}", headers=headers_beta
    )
    assert resp_get_cross_tenant.status_code == 404
