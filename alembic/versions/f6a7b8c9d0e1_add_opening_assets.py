"""Add opening_assets table (S4a).

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def _has_table(bind, name: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return name in insp.get_table_names()
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "opening_assets"):
        return
    op.create_table(
        "opening_assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("batch_id", sa.String(36), sa.ForeignKey("opening_batches.id"), index=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("original_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("remaining_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("months_left", sa.Integer(), nullable=False),
        sa.Column("expense_account", sa.String(20), nullable=False),
    )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "opening_assets"):
        op.drop_table("opening_assets")
