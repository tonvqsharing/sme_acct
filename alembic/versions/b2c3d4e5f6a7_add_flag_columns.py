"""add sales_einvoice_enabled + variance_account (config slice 3)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-04

Hand-written (autogenerate broken repo-wide, pre-existing FK error).
Guarded → safe on both DB lineages, re-runnable.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return insp.has_table(table) and column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if _has_table("system_settings"):
        if not _has_column("system_settings", "sales_einvoice_enabled"):
            op.add_column(
                "system_settings", sa.Column("sales_einvoice_enabled", sa.Boolean(), nullable=True)
            )
        if not _has_column("system_settings", "variance_account"):
            op.add_column(
                "system_settings", sa.Column("variance_account", sa.String(length=10), nullable=True)
            )


def downgrade() -> None:
    if _has_column("system_settings", "variance_account"):
        op.drop_column("system_settings", "variance_account")
    if _has_column("system_settings", "sales_einvoice_enabled"):
        op.drop_column("system_settings", "sales_einvoice_enabled")
