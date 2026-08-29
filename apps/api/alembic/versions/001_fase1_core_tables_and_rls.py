"""
Fase 1: Tablas Core (tenants, clientes, usuarios, audit_logs) y Políticas RLS

Revision ID: 001_fase1_core_tables_and_rls
Revises:
Create Date: 2026-08-29 08:50:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001_fase1_core_tables_and_rls'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Tabla: tenants ─────────────────────────────────────────
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=False, server_default='community'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tenants')),
    )
    op.create_index(op.f('ix_tenants_slug'), 'tenants', ['slug'], unique=True)

    # ── 2. Tabla: clientes ────────────────────────────────────────
    op.create_table(
        'clientes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nombre_razon_social', sa.String(length=255), nullable=False),
        sa.Column('ruc', sa.String(length=13), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('contacto_principal_nombre', sa.String(length=255), nullable=False),
        sa.Column('contacto_principal_email', sa.String(length=255), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_clientes_tenant_id_tenants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_clientes')),
        sa.UniqueConstraint('tenant_id', 'ruc', name='uq_clientes_tenant_ruc'),
    )
    op.create_index(op.f('ix_clientes_tenant_id'), 'clientes', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_clientes_ruc'), 'clientes', ['ruc'], unique=False)

    # ── 3. Tabla: usuarios ────────────────────────────────────────
    op.create_table(
        'usuarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('apellido', sa.String(length=100), nullable=False),
        sa.Column('rol', sa.String(length=50), nullable=False, server_default='analista'),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_usuarios_tenant_id_tenants'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], name=op.f('fk_usuarios_cliente_id_clientes'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_usuarios')),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_usuarios_tenant_email'),
    )
    op.create_index(op.f('ix_usuarios_tenant_id'), 'usuarios', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_usuarios_email'), 'usuarios', ['email'], unique=False)
    op.create_index(op.f('ix_usuarios_cliente_id'), 'usuarios', ['cliente_id'], unique=False)

    # ── 4. Tabla: audit_logs ──────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accion', sa.String(length=50), nullable=False),
        sa.Column('entidad', sa.String(length=50), nullable=False),
        sa.Column('entidad_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('detalles', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_audit_logs_tenant_id_tenants'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name=op.f('fk_audit_logs_usuario_id_usuarios'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs')),
    )
    op.create_index(op.f('ix_audit_logs_tenant_id'), 'audit_logs', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_usuario_id'), 'audit_logs', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_accion'), 'audit_logs', ['accion'], unique=False)
    op.create_index(op.f('ix_audit_logs_entidad'), 'audit_logs', ['entidad'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)

    # ── 5. Habilitación de Row Level Security (RLS) ───────────────
    # Políticas para aislamiento multi-tenant estricto en PostgreSQL
    op.execute("ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE clientes FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY clientes_tenant_isolation ON clientes
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

    op.execute("ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE usuarios FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY usuarios_tenant_isolation ON usuarios
        FOR ALL
        USING (
            current_setting('app.tenant_id', true) = ''
            OR tenant_id IS NULL
            OR tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        )
        WITH CHECK (
            current_setting('app.tenant_id', true) = ''
            OR tenant_id IS NULL
            OR tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        );
    """)

    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY audit_logs_tenant_isolation ON audit_logs
        FOR ALL
        USING (
            current_setting('app.tenant_id', true) = ''
            OR tenant_id IS NULL
            OR tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        )
        WITH CHECK (
            current_setting('app.tenant_id', true) = ''
            OR tenant_id IS NULL
            OR tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        );
    """)


def downgrade() -> None:
    # ── Eliminar Políticas RLS ────────────────────────────────────
    op.execute("DROP POLICY IF EXISTS audit_logs_tenant_isolation ON audit_logs;")
    op.execute("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS usuarios_tenant_isolation ON usuarios;")
    op.execute("ALTER TABLE usuarios DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS clientes_tenant_isolation ON clientes;")
    op.execute("ALTER TABLE clientes DISABLE ROW LEVEL SECURITY;")

    # ── Eliminar Tablas ───────────────────────────────────────────
    op.drop_table('audit_logs')
    op.drop_table('usuarios')
    op.drop_table('clientes')
    op.drop_table('tenants')
