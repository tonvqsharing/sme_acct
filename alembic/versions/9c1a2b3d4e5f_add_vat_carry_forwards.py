"""Add vat_carry_forwards for 01/GTGT persistence.

Revision ID: 9c1a2b3d4e5f
Revises: 7a3e2b1c4d5f
Create Date: 2026-09-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "9c1a2b3d4e5f"
down_revision = "7a3e2b1c4d5f"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "vat_carry_forwards",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), nullable=False, index=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=True),
        sa.Column("quarter", sa.Integer(), nullable=True),
        sa.Column("carry_amount", sa.Numeric(18, 2), server_default=sa.text("0")),
        sa.UniqueConstraint("company_id", "year", "month", "quarter", name="uq_vat_carry"),
    )


def downgrade() -> None:
    op.drop_table("vat_carry_forwards")
