"""
OS Privacidad — Tests de Aislamiento Multi-Tenant (RLS) Fase 5
===============================================================
Verifica que las brechas de seguridad y sus informes técnicos oficiales
estén 100% aislados entre diferentes organizaciones mediante RLS.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_fase5_cross_tenant_isolation(client: AsyncClient, multi_tenant_setup: dict):
    """
    1. Tenant Alpha registra incidente crítico de vulneración de seguridad.
    2. Tenant Beta lista brechas y NO debe ver la brecha de Alpha.
    3. Tenant Beta intenta acceso directo por ID o informe SPDP -> 404 NOT FOUND.
    """
    headers_alpha = multi_tenant_setup["headers_alpha"]
    headers_beta = multi_tenant_setup["headers_beta"]

    # ── 1. Tenant Alpha crea Brecha de Seguridad ─────────────────
    create_payload = {
        "titulo": "Fuga de Tokens API Confidenciales de Alpha",
        "descripcion": "Exposición inadvertida de tokens de acceso al repositorio privado.",
        "tipo_vulneracion": "confidencialidad",
        "severidad": "alta",
        "sistemas_afectados": "Pipeline CI/CD y Servidor de Build Alpha",
        "causa_presunta": "Commit accidental en rama pública",
        "colectivos_afectados": ["Desarrolladores Alpha"],
        "volumen_titulares_estimado": 15,
        "categorias_datos_expuestas": ["credenciales_api", "correos_internos"],
        "medidas_contencion_inmediatas": "Revocación inmediata del token expuesto en el KMS.",
        "medidas_remediacion_previstas": "Instalación de hook pre-commit de escaneo de secretos (TruffleHog).",
    }
    resp_alpha = await client.post(
        "/api/v1/brechas-seguridad", json=create_payload, headers=headers_alpha
    )
    assert resp_alpha.status_code == 201
    brecha_alpha_id = resp_alpha.json()["id"]

    # ── 2. Tenant Beta lista y NO debe ver la brecha de Alpha ─────
    beta_brechas = (await client.get("/api/v1/brechas-seguridad", headers=headers_beta)).json()
    assert not any(b["id"] == brecha_alpha_id for b in beta_brechas)

    # ── 3. Tenant Beta intenta acceso directo -> 404 ─────────────
    assert (
        await client.get(f"/api/v1/brechas-seguridad/{brecha_alpha_id}", headers=headers_beta)
    ).status_code == 404
    assert (
        await client.get(
            f"/api/v1/brechas-seguridad/{brecha_alpha_id}/informe-spdp", headers=headers_beta
        )
    ).status_code == 404
