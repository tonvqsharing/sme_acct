"""add fixed_assets table

Revision ID: 7f26e5ec1793
Revises: 2d7adc359b8c
Create Date: 2026-08-26
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '7f26e5ec1793'
down_revision = '2d7adc359b8c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'fixed_assets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), nullable=False),
        sa.Column('asset_code', sa.String(30), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('category', sa.String(20), server_default='huu_hinh'),
        sa.Column('original_cost', sa.Numeric(18, 2), nullable=False),
        sa.Column('acquisition_date', sa.Date(), nullable=False),
        sa.Column('useful_life_months', sa.Integer(), nullable=False),
        sa.Column('depreciation_account', sa.String(10), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('accumulated_depreciation', sa.Numeric(18, 2), server_default='0'),
        sa.Column('checksum', sa.String(64), server_default=''),
    )
    op.create_index(
        'ix_fixed_assets_company_id', 'fixed_assets', ['company_id']
    )


def downgrade() -> None:
    op.drop_index('ix_fixed_assets_company_id', table_name='fixed_assets')
    op.drop_table('fixed_assets')
