"""
OS Privacidad — Tests de Aislamiento Multi-Tenant (RLS) Fase 2
===============================================================
Verifica que las actividades de tratamiento, casos y expedientes
estén 100% aislados entre diferentes organizaciones mediante RLS.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_fase2_cross_tenant_isolation(client: AsyncClient, multi_tenant_setup: dict):
    """
    1. Tenant Alpha crea un Proceso, un Caso y un Expediente confidenciales.
    2. Tenant Beta lista y NO debe ver ninguno de los registros de Alpha.
    3. Tenant Beta intenta acceder directamente a los IDs de Alpha y recibe 404.
    """
    headers_alpha = multi_tenant_setup["headers_alpha"]
    headers_beta = multi_tenant_setup["headers_beta"]

    # ── 1. Tenant Alpha crea Proceso, Caso y Expediente ──────────
    proc_resp = await client.post(
        "/api/v1/procesos",
        json={
            "nombre": "Tratamiento Datos Biométricos Alpha",
            "area_responsable": "Seguridad Alpha",
            "base_legal": "consentimiento",
            "finalidad": "Control de acceso biométrico",
        },
        headers=headers_alpha,
    )
    assert proc_resp.status_code == 201
    proc_alpha_id = proc_resp.json()["id"]

    caso_resp = await client.post(
        "/api/v1/casos",
        json={
            "titulo": "Incidente Crítico Confidencial Alpha",
            "descripcion": "Detalles ultra secretos de Alpha",
            "tipo": "incidente_seguridad",
            "prioridad": "critica",
        },
        headers=headers_alpha,
    )
    assert caso_resp.status_code == 201
    caso_alpha_id = caso_resp.json()["id"]

    exp_resp = await client.post(
        "/api/v1/expedientes",
        json={
            "nombre": "Expediente Jurídico Alpha",
            "descripcion": "Dictamen confidencial",
            "caso_id": caso_alpha_id,
        },
        headers=headers_alpha,
    )
    assert exp_resp.status_code == 201
    exp_alpha_id = exp_resp.json()["id"]

    # ── 2. Tenant Beta lista y NO debe ver los registros de Alpha ──
    # Procesos
    beta_procs = (await client.get("/api/v1/procesos", headers=headers_beta)).json()
    assert not any(p["id"] == proc_alpha_id for p in beta_procs)

    # Casos
    beta_casos = (await client.get("/api/v1/casos", headers=headers_beta)).json()
    assert not any(c["id"] == caso_alpha_id for c in beta_casos)

    # Expedientes
    beta_exps = (await client.get("/api/v1/expedientes", headers=headers_beta)).json()
    assert not any(e["id"] == exp_alpha_id for e in beta_exps)

    # ── 3. Tenant Beta intenta acceso directo por ID -> 404 ───────
    assert (
        await client.get(f"/api/v1/procesos/{proc_alpha_id}", headers=headers_beta)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/casos/{caso_alpha_id}", headers=headers_beta)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/expedientes/{exp_alpha_id}", headers=headers_beta)
    ).status_code == 404
