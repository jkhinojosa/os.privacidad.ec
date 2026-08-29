"""
OS Privacidad — Script de Sembrado de Datos Iniciales (Seed)
=============================================================
Crea organizaciones demo, usuarios, clientes, procesos RAT (con MTGE),
medidas de seguridad ISO 27001 / LOPDP, riesgos de derechos y libertades y EIPD.
Ejecución: python -m db.seed (o vía Docker)
"""

import asyncio
import datetime
import logging
import uuid

from sqlalchemy import select

from core.risk_engine import calcular_puntaje_mtge, calcular_score_y_nivel_riesgo
from core.security import hash_password
from db.session import async_session_maker
from models.caso import Caso, CasoEstado, CasoPrioridad, CasoTipo
from models.cliente import Cliente
from models.eipd import EIPDEstado, EvaluacionImpacto
from models.expediente import Expediente, ExpedienteEstado
from models.medida_seguridad import MedidaEstado, MedidaSeguridad, MedidaTipo
from models.proceso import BaseLegal, FrecuenciaTratamiento, Proceso
from models.riesgo import (
    Riesgo,
    RiesgoDimension,
    RiesgoEstado,
)
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
        cliente = res.scalar_one_or_none()
        if not cliente:
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
            await db.flush()
            logger.info("✅ Cliente Demo creado: Empresa Farmacéutica Andina S.A. (RUC 1790012345001)")

        # ── 5. Proceso Demo (RAT) con MTGE ────────────────────────
        stmt = select(Proceso).where(Proceso.tenant_id == tenant_demo.id, Proceso.nombre == "Gestión de Pacientes y Ensayos Clínicos")
        res = await db.execute(stmt)
        proceso = res.scalar_one_or_none()
        tipo_datos = ["identificativos", "salud", "biométricos", "genéticos"]
        mtge_score = calcular_puntaje_mtge(
            volumen_titulares=15000,
            frecuencia=FrecuenciaTratamiento.continua.value,
            tipo_datos=tipo_datos,
            tiene_perfiles=True,
            transferencia_internacional=True,
        )

        if not proceso:
            proceso = Proceso(
                id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
                tenant_id=tenant_demo.id,
                cliente_id=cliente.id,
                nombre="Gestión de Pacientes y Ensayos Clínicos",
                descripcion="Tratamiento de historias clínicas, consentimiento informado y datos genéticos para investigación",
                area_responsable="Dirección Médica y Regulatoria",
                base_legal=BaseLegal.consentimiento.value,
                finalidad="Investigación clínica y cumplimiento de protocolos farmacológicos LOPDP Art. 7",
                tipo_datos=tipo_datos,
                destinatarios=["Laboratorios Centrales S.A.", "Ministerio de Salud Pública"],
                colectivos_titulares=["Pacientes Ensayos Clínicos", "Médicos Investigadores"],
                tiene_perfiles=True,
                transferencia_internacional=True,
                paises_transferencia=["Alemania", "Estados Unidos"],
                garantias_transferencia="Cláusulas Contractuales Tipo (CTM) homologadas por la SPDP",
                plazo_conservacion="15 años conforme a normativa sanitaria nacional",
                frecuencia_tratamiento=FrecuenciaTratamiento.continua.value,
                permanencia_tratamiento="indefinida",
                volumen_titulares_estimado=15000,
                puntaje_mtge=mtge_score,
                requiere_eipd=True,
                activo=True,
                created_by=super_admin.id,
            )
            db.add(proceso)
            await db.flush()
            logger.info("✅ Proceso RAT creado: Gestión de Pacientes y Ensayos Clínicos (Puntaje MTGE: %s)", mtge_score)

        # ── 6. Medidas de Seguridad Demo (Salvaguardas) ───────────
        medidas_seed = [
            (
                "MED-2026-0001",
                MedidaTipo.tecnica,
                "Cifrado AES-256 en Reposo y Tránsito",
                "Cifrado de todas las bases de datos de salud y certificados TLS 1.3",
                MedidaEstado.implementada,
                "Ing. Andrés Silva",
            ),
            (
                "MED-2026-0002",
                MedidaTipo.tecnica,
                "Autenticación Multifactor (MFA) Obligatoria",
                "MFA basado en tokens TOTP / FIDO2 para acceso al sistema de historias clínicas",
                MedidaEstado.implementada,
                "Ing. Andrés Silva",
            ),
            (
                "MED-2026-0003",
                MedidaTipo.organizativa,
                "Política de Control de Accesos y Privilegios Mínimos",
                "Revisión trimestral de accesos y roles según el principio de necesidad de conocer",
                MedidaEstado.verificada,
                "DPO Dr. Carlos Mendoza",
            ),
            (
                "MED-2026-0004",
                MedidaTipo.juridica,
                "Acuerdos de Encargo de Tratamiento con Cláusulas LOPDP",
                "Contratos firmados con proveedores tecnológicos garantizando soberanía de datos",
                MedidaEstado.implementada,
                "Abg. María Paredes",
            ),
        ]

        medidas_db = []
        for cod, tipo_m, nom, desc, est, resp in medidas_seed:
            stmt = select(MedidaSeguridad).where(MedidaSeguridad.tenant_id == tenant_demo.id, MedidaSeguridad.codigo == cod)
            res = await db.execute(stmt)
            med = res.scalar_one_or_none()
            if not med:
                med = MedidaSeguridad(
                    tenant_id=tenant_demo.id,
                    codigo=cod,
                    tipo=tipo_m,
                    nombre=nom,
                    descripcion=desc,
                    estado_implementacion=est,
                    responsable=resp,
                    created_by=super_admin.id,
                )
                db.add(med)
                await db.flush()
                logger.info(f"✅ Medida de Seguridad creada: {cod} ({nom})")
            medidas_db.append(med)

        # ── 7. Riesgos de Derechos y Libertades Demo ───────────────
        stmt = select(Riesgo).where(Riesgo.tenant_id == tenant_demo.id, Riesgo.codigo == "RSK-2026-0001")
        res = await db.execute(stmt)
        riesgo1 = res.scalar_one_or_none()
        if not riesgo1:
            score_inh, nivel_inh = calcular_score_y_nivel_riesgo(probabilidad=4, impacto=5, es_vulnerable=True)
            score_res, nivel_res = calcular_score_y_nivel_riesgo(probabilidad=2, impacto=4, es_vulnerable=True)
            riesgo1 = Riesgo(
                tenant_id=tenant_demo.id,
                codigo="RSK-2026-0001",
                proceso_id=proceso.id,
                nombre="Exfiltración masiva de datos genéticos y de salud",
                descripcion_amenaza="Ataque cibernético dirigido o vulneración de credenciales privilegiadas",
                vulnerabilidad="Exposición de endpoints API sin MFA y almacenamiento sin cifrado a nivel de campo",
                dimension_afectada=RiesgoDimension.confidencialidad,
                es_grupo_vulnerable=True,
                probabilidad_inherente=4,
                impacto_inherente=5,
                riesgo_inherente_score=score_inh,
                nivel_riesgo_inherente=nivel_inh,
                probabilidad_residual=2,
                impacto_residual=4,
                riesgo_residual_score=score_res,
                nivel_riesgo_residual=nivel_res,
                estado=RiesgoEstado.mitigado,
                medidas=medidas_db[:2],  # Asocia MED-0001 y MED-0002
                created_by=super_admin.id,
            )
            db.add(riesgo1)
            await db.flush()
            logger.info("✅ Riesgo Demo creado: RSK-2026-0001 (Score Inh: %s -> Res: %s)", score_inh, score_res)

        # ── 8. Evaluación de Impacto Demo (EIPD / PIA) ─────────────
        stmt = select(EvaluacionImpacto).where(EvaluacionImpacto.tenant_id == tenant_demo.id, EvaluacionImpacto.codigo == "EIPD-2026-0001")
        res = await db.execute(stmt)
        eipd = res.scalar_one_or_none()
        if not eipd:
            eipd = EvaluacionImpacto(
                tenant_id=tenant_demo.id,
                codigo="EIPD-2026-0001",
                proceso_id=proceso.id,
                titulo="Evaluación de Impacto del Sistema de Ensayos Clínicos y Pacientes",
                descripcion_sistematica="Tratamiento automatizado y perfilamiento de datos sensibles de pacientes para ensayos clínicos farmacológicos conforme al Art. 42 LOPDP.",
                justificacion_necesidad_proporcionalidad="El tratamiento es estrictamente necesario para la evaluación de eficacia terapéutica. Se aplican salvaguardas de minimización y seudonimización.",
                dictamen_dpd="El Delegado de Protección de Datos emite DICTAMEN FAVORABLE. Los riesgos residuales son tolerables tras la verificación de las medidas técnicas AES-256 y MFA.",
                estado=EIPDEstado.aprobada,
                fecha_aprobacion=datetime.datetime.now(datetime.UTC),
                aprobado_por=super_admin.id,
                created_by=super_admin.id,
            )
            db.add(eipd)
            await db.flush()
            logger.info("✅ EIPD Demo creada y aprobada: EIPD-2026-0001")

        # ── 9. Caso Demo ──────────────────────────────────────────
        stmt = select(Caso).where(Caso.tenant_id == tenant_demo.id, Caso.codigo == "CAS-2026-0001")
        res = await db.execute(stmt)
        caso = res.scalar_one_or_none()
        if not caso:
            caso = Caso(
                id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
                tenant_id=tenant_demo.id,
                codigo="CAS-2026-0001",
                cliente_id=cliente.id,
                proceso_id=proceso.id,
                titulo="Sospecha de exfiltración de base de datos de pacientes",
                descripcion="Alerta del SIEM sobre tráfico anómalo outbound desde el servidor de base de datos médica",
                tipo=CasoTipo.incidente_seguridad,
                prioridad=CasoPrioridad.critica,
                estado=CasoEstado.en_investigacion,
                created_by=super_admin.id,
            )
            db.add(caso)
            await db.flush()
            logger.info("✅ Caso Demo creado: CAS-2026-0001 (Incidente Crítico)")

        # ── 10. Expediente Demo ───────────────────────────────────
        stmt = select(Expediente).where(Expediente.tenant_id == tenant_demo.id, Expediente.codigo == "EXP-2026-0001")
        res = await db.execute(stmt)
        expediente = res.scalar_one_or_none()
        if not expediente:
            expediente = Expediente(
                id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
                tenant_id=tenant_demo.id,
                codigo="EXP-2026-0001",
                caso_id=caso.id,
                cliente_id=cliente.id,
                nombre="Expediente Pericial Forense CAS-2026-0001",
                descripcion="Informes técnicos de mitigación, actas del comité de crisis y notificación a la Autoridad de Protección de Datos",
                estado=ExpedienteEstado.activo,
                created_by=super_admin.id,
            )
            db.add(expediente)
            logger.info("✅ Expediente Demo creado: EXP-2026-0001")

        await db.commit()
        logger.info("🎉 Seed completado exitosamente con entidades de Fase 1, Fase 2 y Fase 3.")


if __name__ == "__main__":
    asyncio.run(run_seed())
