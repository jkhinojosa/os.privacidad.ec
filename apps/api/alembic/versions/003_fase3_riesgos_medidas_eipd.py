"""
Fase 3: Riesgos, Medidas de Seguridad y Evaluaciones de Impacto (EIPD) con RLS

Revision ID: 003_fase3_riesgos
Revises: 002_fase2_core
Create Date: 2026-08-29 16:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '003_fase3_riesgos'
down_revision: str | None = '002_fase2_core'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Columnas RAT LOPDP y MTGE en tabla procesos ───────────
    op.add_column('procesos', sa.Column('destinatarios', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('procesos', sa.Column('colectivos_titulares', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('procesos', sa.Column('tiene_perfiles', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('procesos', sa.Column('transferencia_internacional', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('procesos', sa.Column('paises_transferencia', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('procesos', sa.Column('garantias_transferencia', sa.String(length=255), nullable=True))
    op.add_column('procesos', sa.Column('plazo_conservacion', sa.String(length=255), nullable=True))
    op.add_column('procesos', sa.Column('frecuencia_tratamiento', sa.String(length=50), server_default='continua', nullable=False))
    op.add_column('procesos', sa.Column('permanencia_tratamiento', sa.String(length=50), server_default='indefinida', nullable=False))
    op.add_column('procesos', sa.Column('volumen_titulares_estimado', sa.Integer(), nullable=True))
    op.add_column('procesos', sa.Column('puntaje_mtge', sa.Float(), server_default='0.0', nullable=False))
    op.add_column('procesos', sa.Column('requiere_eipd', sa.Boolean(), server_default=sa.text('false'), nullable=False))

    # ── 2. Tabla: medidas_seguridad ───────────────────────────────
    op.create_table(
        'medidas_seguridad',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('codigo', sa.String(length=30), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('estado_implementacion', sa.String(length=50), server_default='planificada', nullable=False),
        sa.Column('responsable', sa.String(length=100), nullable=True),
        sa.Column('evidencia_url', sa.String(length=500), nullable=True),
        sa.Column('activo', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_medidas_seguridad_tenant_id_tenants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_medidas_seguridad')),
        sa.UniqueConstraint('tenant_id', 'codigo', name='uq_medidas_tenant_codigo'),
    )
    op.create_index(op.f('ix_medidas_seguridad_tenant_id'), 'medidas_seguridad', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medidas_seguridad_codigo'), 'medidas_seguridad', ['codigo'], unique=False)
    op.create_index(op.f('ix_medidas_seguridad_tipo'), 'medidas_seguridad', ['tipo'], unique=False)
    op.create_index(op.f('ix_medidas_seguridad_estado_implementacion'), 'medidas_seguridad', ['estado_implementacion'], unique=False)

    # ── 3. Tabla: riesgos ─────────────────────────────────────────
    op.create_table(
        'riesgos',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('codigo', sa.String(length=30), nullable=False),
        sa.Column('proceso_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion_amenaza', sa.Text(), nullable=False),
        sa.Column('vulnerabilidad', sa.Text(), nullable=False),
        sa.Column('dimension_afectada', sa.String(length=50), server_default='confidencialidad', nullable=False),
        sa.Column('es_grupo_vulnerable', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('probabilidad_inherente', sa.Integer(), server_default='3', nullable=False),
        sa.Column('impacto_inherente', sa.Integer(), server_default='3', nullable=False),
        sa.Column('riesgo_inherente_score', sa.Float(), server_default='4.5', nullable=False),
        sa.Column('nivel_riesgo_inherente', sa.String(length=50), server_default='medio', nullable=False),
        sa.Column('probabilidad_residual', sa.Integer(), nullable=True),
        sa.Column('impacto_residual', sa.Integer(), nullable=True),
        sa.Column('riesgo_residual_score', sa.Float(), nullable=True),
        sa.Column('nivel_riesgo_residual', sa.String(length=50), nullable=True),
        sa.Column('estado', sa.String(length=50), server_default='identificado', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_riesgos_tenant_id_tenants'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['proceso_id'], ['procesos.id'], name=op.f('fk_riesgos_proceso_id_procesos'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_riesgos')),
        sa.UniqueConstraint('tenant_id', 'codigo', name='uq_riesgos_tenant_codigo'),
    )
    op.create_index(op.f('ix_riesgos_tenant_id'), 'riesgos', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_riesgos_codigo'), 'riesgos', ['codigo'], unique=False)
    op.create_index(op.f('ix_riesgos_proceso_id'), 'riesgos', ['proceso_id'], unique=False)
    op.create_index(op.f('ix_riesgos_nivel_riesgo_inherente'), 'riesgos', ['nivel_riesgo_inherente'], unique=False)
    op.create_index(op.f('ix_riesgos_nivel_riesgo_residual'), 'riesgos', ['nivel_riesgo_residual'], unique=False)
    op.create_index(op.f('ix_riesgos_estado'), 'riesgos', ['estado'], unique=False)

    # ── 4. Tabla Intermedia: riesgo_medidas ───────────────────────
    op.create_table(
        'riesgo_medidas',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('riesgo_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('medida_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_riesgo_medidas_tenant_id_tenants'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['riesgo_id'], ['riesgos.id'], name=op.f('fk_riesgo_medidas_riesgo_id_riesgos'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['medida_id'], ['medidas_seguridad.id'], name=op.f('fk_riesgo_medidas_medida_id_medidas'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_riesgo_medidas')),
        sa.UniqueConstraint('tenant_id', 'riesgo_id', 'medida_id', name='uq_riesgo_medida'),
    )
    op.create_index(op.f('ix_riesgo_medidas_tenant_id'), 'riesgo_medidas', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_riesgo_medidas_riesgo_id'), 'riesgo_medidas', ['riesgo_id'], unique=False)
    op.create_index(op.f('ix_riesgo_medidas_medida_id'), 'riesgo_medidas', ['medida_id'], unique=False)

    # ── 5. Tabla: evaluaciones_impacto (EIPD / PIA) ───────────────
    op.create_table(
        'evaluaciones_impacto',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('codigo', sa.String(length=30), nullable=False),
        sa.Column('proceso_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('titulo', sa.String(length=255), nullable=False),
        sa.Column('descripcion_sistematica', sa.Text(), nullable=False),
        sa.Column('justificacion_necesidad_proporcionalidad', sa.Text(), nullable=False),
        sa.Column('dictamen_dpd', sa.Text(), nullable=True),
        sa.Column('opinion_titulares_consultados', sa.Text(), nullable=True),
        sa.Column('estado', sa.String(length=50), server_default='borrador', nullable=False),
        sa.Column('fecha_aprobacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('aprobado_por', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_evaluaciones_impacto_tenant_id_tenants'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['proceso_id'], ['procesos.id'], name=op.f('fk_evaluaciones_impacto_proceso_id_procesos'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['aprobado_por'], ['usuarios.id'], name=op.f('fk_evaluaciones_impacto_aprobado_por_usuarios'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_evaluaciones_impacto')),
        sa.UniqueConstraint('tenant_id', 'codigo', name='uq_eipd_tenant_codigo'),
    )
    op.create_index(op.f('ix_evaluaciones_impacto_tenant_id'), 'evaluaciones_impacto', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_evaluaciones_impacto_codigo'), 'evaluaciones_impacto', ['codigo'], unique=False)
    op.create_index(op.f('ix_evaluaciones_impacto_proceso_id'), 'evaluaciones_impacto', ['proceso_id'], unique=False)
    op.create_index(op.f('ix_evaluaciones_impacto_estado'), 'evaluaciones_impacto', ['estado'], unique=False)

    # ── 6. Habilitación de Row Level Security (RLS) ───────────────
    for table in ['medidas_seguridad', 'riesgos', 'riesgo_medidas', 'evaluaciones_impacto']:
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
    for table in ['evaluaciones_impacto', 'riesgo_medidas', 'riesgos', 'medidas_seguridad']:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_table('evaluaciones_impacto')
    op.drop_table('riesgo_medidas')
    op.drop_table('riesgos')
    op.drop_table('medidas_seguridad')

    # Eliminar columnas RAT/MTGE agregadas a procesos
    for col in [
        'requiere_eipd', 'puntaje_mtge', 'volumen_titulares_estimado',
        'permanencia_tratamiento', 'frecuencia_tratamiento', 'plazo_conservacion',
        'garantias_transferencia', 'paises_transferencia', 'transferencia_internacional',
        'tiene_perfiles', 'colectivos_titulares', 'destinatarios'
    ]:
        op.drop_column('procesos', col)
