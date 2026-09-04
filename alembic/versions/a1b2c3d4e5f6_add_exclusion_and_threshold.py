"""add excluded_8pct_categories + supplier threshold (config slice 2)

Revision ID: a1b2c3d4e5f6
Revises: f4a9c1d2e7b5
Create Date: 2026-09-04

Hand-written (autogenerate broken repo-wide, pre-existing FK error).
Every step guarded → safe on both DB lineages, re-runnable.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "f4a9c1d2e7b5"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return insp.has_table(table) and column in {c["name"] for c in insp.get_columns(table)}


def _has_index(name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(
        ix["name"] == name for table in insp.get_table_names() for ix in insp.get_indexes(table)
    )


def upgrade() -> None:
    if not _has_table("excluded_8pct_categories"):
        op.create_table(
            "excluded_8pct_categories",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("company_id", sa.String(length=36), nullable=False),
            sa.Column("category", sa.String(length=50), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index("ix_excluded_8pct_company_id"):
        op.create_index("ix_excluded_8pct_company_id", "excluded_8pct_categories", ["company_id"])
    if not _has_index("ix_excluded_8pct_category"):
        op.create_index("ix_excluded_8pct_category", "excluded_8pct_categories", ["category"])
    if _has_table("supplier_invoices") and not _has_column(
        "supplier_invoices", "non_cash_threshold"
    ):
        op.add_column(
            "supplier_invoices",
            sa.Column("non_cash_threshold", sa.Numeric(18, 2), nullable=True),
        )


def downgrade() -> None:
    if _has_index("ix_excluded_8pct_category"):
        op.drop_index("ix_excluded_8pct_category", table_name="excluded_8pct_categories")
    if _has_index("ix_excluded_8pct_company_id"):
        op.drop_index("ix_excluded_8pct_company_id", table_name="excluded_8pct_categories")
    if _has_table("excluded_8pct_categories"):
        op.drop_table("excluded_8pct_categories")
    if _has_column("supplier_invoices", "non_cash_threshold"):
        op.drop_column("supplier_invoices", "non_cash_threshold")
