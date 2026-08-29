"""
Fase 2: Tablas de Procesos, Casos y Expedientes con RLS

Revision ID: 002_fase2_procesos_casos_expedientes
Revises: 001_fase1_core_tables_and_rls
Create Date: 2026-08-29 11:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_fase2_core"
down_revision: str | None = "001_fase1_core_tables_and_rls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Tabla: procesos ────────────────────────────────────────
    op.create_table(
        "procesos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("area_responsable", sa.String(length=100), nullable=False),
        sa.Column("base_legal", sa.String(length=100), nullable=False),
        sa.Column("finalidad", sa.Text(), nullable=False),
        sa.Column("tipo_datos", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
            name=op.f("fk_procesos_tenant_id_tenants"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clientes.id"],
            name=op.f("fk_procesos_cliente_id_clientes"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_procesos")),
    )
    op.create_index(op.f("ix_procesos_tenant_id"), "procesos", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_procesos_cliente_id"), "procesos", ["cliente_id"], unique=False)

    # ── 2. Tabla: casos ───────────────────────────────────────────
    op.create_table(
        "casos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("codigo", sa.String(length=30), nullable=False),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("proceso_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asignado_a", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False, server_default="otro"),
        sa.Column("prioridad", sa.String(length=20), nullable=False, server_default="media"),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="abierto"),
        sa.Column("fecha_limite", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_cierre", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolucion", sa.Text(), nullable=True),
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
            name=op.f("fk_casos_tenant_id_tenants"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clientes.id"],
            name=op.f("fk_casos_cliente_id_clientes"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["proceso_id"],
            ["procesos.id"],
            name=op.f("fk_casos_proceso_id_procesos"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["asignado_a"],
            ["usuarios.id"],
            name=op.f("fk_casos_asignado_a_usuarios"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_casos")),
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_casos_tenant_codigo"),
    )
    op.create_index(op.f("ix_casos_tenant_id"), "casos", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_casos_codigo"), "casos", ["codigo"], unique=False)
    op.create_index(op.f("ix_casos_estado"), "casos", ["estado"], unique=False)
    op.create_index(op.f("ix_casos_cliente_id"), "casos", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_casos_proceso_id"), "casos", ["proceso_id"], unique=False)
    op.create_index(op.f("ix_casos_asignado_a"), "casos", ["asignado_a"], unique=False)

    # ── 3. Tabla: expedientes ─────────────────────────────────────
    op.create_table(
        "expedientes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("codigo", sa.String(length=30), nullable=False),
        sa.Column("caso_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="activo"),
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
            name=op.f("fk_expedientes_tenant_id_tenants"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["caso_id"],
            ["casos.id"],
            name=op.f("fk_expedientes_caso_id_casos"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clientes.id"],
            name=op.f("fk_expedientes_cliente_id_clientes"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expedientes")),
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_expedientes_tenant_codigo"),
    )
    op.create_index(op.f("ix_expedientes_tenant_id"), "expedientes", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_expedientes_codigo"), "expedientes", ["codigo"], unique=False)
    op.create_index(op.f("ix_expedientes_caso_id"), "expedientes", ["caso_id"], unique=False)
    op.create_index(op.f("ix_expedientes_cliente_id"), "expedientes", ["cliente_id"], unique=False)

    # ── 4. Habilitación de Row Level Security (RLS) ───────────────
    op.execute("ALTER TABLE procesos ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE procesos FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY procesos_tenant_isolation ON procesos
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

    op.execute("ALTER TABLE casos ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE casos FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY casos_tenant_isolation ON casos
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

    op.execute("ALTER TABLE expedientes ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE expedientes FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY expedientes_tenant_isolation ON expedientes
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
    # ── Eliminar Políticas RLS ────────────────────────────────────
    op.execute("DROP POLICY IF EXISTS expedientes_tenant_isolation ON expedientes;")
    op.execute("ALTER TABLE expedientes DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS casos_tenant_isolation ON casos;")
    op.execute("ALTER TABLE casos DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS procesos_tenant_isolation ON procesos;")
    op.execute("ALTER TABLE procesos DISABLE ROW LEVEL SECURITY;")

    # ── Eliminar Tablas ───────────────────────────────────────────
    op.drop_table("expedientes")
    op.drop_table("casos")
    op.drop_table("procesos")
