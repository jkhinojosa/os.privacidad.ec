"""
OS Privacidad — Tests de Aislamiento Multi-Tenant (RLS) Fase 3
===============================================================
Verifica que las medidas de seguridad, riesgos y evaluaciones de impacto
estén 100% aislados entre diferentes organizaciones mediante RLS.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_fase3_cross_tenant_isolation(client: AsyncClient, multi_tenant_setup: dict):
    """
    1. Tenant Alpha crea Medida, Proceso, Riesgo y EIPD confidenciales.
    2. Tenant Beta lista y NO debe ver ninguno de los registros de Alpha.
    3. Tenant Beta intenta acceder directamente a los IDs de Alpha y recibe 404.
    """
    headers_alpha = multi_tenant_setup["headers_alpha"]
    headers_beta = multi_tenant_setup["headers_beta"]

    # ── 1. Tenant Alpha crea Medida, Proceso, Riesgo y EIPD ──────
    med_resp = await client.post(
        "/api/v1/medidas-seguridad",
        json={
            "tipo": "tecnica",
            "nombre": "Cifrado Homomórfico Alpha",
            "descripcion": "Tecnología confidencial de Alpha",
        },
        headers=headers_alpha,
    )
    assert med_resp.status_code == 201
    med_alpha_id = med_resp.json()["id"]

    proc_resp = await client.post(
        "/api/v1/procesos",
        json={
            "nombre": "Proyecto Secreto Alpha",
            "area_responsable": "I+D Alpha",
            "base_legal": "consentimiento",
            "finalidad": "Desarrollo de IA",
        },
        headers=headers_alpha,
    )
    assert proc_resp.status_code == 201
    proc_alpha_id = proc_resp.json()["id"]

    rsk_resp = await client.post(
        "/api/v1/riesgos",
        json={
            "proceso_id": proc_alpha_id,
            "nombre": "Fuga de Algoritmos Secretos Alpha",
            "descripcion_amenaza": "Espionaje industrial",
            "vulnerabilidad": "Sin cifrado en reposo",
            "probabilidad_inherente": 4,
            "impacto_inherente": 5,
            "es_grupo_vulnerable": False,
        },
        headers=headers_alpha,
    )
    assert rsk_resp.status_code == 201
    rsk_alpha_id = rsk_resp.json()["id"]

    eipd_resp = await client.post(
        "/api/v1/eipds",
        json={
            "proceso_id": proc_alpha_id,
            "titulo": "EIPD Proyecto Secreto Alpha",
            "descripcion_sistematica": "Descripción confidencial de operaciones de IA",
            "justificacion_necesidad_proporcionalidad": "Justificación técnica confidencial",
        },
        headers=headers_alpha,
    )
    assert eipd_resp.status_code == 201
    eipd_alpha_id = eipd_resp.json()["id"]

    # ── 2. Tenant Beta lista y NO debe ver los registros de Alpha ──
    beta_meds = (await client.get("/api/v1/medidas-seguridad", headers=headers_beta)).json()
    assert not any(m["id"] == med_alpha_id for m in beta_meds)

    beta_rsks = (await client.get("/api/v1/riesgos", headers=headers_beta)).json()
    assert not any(r["id"] == rsk_alpha_id for r in beta_rsks)

    beta_eipds = (await client.get("/api/v1/eipds", headers=headers_beta)).json()
    assert not any(e["id"] == eipd_alpha_id for e in beta_eipds)

    # ── 3. Tenant Beta intenta acceso directo por ID -> 404 ───────
    assert (
        await client.get(f"/api/v1/medidas-seguridad/{med_alpha_id}", headers=headers_beta)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/riesgos/{rsk_alpha_id}", headers=headers_beta)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/eipds/{eipd_alpha_id}", headers=headers_beta)
    ).status_code == 404
