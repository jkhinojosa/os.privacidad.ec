"""
Fase 4: Solicitudes de Derechos de Titulares (LOPDP) y Notificaciones a Encargados con RLS

Revision ID: 004_fase4_derechos
Revises: 003_fase3_riesgos
Create Date: 2026-08-29 19:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '004_fase4_derechos'
down_revision: str | None = '003_fase3_riesgos'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Tabla: solicitudes_derechos ────────────────────────────
    op.create_table(
        'solicitudes_derechos',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('codigo', sa.String(length=30), nullable=False),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('proceso_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('asignado_a', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('titular_nombre', sa.String(length=255), nullable=False),
        sa.Column('titular_identificacion', sa.String(length=50), nullable=False),
        sa.Column('titular_email', sa.String(length=255), nullable=False),
        sa.Column('titular_telefono', sa.String(length=50), nullable=True),
        sa.Column('es_representante', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('representante_nombre', sa.String(length=255), nullable=True),
        sa.Column('representante_identificacion', sa.String(length=50), nullable=True),
        sa.Column('documento_acreditacion_url', sa.String(length=500), nullable=True),
        sa.Column('tipo_derecho', sa.String(length=50), nullable=False),
        sa.Column('canal_recepcion', sa.String(length=50), server_default='formulario_web', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='recibida', nullable=False),
        sa.Column('motivo_solicitud', sa.Text(), nullable=False),
        sa.Column('especificacion_datos', sa.Text(), nullable=True),
        sa.Column('datos_a_modificar', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('fecha_recepcion', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fecha_limite_sla', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fecha_subsanacion_limite', sa.DateTime(timezone=True), nullable=True),
        sa.Column('prorroga_aplicada', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('fecha_prorroga', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dias_prorroga', sa.Integer(), server_default='0', nullable=False),
        sa.Column('motivo_prorroga', sa.Text(), nullable=True),
        sa.Column('dictamen_dpd', sa.Text(), nullable=True),
        sa.Column('excepcion_legal_aplicada', sa.String(length=255), nullable=True),
        sa.Column('motivo_negativa', sa.Text(), nullable=True),
        sa.Column('fecha_resolucion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resuelto_por', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ejecucion_tecnica_completada', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('fecha_ejecucion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resultado_ejecucion', sa.Text(), nullable=True),
        sa.Column('fecha_cierre', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_solicitudes_derechos_tenant_id_tenants'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], name=op.f('fk_solicitudes_derechos_cliente_id_clientes'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['proceso_id'], ['procesos.id'], name=op.f('fk_solicitudes_derechos_proceso_id_procesos'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['asignado_a'], ['usuarios.id'], name=op.f('fk_solicitudes_derechos_asignado_a_usuarios'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resuelto_por'], ['usuarios.id'], name=op.f('fk_solicitudes_derechos_resuelto_por_usuarios'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_solicitudes_derechos')),
        sa.UniqueConstraint('tenant_id', 'codigo', name='uq_solicitud_tenant_codigo'),
    )
    op.create_index(op.f('ix_solicitudes_derechos_tenant_id'), 'solicitudes_derechos', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_solicitudes_derechos_codigo'), 'solicitudes_derechos', ['codigo'], unique=False)
    op.create_index(op.f('ix_solicitudes_derechos_titular_identificacion'), 'solicitudes_derechos', ['titular_identificacion'], unique=False)
    op.create_index(op.f('ix_solicitudes_derechos_tipo_derecho'), 'solicitudes_derechos', ['tipo_derecho'], unique=False)
    op.create_index(op.f('ix_solicitudes_derechos_estado'), 'solicitudes_derechos', ['estado'], unique=False)

    # ── 2. Tabla: notificaciones_encargados ───────────────────────
    op.create_table(
        'notificaciones_encargados',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('solicitud_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encargado_nombre', sa.String(length=255), nullable=False),
        sa.Column('encargado_email', sa.String(length=255), nullable=False),
        sa.Column('tipo_accion_requerida', sa.String(length=50), nullable=False),
        sa.Column('instrucciones_tecnicas', sa.Text(), nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='enviada', nullable=False),
        sa.Column('fecha_envio', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fecha_confirmacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('evidencia_respuesta', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_notificaciones_encargados_tenant_id_tenants'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['solicitud_id'], ['solicitudes_derechos.id'], name=op.f('fk_notificaciones_encargados_solicitud_id_solicitudes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_notificaciones_encargados')),
    )
    op.create_index(op.f('ix_notificaciones_encargados_tenant_id'), 'notificaciones_encargados', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_notificaciones_encargados_solicitud_id'), 'notificaciones_encargados', ['solicitud_id'], unique=False)
    op.create_index(op.f('ix_notificaciones_encargados_estado'), 'notificaciones_encargados', ['estado'], unique=False)

    # ── 3. Habilitación de Row Level Security (RLS) ───────────────
    for table in ['solicitudes_derechos', 'notificaciones_encargados']:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
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
    for table in ['notificaciones_encargados', 'solicitudes_derechos']:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_table('notificaciones_encargados')
    op.drop_table('solicitudes_derechos')
