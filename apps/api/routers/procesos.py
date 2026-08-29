"""
OS Privacidad — Router de Procesos (Registro de Actividades de Tratamiento)
===========================================================================
Endpoints CRUD para actividades de tratamiento (RAT) conforme a la LOPDP.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_tenant_db, log_audit, require_role
from models.proceso import Proceso
from models.usuario import UserRole, Usuario
from schemas.proceso import ProcesoCreate, ProcesoResponse, ProcesoUpdate

router = APIRouter(prefix="/procesos", tags=["Procesos (RAT)"])


@router.get("", response_model=list[ProcesoResponse])
async def list_procesos(
    cliente_id: uuid.UUID | None = Query(None, description="Filtrar por empresa cliente"),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(
            UserRole.super_admin,
            UserRole.tenant_admin,
            UserRole.dpo,
            UserRole.analista,
            UserRole.auditor,
        )
    ),
) -> list[ProcesoResponse]:
    """
    Lista las actividades de tratamiento del tenant (RLS + filtro opcional).
    """
    stmt = select(Proceso).where(Proceso.activo.is_(True))
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Proceso.tenant_id == current_user.tenant_id)

    if cliente_id:
        stmt = stmt.where(Proceso.cliente_id == cliente_id)

    stmt = stmt.order_by(Proceso.nombre.asc())
    result = await db.execute(stmt)
    procesos = result.scalars().all()
    return [ProcesoResponse.model_validate(p) for p in procesos]


@router.post("", response_model=ProcesoResponse, status_code=status.HTTP_201_CREATED)
async def create_proceso(
    payload: ProcesoCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> ProcesoResponse:
    """
    Registra una nueva actividad de tratamiento de datos personales en el tenant.
    """
    if not current_user.tenant_id and current_user.rol != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "NO_TENANT", "message": "Usuario no pertenece a un tenant válido"}
            },
        )

    tenant_id = current_user.tenant_id

    proceso = Proceso(
        tenant_id=tenant_id,
        cliente_id=payload.cliente_id,
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        area_responsable=payload.area_responsable,
        base_legal=payload.base_legal,
        finalidad=payload.finalidad,
        tipo_datos=payload.tipo_datos,
        created_by=current_user.id,
    )
    db.add(proceso)
    await db.flush()

    # Auditoría
    await log_audit(
        db=db,
        accion="CREATE",
        entidad="proceso",
        entidad_id=proceso.id,
        usuario=current_user,
        detalles={"nombre": proceso.nombre, "base_legal": proceso.base_legal},
        request=request,
    )
    await db.commit()
    await db.refresh(proceso)

    return ProcesoResponse.model_validate(proceso)


@router.get("/{proceso_id}", response_model=ProcesoResponse)
async def get_proceso(
    proceso_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(
            UserRole.super_admin,
            UserRole.tenant_admin,
            UserRole.dpo,
            UserRole.analista,
            UserRole.auditor,
        )
    ),
) -> ProcesoResponse:
    """
    Obtiene los detalles de un proceso por ID.
    """
    stmt = select(Proceso).where(Proceso.id == proceso_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Proceso.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    proceso = result.scalar_one_or_none()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PROCESO_NOT_FOUND",
                    "message": "Actividad de tratamiento no encontrada",
                }
            },
        )

    return ProcesoResponse.model_validate(proceso)


@router.patch("/{proceso_id}", response_model=ProcesoResponse)
async def update_proceso(
    proceso_id: uuid.UUID,
    payload: ProcesoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo, UserRole.analista)
    ),
) -> ProcesoResponse:
    """
    Actualiza la información de un proceso.
    """
    stmt = select(Proceso).where(Proceso.id == proceso_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Proceso.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    proceso = result.scalar_one_or_none()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PROCESO_NOT_FOUND",
                    "message": "Actividad de tratamiento no encontrada",
                }
            },
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proceso, field, value)

    proceso.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="UPDATE",
        entidad="proceso",
        entidad_id=proceso.id,
        usuario=current_user,
        detalles=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(proceso)

    return ProcesoResponse.model_validate(proceso)


@router.delete("/{proceso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proceso(
    proceso_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: Usuario = Depends(
        require_role(UserRole.super_admin, UserRole.tenant_admin, UserRole.dpo)
    ),
):
    """
    Desactiva (soft-delete) una actividad de tratamiento.
    """
    stmt = select(Proceso).where(Proceso.id == proceso_id)
    if current_user.rol != UserRole.super_admin and current_user.tenant_id:
        stmt = stmt.where(Proceso.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    proceso = result.scalar_one_or_none()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PROCESO_NOT_FOUND",
                    "message": "Actividad de tratamiento no encontrada",
                }
            },
        )

    proceso.activo = False
    proceso.updated_by = current_user.id

    await log_audit(
        db=db,
        accion="DELETE",
        entidad="proceso",
        entidad_id=proceso.id,
        usuario=current_user,
        detalles={"soft_delete": True},
        request=request,
    )
    await db.commit()
