"""add account_type to accounts

Revision ID: 4107c140af78
Revises: e348258e2761
Create Date: 2026-08-28 08:45:58.766868
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '4107c140af78'
down_revision = 'e348258e2761'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("account_type", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "account_type")
