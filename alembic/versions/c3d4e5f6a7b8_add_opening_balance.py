"""add opening balance tables (opening S1)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-04

Hand-written (autogenerate broken repo-wide, pre-existing FK error).
Guarded → safe on both DB lineages, re-runnable.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
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
    if not _has_table("opening_batches"):
        op.create_table(
            "opening_batches",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("company_id", sa.String(length=36), nullable=False),
            sa.Column("fiscal_year_id", sa.String(length=36), nullable=False),
            sa.Column("source", sa.String(length=20), nullable=False),
            sa.Column("state", sa.String(length=20), nullable=False),
            sa.Column("checksum", sa.String(length=64), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index("ix_opening_batches_company_id"):
        op.create_index("ix_opening_batches_company_id", "opening_batches", ["company_id"])
    if not _has_index("ix_opening_batches_fiscal_year_id"):
        op.create_index(
            "ix_opening_batches_fiscal_year_id", "opening_batches", ["fiscal_year_id"]
        )
    if not _has_table("opening_gl"):
        op.create_table(
            "opening_gl",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("batch_id", sa.String(length=36), nullable=False),
            sa.Column("account_code", sa.String(length=20), nullable=False),
            sa.Column("debit", sa.Numeric(18, 2), nullable=False),
            sa.Column("credit", sa.Numeric(18, 2), nullable=False),
            sa.Column("currency_code", sa.String(length=3), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index("ix_opening_gl_batch_id"):
        op.create_index("ix_opening_gl_batch_id", "opening_gl", ["batch_id"])
    if not _has_table("opening_bank"):
        op.create_table(
            "opening_bank",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("batch_id", sa.String(length=36), nullable=False),
            sa.Column("bank_account_id", sa.String(length=36), nullable=False),
            sa.Column("amount", sa.Numeric(18, 2), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index("ix_opening_bank_batch_id"):
        op.create_index("ix_opening_bank_batch_id", "opening_bank", ["batch_id"])


def downgrade() -> None:
    if _has_index("ix_opening_bank_batch_id"):
        op.drop_index("ix_opening_bank_batch_id", table_name="opening_bank")
    if _has_table("opening_bank"):
        op.drop_table("opening_bank")
    if _has_index("ix_opening_gl_batch_id"):
        op.drop_index("ix_opening_gl_batch_id", table_name="opening_gl")
    if _has_table("opening_gl"):
        op.drop_table("opening_gl")
    if _has_index("ix_opening_batches_fiscal_year_id"):
        op.drop_index("ix_opening_batches_fiscal_year_id", table_name="opening_batches")
    if _has_index("ix_opening_batches_company_id"):
        op.drop_index("ix_opening_batches_company_id", table_name="opening_batches")
    if _has_table("opening_batches"):
        op.drop_table("opening_batches")
