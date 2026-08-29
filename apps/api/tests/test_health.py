"""
OS Privacidad — Test: Health Check
====================================
Fase 0 — Definición de Hecho:
"GET /health responde 200"
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient):
    """
    Verifica que GET /api/v1/health retorna 200
    con los campos status, db y redis.
    """
    response = await client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "db" in data
    assert "redis" in data


@pytest.mark.asyncio
async def test_health_response_schema(client: AsyncClient):
    """
    Verifica que la respuesta del health check tiene la estructura correcta.
    """
    response = await client.get("/api/v1/health")
    data = response.json()

    # Los campos deben ser strings
    assert isinstance(data["status"], str)
    assert isinstance(data["db"], str)
    assert isinstance(data["redis"], str)

    # El status debe ser 'ok' o 'degraded'
    assert data["status"] in ("ok", "degraded")

    # db y redis deben ser 'connected', 'disconnected' o 'error'
    valid_states = ("connected", "disconnected", "error")
    assert data["db"] in valid_states
    assert data["redis"] in valid_states
