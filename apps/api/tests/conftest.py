"""
OS Privacidad — Test Configuration (conftest.py)
==================================================
Fixtures compartidas para todos los tests.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    """
    Cliente HTTP async para tests de la API.
    Usa ASGITransport para testear sin levantar un servidor real.
    """
    # Import diferido para evitar problemas de carga de config en tests
    import os

    # Setear variables de entorno para tests
    os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-characters-long-for-testing")
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://osprivacidad:changeme@localhost:5432/osprivacidad")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("API_ENV", "testing")

    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
