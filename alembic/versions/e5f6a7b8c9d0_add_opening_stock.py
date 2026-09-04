"""add opening_stock (opening S3)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-04

Hand-written (autogenerate broken repo-wide, pre-existing FK error).
Guarded → safe on both DB lineages, re-runnable.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _has_index(name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(
        ix["name"] == name for table in insp.get_table_names() for ix in insp.get_indexes(table)
    )


def upgrade() -> None:
    if not _has_table("opening_stock"):
        op.create_table(
            "opening_stock",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("batch_id", sa.String(length=36), nullable=False),
            sa.Column("product_id", sa.String(length=36), nullable=False),
            sa.Column("warehouse_id", sa.String(length=36), nullable=False),
            sa.Column("qty", sa.Numeric(18, 2), nullable=False),
            sa.Column("total_value", sa.Numeric(18, 2), nullable=False),
            sa.Column("lot_code", sa.String(length=30), nullable=True),
            sa.Column("expiry_date", sa.Date(), nullable=True),
            sa.Column("receipt_date", sa.Date(), nullable=True),
            sa.Column("receipt_doc", sa.String(length=50), nullable=True),
            sa.Column("unit_cost", sa.Numeric(18, 2), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index("ix_opening_stock_batch_id"):
        op.create_index("ix_opening_stock_batch_id", "opening_stock", ["batch_id"])
    if not _has_index("ix_opening_stock_product_id"):
        op.create_index("ix_opening_stock_product_id", "opening_stock", ["product_id"])


def downgrade() -> None:
    if _has_index("ix_opening_stock_product_id"):
        op.drop_index("ix_opening_stock_product_id", table_name="opening_stock")
    if _has_index("ix_opening_stock_batch_id"):
        op.drop_index("ix_opening_stock_batch_id", table_name="opening_stock")
    if _has_table("opening_stock"):
        op.drop_table("opening_stock")
