"""Add report templates, instances, and retained earnings tables.

Revision ID: 7a3e2b1c4d5f
Revises: 04f5e599b70b
Create Date: 2026-08-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "7a3e2b1c4d5f"
down_revision = "04f5e599b70b"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "report_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(10), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), server_default=""),
        sa.Column("company_id", sa.String(36), nullable=True, index=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1")),
    )

    op.create_table(
        "report_template_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("template_id", sa.String(36), sa.ForeignKey("report_templates.id"), nullable=False),
        sa.Column("line_code", sa.String(20), nullable=False),
        sa.Column("line_name", sa.String(200), nullable=False),
        sa.Column("line_type", sa.String(20), nullable=False),
        sa.Column("account_codes", sa.JSON(), nullable=True),
        sa.Column("formula", sa.String(500), nullable=True),
        sa.Column("parent_code", sa.String(20), nullable=True),
        sa.Column("level", sa.Integer(), server_default=sa.text("0")),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0")),
        sa.Column("sign", sa.Integer(), server_default=sa.text("1")),
    )
    op.create_index("ix_report_template_lines_template", "report_template_lines", ["template_id"])

    op.create_table(
        "report_instances",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("template_id", sa.String(36), sa.ForeignKey("report_templates.id"), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False, index=True),
        sa.Column("period_from", sa.Date(), nullable=False),
        sa.Column("period_to", sa.Date(), nullable=False),
        sa.Column("status", sa.String(10), server_default="DRAFT"),
    )
    op.create_index("ix_report_instances_template", "report_instances", ["template_id"])

    op.create_table(
        "report_instance_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("instance_id", sa.String(36), sa.ForeignKey("report_instances.id"), nullable=False),
        sa.Column("line_code", sa.String(20), nullable=False),
        sa.Column("line_name", sa.String(200), nullable=False),
        sa.Column("value_current", sa.Text(), server_default=sa.text("0")),
        sa.Column("value_prior", sa.Text(), nullable=True),
    )
    op.create_index("ix_report_instance_lines_instance", "report_instance_lines", ["instance_id"])

    op.create_table(
        "retained_earnings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), nullable=False, index=True),
        sa.Column("fiscal_year_id", sa.String(36), nullable=False),
        sa.Column("opening_balance", sa.Text(), server_default=sa.text("0")),
        sa.Column("net_income", sa.Text(), server_default=sa.text("0")),
        sa.Column("dividends", sa.Text(), server_default=sa.text("0")),
        sa.Column("checksum", sa.String(64), server_default=""),
        sa.UniqueConstraint("company_id", "fiscal_year_id"),
    )


def downgrade() -> None:
    op.drop_table("retained_earnings")
    op.drop_table("report_instance_lines")
    op.drop_index("ix_report_instances_template")
    op.drop_table("report_instances")
    op.drop_index("ix_report_template_lines_template")
    op.drop_table("report_template_lines")
    op.drop_table("report_templates")
