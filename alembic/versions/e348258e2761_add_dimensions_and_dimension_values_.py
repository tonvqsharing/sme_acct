"""add dimensions and dimension_values tables

Revision ID: e348258e2761
Revises: 0bc4d5a35684
Create Date: 2026-08-27 09:06:05.152182
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = 'e348258e2761'
down_revision = '0bc4d5a35684'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- dimensions --------------------------------------------------------
    op.create_table(
        'dimensions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('company_id', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('audit_checksum', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'company_id', name='uq_dimensions_code_company'),
    )
    op.create_index('ix_dimensions_company_id', 'dimensions', ['company_id'])
    op.create_index('ix_dimensions_type', 'dimensions', ['type'])
    op.create_index('ix_dimensions_is_system', 'dimensions', ['is_system'])

    # -- dimension_values --------------------------------------------------
    op.create_table(
        'dimension_values',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('company_id', sa.String(length=36), nullable=False),
        sa.Column('dimension_id', sa.String(length=36), sa.ForeignKey('dimensions.id'), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('audit_checksum', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'code', 'dimension_id', 'company_id',
            name='uq_dimension_values_code_dim_company',
        ),
    )
    op.create_index('ix_dimension_values_company_id', 'dimension_values', ['company_id'])
    op.create_index('ix_dimension_values_dimension_id', 'dimension_values', ['dimension_id'])
    op.create_index('ix_dimension_values_status', 'dimension_values', ['status'])


def downgrade() -> None:
    op.drop_index('ix_dimension_values_status', table_name='dimension_values')
    op.drop_index('ix_dimension_values_dimension_id', table_name='dimension_values')
    op.drop_index('ix_dimension_values_company_id', table_name='dimension_values')
    op.drop_table('dimension_values')
    op.drop_index('ix_dimensions_is_system', table_name='dimensions')
    op.drop_index('ix_dimensions_type', table_name='dimensions')
    op.drop_index('ix_dimensions_company_id', table_name='dimensions')
    op.drop_table('dimensions')
