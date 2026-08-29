"""
OS Privacidad — Script de Sembrado de Datos Iniciales (Seed)
=============================================================
Crea organizaciones demo, usuarios iniciales con diferentes roles y un cliente de prueba.
Ejecución: python -m db.seed (o vía Docker)
"""

import asyncio
import logging
import uuid

from sqlalchemy import select

from core.security import hash_password
from db.session import async_session_maker
from models.cliente import Cliente
from models.tenant import Tenant, TenantPlan
from models.usuario import UserRole, Usuario

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


async def run_seed():
    """Ejecuta el sembrado de datos en la base de datos."""
    async with async_session_maker() as db:
        logger.info("Verificando si ya existen datos sembrados...")

        # ── 1. SuperAdmin Global ──────────────────────────────────
        stmt = select(Usuario).where(Usuario.email == "admin@osprivacidad.ec")
        res = await db.execute(stmt)
        super_admin = res.scalar_one_or_none()

        if not super_admin:
            logger.info("Creando SuperAdmin global...")
            super_admin = Usuario(
                id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                tenant_id=None,
                email="admin@osprivacidad.ec",
                password_hash=hash_password("Admin123456!"),
                nombre="Super",
                apellido="Admin",
                rol=UserRole.super_admin,
                activo=True,
            )
            db.add(super_admin)
            await db.flush()
            logger.info("✅ SuperAdmin creado: admin@osprivacidad.ec / Admin123456!")
        else:
            logger.info("ℹ️ SuperAdmin ya existe.")

        # ── 2. Tenant Demo ────────────────────────────────────────
        stmt = select(Tenant).where(Tenant.slug == "demo-corp")
        res = await db.execute(stmt)
        tenant_demo = res.scalar_one_or_none()

        if not tenant_demo:
            logger.info("Creando Tenant demo...")
            tenant_demo = Tenant(
                id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                nombre="Corporación Demo S.A.",
                slug="demo-corp",
                plan=TenantPlan.professional,
                activo=True,
            )
            db.add(tenant_demo)
            await db.flush()
            logger.info("✅ Tenant Demo creado: Corporación Demo S.A. (slug: demo-corp)")
        else:
            logger.info("ℹ️ Tenant Demo ya existe.")

        # ── 3. Usuarios dentro del Tenant Demo ────────────────────
        demo_users = [
            ("tenantadmin@demo.ec", "Tenant", "Admin", UserRole.tenant_admin),
            ("dpo@demo.ec", "Oficial", "DPO", UserRole.dpo),
            ("analista@demo.ec", "Analista", "Seguridad", UserRole.analista),
            ("auditor@demo.ec", "Auditor", "Cumplimiento", UserRole.auditor),
        ]

        for email, nombre, apellido, rol in demo_users:
            stmt = select(Usuario).where(Usuario.tenant_id == tenant_demo.id, Usuario.email == email)
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                user = Usuario(
                    tenant_id=tenant_demo.id,
                    email=email,
                    password_hash=hash_password("Demo123456!"),
                    nombre=nombre,
                    apellido=apellido,
                    rol=rol,
                    activo=True,
                    created_by=super_admin.id,
                )
                db.add(user)
                logger.info(f"✅ Usuario creado: {email} ({rol.value})")

        # ── 4. Cliente Demo dentro del Tenant ─────────────────────
        stmt = select(Cliente).where(Cliente.tenant_id == tenant_demo.id, Cliente.ruc == "1790012345001")
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            cliente = Cliente(
                id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                tenant_id=tenant_demo.id,
                nombre_razon_social="Empresa Farmacéutica Andina S.A.",
                ruc="1790012345001",
                sector="Salud / Farmacéutica",
                contacto_principal_nombre="Dr. Carlos Mendoza",
                contacto_principal_email="carlos.mendoza@farmandina.ec",
                created_by=super_admin.id,
                activo=True,
            )
            db.add(cliente)
            logger.info("✅ Cliente Demo creado: Empresa Farmacéutica Andina S.A. (RUC 1790012345001)")

        await db.commit()
        logger.info("🎉 Seed completado exitosamente.")


if __name__ == "__main__":
    asyncio.run(run_seed())
