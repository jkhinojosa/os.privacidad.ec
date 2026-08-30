"""
OS Privacidad — Tests de Aislamiento Multi-Tenant (RLS) Fase 4
===============================================================
Verifica que las solicitudes de derechos y notificaciones a encargados
estén 100% aisladas entre diferentes organizaciones mediante RLS.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_fase4_cross_tenant_isolation(client: AsyncClient, multi_tenant_setup: dict):
    """
    1. Tenant Alpha registra solicitud confidencial de derechos y notifica a su encargado.
    2. Tenant Beta lista solicitudes y NO debe ver la solicitud de Alpha.
    3. Tenant Beta intenta acceso directo por ID -> 404 NOT FOUND.
    """
    headers_alpha = multi_tenant_setup["headers_alpha"]
    headers_beta = multi_tenant_setup["headers_beta"]

    # ── 1. Tenant Alpha crea Solicitud de Oposición ───────────────
    sol_payload = {
        "tipo_derecho": "oposicion",
        "canal_recepcion": "formulario_web",
        "titular_nombre": "Directivo Confidencial Alpha",
        "titular_identificacion": "1799887766",
        "titular_email": "directivo@alpha.ec",
        "motivo_solicitud": "Oposición a la elaboración de perfiles comerciales automatizados.",
    }
    resp_alpha = await client.post(
        "/api/v1/solicitudes-derechos", json=sol_payload, headers=headers_alpha
    )
    assert resp_alpha.status_code == 201
    sol_alpha_id = resp_alpha.json()["id"]

    # Notificar a encargado de Alpha
    notif_payload = {
        "encargado_nombre": "Proveedor Marketing Alpha S.A.",
        "encargado_email": "privacidad@marketingalpha.ec",
        "tipo_accion_requerida": "oponerse",
        "instrucciones_tecnicas": "Excluir de listas de envíos automatizados.",
    }
    resp_notif = await client.post(
        f"/api/v1/solicitudes-derechos/{sol_alpha_id}/notificar-encargados",
        json=notif_payload,
        headers=headers_alpha,
    )
    assert resp_notif.status_code == 201

    # ── 2. Tenant Beta lista y NO debe ver la solicitud de Alpha ──
    beta_sols = (await client.get("/api/v1/solicitudes-derechos", headers=headers_beta)).json()
    assert not any(s["id"] == sol_alpha_id for s in beta_sols)

    # ── 3. Tenant Beta intenta acceso directo por ID -> 404 ───────
    assert (
        await client.get(f"/api/v1/solicitudes-derechos/{sol_alpha_id}", headers=headers_beta)
    ).status_code == 404
    assert (
        await client.get(
            f"/api/v1/solicitudes-derechos/{sol_alpha_id}/exportar-portabilidad",
            headers=headers_beta,
        )
    ).status_code == 404
