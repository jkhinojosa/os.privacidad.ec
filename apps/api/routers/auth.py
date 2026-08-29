"""
OS Privacidad — Router de Autenticación
=======================================
Endpoints para login, refresco de sesión, logout y obtención del perfil de usuario.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.deps import get_current_user, get_db, log_audit
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    is_refresh_token_valid,
    revoke_refresh_token,
    save_refresh_token,
    verify_password,
)
from models.usuario import Usuario
from schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Inicia sesión con email y contraseña.
    Retorna access token y perfil de usuario, configurando refresh token en cookie httpOnly.
    """
    stmt = select(Usuario).where(Usuario.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Credenciales inválidas"}},
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "USER_INACTIVE", "message": "Usuario inactivo"}},
        )

    # Claims del access token
    access_claims = {
        "email": user.email,
        "rol": user.rol.value,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
    }
    access_token = create_access_token(subject=user.id, extra_claims=access_claims)
    refresh_token, jti = create_refresh_token(subject=user.id)

    # Registrar refresh token en Redis
    refresh_expire_seconds = settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 3600
    await save_refresh_token(user.id, jti, refresh_expire_seconds)

    # Setear cookie httpOnly para refresh token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.API_ENV == "production",
        samesite="lax",
        max_age=refresh_expire_seconds,
        path="/api/v1/auth",
    )

    # Registrar auditoría
    await log_audit(
        db=db,
        accion="LOGIN",
        entidad="usuario",
        entidad_id=user.id,
        usuario=user,
        detalles={"email": user.email, "rol": user.rol.value},
        request=request,
    )
    await db.commit()

    return AuthResponse(
        token=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        ),
        user=UserProfileResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_session(
    response: Response,
    payload: RefreshTokenRequest | None = None,
    refresh_token_cookie: str | None = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Refresca el access token y rota el refresh token para máxima seguridad.
    Acepta el refresh token desde la cookie httpOnly o desde el body.
    """
    token_str = (payload and payload.refresh_token) or refresh_token_cookie

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "NO_REFRESH_TOKEN", "message": "Refresh token no proporcionado"}},
        )

    try:
        decoded = decode_token(token_str)
        user_id_str: str = decoded.get("sub")
        jti: str = decoded.get("jti")
        token_type: str = decoded.get("type")

        if not user_id_str or not jti or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "INVALID_REFRESH_TOKEN", "message": "Token de refresco inválido"}},
            )
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_REFRESH_TOKEN", "message": "Token de refresco inválido o expirado"}},
        ) from None

    # Verificar validez en Redis
    if not await is_refresh_token_valid(user_id, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "REVOKED_TOKEN", "message": "Token revocado o ya utilizado"}},
        )

    # Revocar el token anterior (Rotación de tokens)
    await revoke_refresh_token(user_id, jti)

    # Obtener datos del usuario
    stmt = select(Usuario).where(Usuario.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_INACTIVE", "message": "Usuario no encontrado o inactivo"}},
        )

    # Emitir nuevo access token y nuevo refresh token
    access_claims = {
        "email": user.email,
        "rol": user.rol.value,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
    }
    new_access_token = create_access_token(subject=user.id, extra_claims=access_claims)
    new_refresh_token, new_jti = create_refresh_token(subject=user.id)

    # Guardar nuevo refresh token en Redis
    refresh_expire_seconds = settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 3600
    await save_refresh_token(user.id, new_jti, refresh_expire_seconds)

    # Actualizar cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.API_ENV == "production",
        samesite="lax",
        max_age=refresh_expire_seconds,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: Usuario = Depends(get_current_user),
    refresh_token_cookie: str | None = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Cierra la sesión del usuario revocando el refresh token en Redis y limpiando cookies.
    """
    if refresh_token_cookie:
        try:
            decoded = decode_token(refresh_token_cookie)
            jti = decoded.get("jti")
            if jti:
                await revoke_refresh_token(current_user.id, jti)
        except JWTError:
            pass

    response.delete_cookie(key="refresh_token", path="/api/v1/auth")

    # Auditoría
    await log_audit(
        db=db,
        accion="LOGOUT",
        entidad="usuario",
        entidad_id=current_user.id,
        usuario=current_user,
        request=request,
    )
    await db.commit()

    return {"status": "ok", "message": "Sesión finalizada exitosamente"}


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: Usuario = Depends(get_current_user),
) -> UserProfileResponse:
    """
    Retorna los datos y permisos del usuario actualmente autenticado.
    """
    return UserProfileResponse.model_validate(current_user)
