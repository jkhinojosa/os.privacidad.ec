"""
Fase 5: Vulneraciones de Seguridad (Brechas de Datos) y Notificación a SPDP con RLS

Revision ID: 005_fase5_brechas
Revises: 004_fase4_derechos
Create Date: 2026-08-29 19:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_fase5_brechas"
down_revision: str | None = "004_fase4_derechos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Tabla: brechas_seguridad ───────────────────────────────
    op.create_table(
        "brechas_seguridad",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("codigo", sa.String(length=30), nullable=False),
        sa.Column("caso_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("proceso_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column(
            "tipo_vulneracion",
            sa.String(length=50),
            server_default="confidencialidad",
            nullable=False,
        ),
        sa.Column("severidad", sa.String(length=50), server_default="alta", nullable=False),
        sa.Column("estado", sa.String(length=50), server_default="detectada", nullable=False),
        sa.Column("sistemas_afectados", sa.Text(), nullable=False),
        sa.Column("causa_presunta", sa.Text(), nullable=False),
        sa.Column("colectivos_afectados", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("volumen_titulares_estimado", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "categorias_datos_expuestas", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("fecha_deteccion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_limite_spdp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "notificada_a_spdp", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("fecha_notificacion_spdp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("numero_radicado_spdp", sa.String(length=100), nullable=True),
        sa.Column(
            "notificada_a_arcotel", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("justificacion_dilacion", sa.Text(), nullable=True),
        sa.Column(
            "requiere_notificacion_titulares",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("fecha_calificacion_riesgo", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_limite_titulares", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "notificada_a_titulares", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("fecha_notificacion_titulares", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canal_notificacion_titulares", sa.String(length=100), nullable=True),
        sa.Column("excepcion_titulares_aplicada", sa.String(length=100), nullable=True),
        sa.Column("justificacion_excepcion_titulares", sa.Text(), nullable=True),
        sa.Column("medidas_contencion_inmediatas", sa.Text(), nullable=False),
        sa.Column("medidas_remediacion_previstas", sa.Text(), nullable=False),
        sa.Column("dictamen_dpd", sa.Text(), nullable=True),
        sa.Column("evaluacion_riesgo_titulares", sa.Text(), nullable=True),
        sa.Column("fecha_cierre", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name=op.f("fk_brechas_seguridad_tenant_id_tenants"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["caso_id"],
            ["casos.id"],
            name=op.f("fk_brechas_seguridad_caso_id_casos"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["proceso_id"],
            ["procesos.id"],
            name=op.f("fk_brechas_seguridad_proceso_id_procesos"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_brechas_seguridad")),
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_brecha_tenant_codigo"),
    )
    op.create_index(
        op.f("ix_brechas_seguridad_tenant_id"), "brechas_seguridad", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_brechas_seguridad_codigo"), "brechas_seguridad", ["codigo"], unique=False
    )
    op.create_index(
        op.f("ix_brechas_seguridad_tipo_vulneracion"),
        "brechas_seguridad",
        ["tipo_vulneracion"],
        unique=False,
    )
    op.create_index(
        op.f("ix_brechas_seguridad_severidad"), "brechas_seguridad", ["severidad"], unique=False
    )
    op.create_index(
        op.f("ix_brechas_seguridad_estado"), "brechas_seguridad", ["estado"], unique=False
    )

    # ── 2. Habilitación de Row Level Security (RLS) ───────────────
    op.execute("ALTER TABLE brechas_seguridad ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE brechas_seguridad FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY brechas_seguridad_tenant_isolation ON brechas_seguridad
        FOR ALL
        USING (
            current_setting('app.tenant_id', true) = ''
            OR tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        )
        WITH CHECK (
            current_setting('app.tenant_id', true) = ''
            OR tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        );
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS brechas_seguridad_tenant_isolation ON brechas_seguridad;")
    op.execute("ALTER TABLE brechas_seguridad DISABLE ROW LEVEL SECURITY;")
    op.drop_table("brechas_seguridad")
