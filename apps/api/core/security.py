"""
OS Privacidad — Seguridad (JWT + Password Hashing + Redis Revocación)
=====================================================================
Utilidades de criptografía, hashing con bcrypt y tokens JWT con rotación.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import redis.asyncio as aioredis
from jose import jwt

from core.config import settings


# ── Password Hashing con bcrypt nativo ───────────────────────
def hash_password(password: str) -> str:
    """Hashea una contraseña de forma segura usando bcrypt nativo."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica una contraseña en texto plano contra su hash bcrypt."""
    try:
        pwd_bytes = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False


# ── Redis Client para Gestión de Tokens ─────────────────────
async def get_redis_client() -> aioredis.Redis:
    """Obtiene un cliente Redis asíncrono configurado."""
    return aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


# ── JWT Tokens ──────────────────────────────────────────────
def create_access_token(
    subject: str | uuid.UUID,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Crea un JWT de acceso con tiempo de expiración corto (default 15 min).
    """
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    )
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str | uuid.UUID,
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    """
    Crea un JWT de refresh con jti único para rotación y revocación en Redis.
    Retorna (token_string, jti).
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + (expires_delta or timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS))
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
    }
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    """
    Decodifica y valida un JWT. Lanza JWTError si es inválido o expiró.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


# ── Token Tracking / Revocación en Redis ─────────────────────
async def save_refresh_token(user_id: str | uuid.UUID, jti: str, expires_in_seconds: int) -> None:
    """Almacena el jti activo de refresh token en Redis."""
    redis = await get_redis_client()
    key = f"refresh_token:{user_id}:{jti}"
    await redis.set(key, "valid", ex=expires_in_seconds)


async def is_refresh_token_valid(user_id: str | uuid.UUID, jti: str) -> bool:
    """Verifica si el refresh token sigue activo en Redis."""
    redis = await get_redis_client()
    key = f"refresh_token:{user_id}:{jti}"
    val = await redis.get(key)
    return val == "valid"


async def revoke_refresh_token(user_id: str | uuid.UUID, jti: str) -> None:
    """Invalida un refresh token específico."""
    redis = await get_redis_client()
    key = f"refresh_token:{user_id}:{jti}"
    await redis.delete(key)


async def revoke_all_user_tokens(user_id: str | uuid.UUID) -> None:
    """Revoca todas las sesiones activas de un usuario."""
    redis = await get_redis_client()
    pattern = f"refresh_token:{user_id}:*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)
