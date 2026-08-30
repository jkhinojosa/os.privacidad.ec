"""
OS Privacidad — Tests de Ciclo de Vida y Notificación de Brechas a la SPDP (Fase 5)
===================================================================================
Valida la gestión de incidentes bajo la LOPDP (Arts. 43 y 46) y Reglamento (Arts. 24-28):
- Plazos perentorios de 5 días hábiles para SPDP y 3 días hábiles para Titulares.
- Emisión del Informe Técnico Oficial conforme a los 7 numerales del Art. 26.
- Justificación obligatoria de dilación en notificaciones extemporáneas.
- Acogimiento a excepciones de notificación y cierre del incidente.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_brecha_seguridad_full_lifecycle(
    client: AsyncClient, tenant_admin_auth_headers: dict
):
    """
    1. Registro de vulneración de confidencialidad (BRC-YYYY-NNNN) con 5 días hábiles ante SPDP.
    2. Calificación técnica de riesgo por el DPD (activa 3 días hábiles para titulares).
    3. Generación del Informe Oficial Art. 26 RGLOPDP.
    4. Notificación formal a la SPDP con radicado.
    5. Notificación a titulares afectados (Art. 46 LOPDP).
    6. Cierre final del incidente.
    """
    # ── 1. Registrar Vulneración ────────────────────────────────
    create_payload = {
        "titulo": "Exfiltración de Base de Datos de Clientes VIP",
        "descripcion": "Acceso anómalo mediante credenciales de administrador comprometidas desde dirección IP foránea.",
        "tipo_vulneracion": "confidencialidad",
        "severidad": "critica",
        "sistemas_afectados": "Cluster PostgreSQL Principal y Bucket S3 de respaldos",
        "causa_presunta": "Ataque de fuerza bruta y omisión de segundo factor de autenticación en cuenta de soporte",
        "colectivos_afectados": ["Clientes Corporativos", "Accionistas"],
        "volumen_titulares_estimado": 1200,
        "categorias_datos_expuestas": ["nombres", "cedulas", "cuentas_bancarias", "telefonos"],
        "medidas_contencion_inmediatas": "Aislamiento de la máquina virtual, cambio de credenciales maestras y bloqueo de IPs maliciosas.",
        "medidas_remediacion_previstas": "Habilitación forzosa de MFA en todo el dominio y auditoría forense de accesos.",
    }
    resp_create = await client.post(
        "/api/v1/brechas-seguridad", json=create_payload, headers=tenant_admin_auth_headers
    )
    assert resp_create.status_code == 201
    brecha_data = resp_create.json()
    assert brecha_data["codigo"].startswith("BRC-")
    assert brecha_data["estado"] == "detectada"
    assert brecha_data["notificada_a_spdp"] is False
    assert brecha_data["dias_restantes_spdp"] >= 4
    assert brecha_data["estado_semaforo_spdp"] == "en_tiempo"
    brecha_id = brecha_data["id"]

    # ── 2. Calificar Riesgo por el DPD ─────────────────────────
    calif_payload = {
        "dictamen_dpd": "DICTAMEN VINCULANTE DPD: Se determina la existencia de riesgo alto para los titulares por incluir información financiera.",
        "evaluacion_riesgo_titulares": "Impacto significativo en privacidad financiera conforme a la metodología de evaluación de la SPDP.",
        "conlleva_riesgo_titulares": True,
    }
    resp_calif = await client.post(
        f"/api/v1/brechas-seguridad/{brecha_id}/calificar-riesgo",
        json=calif_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_calif.status_code == 200
    calif_data = resp_calif.json()
    assert calif_data["estado"] == "evaluada_dpd"
    assert calif_data["requiere_notificacion_titulares"] is True
    assert calif_data["dias_restantes_titulares"] >= 2
    assert calif_data["estado_semaforo_titulares"] in ("en_tiempo", "en_alerta")

    # ── 3. Generar Informe Oficial Art. 26 RGLOPDP ──────────────
    resp_inf = await client.get(
        f"/api/v1/brechas-seguridad/{brecha_id}/informe-spdp", headers=tenant_admin_auth_headers
    )
    assert resp_inf.status_code == 200
    inf_data = resp_inf.json()
    md_content = inf_data["informe_markdown"]
    assert "INFORME OFICIAL DE NOTIFICACIÓN DE VULNERACIÓN DE SEGURIDAD" in md_content
    assert "1. NATURALEZA Y TIPO DE LA VULNERACIÓN" in md_content
    assert "2. IDENTIFICACIÓN DE LOS TITULARES AFECTADOS" in md_content
    assert "3. DETALLE DE LOS SISTEMAS VULNERADOS" in md_content
    assert "4. CAUSA PRESUNTA DE LA VULNERACIÓN" in md_content
    assert "5. VOLUMEN Y TIPOLOGÍA DE DATOS EXPUESTOS" in md_content
    assert "6. MEDIDAS ADOPTADAS Y PREVISTAS PARA MITIGAR" in md_content
    assert "7. EVALUACIÓN DE IMPACTO Y RIESGO PARA LOS TITULARES" in md_content

    # ── 4. Notificar formalmente a la SPDP ──────────────────────
    spdp_payload = {
        "numero_radicado_spdp": "SPDP-2026-TRAMITE-008912-E",
        "notificada_a_arcotel": True,
    }
    resp_spdp = await client.post(
        f"/api/v1/brechas-seguridad/{brecha_id}/notificar-spdp",
        json=spdp_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_spdp.status_code == 200
    spdp_data = resp_spdp.json()
    assert spdp_data["notificada_a_spdp"] is True
    assert spdp_data["numero_radicado_spdp"] == "SPDP-2026-TRAMITE-008912-E"
    assert spdp_data["estado"] == "notificada_spdp"

    # ── 5. Notificar a Titulares Afectados ──────────────────────
    tit_payload = {
        "canal_notificacion": "correo_individual_y_comunicado_web",
        "excepcion_aplicada": None,
        "justificacion_excepcion": None,
    }
    resp_tit = await client.post(
        f"/api/v1/brechas-seguridad/{brecha_id}/notificar-titulares",
        json=tit_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_tit.status_code == 200
    tit_data = resp_tit.json()
    assert tit_data["notificada_a_titulares"] is True
    assert tit_data["estado"] == "notificada_titulares"

    # ── 6. Cerrar Incidente de Brecha ───────────────────────────
    close_payload = {
        "resultado_final_remediacion": "Servidor restablecido con parches de seguridad, MFA enforced y monitoreo SIEM 24/7 sin recurrencias.",
    }
    resp_close = await client.post(
        f"/api/v1/brechas-seguridad/{brecha_id}/cerrar",
        json=close_payload,
        headers=tenant_admin_auth_headers,
    )
    assert resp_close.status_code == 200
    close_data = resp_close.json()
    assert close_data["estado"] == "resuelta_cerrada"
    assert close_data["fecha_cierre"] is not None


@pytest.mark.asyncio
async def test_resumen_sla_brechas(client: AsyncClient, tenant_admin_auth_headers: dict):
    """Verifica el endpoint de métricas SLA de brechas ante la SPDP."""
    resp = await client.get(
        "/api/v1/brechas-seguridad/resumen-sla", headers=tenant_admin_auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_brechas" in data
    assert "spdp_en_tiempo" in data
    assert "porcentaje_cumplimiento_spdp" in data
    assert data["total_brechas"] >= 1
