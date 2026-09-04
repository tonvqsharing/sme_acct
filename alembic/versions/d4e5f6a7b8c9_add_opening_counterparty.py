"""add opening_counterparty (opening S2)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-04

Hand-written (autogenerate broken repo-wide, pre-existing FK error).
Guarded → safe on both DB lineages, re-runnable.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _has_index(name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(
        ix["name"] == name
        for table in insp.get_table_names()
        for ix in insp.get_indexes(table)
    )


def upgrade() -> None:
    if not _has_table("opening_counterparty"):
        op.create_table(
            "opening_counterparty",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("batch_id", sa.String(length=36), nullable=False),
            sa.Column("account_code", sa.String(length=20), nullable=False),
            sa.Column("party_id", sa.String(length=36), nullable=False),
            sa.Column("side", sa.String(length=10), nullable=False),
            sa.Column("amount", sa.Numeric(18, 2), nullable=False),
            sa.Column("proof", sa.Boolean(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index("ix_opening_counterparty_batch_id"):
        op.create_index(
            "ix_opening_counterparty_batch_id", "opening_counterparty", ["batch_id"]
        )
    if not _has_index("ix_opening_counterparty_party_id"):
        op.create_index(
            "ix_opening_counterparty_party_id", "opening_counterparty", ["party_id"]
        )


def downgrade() -> None:
    if _has_index("ix_opening_counterparty_party_id"):
        op.drop_index("ix_opening_counterparty_party_id", table_name="opening_counterparty")
    if _has_index("ix_opening_counterparty_batch_id"):
        op.drop_index("ix_opening_counterparty_batch_id", table_name="opening_counterparty")
    if _has_table("opening_counterparty"):
        op.drop_table("opening_counterparty")
