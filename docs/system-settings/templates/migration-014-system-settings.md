# Template: Database Migration — Add System Settings Module

---

## Migration: 014_add_system_settings.py (Flask-Migrate)

```python
"""add_system_settings

Revision ID: 014_system_settings
Revises: 013_previous
Create Date: 2026-08-17

Revision Breakdown:
  1. CREATE TABLE company_configs
  2. CREATE TABLE audit_log
  3. CREATE TABLE period_locks
  4. CREATE TABLE e_invoice_series
  5. CREATE TABLE config_changes
  6. CREATE TABLE invoice_series_log
  7. Add REVOKE DELETE constraints on audit_log
  8. Add triggers for series max count and period unique
  9. Seed default CompanyConfig for existing companies (retroactive creation)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "014_system_settings"
down_revision = "013_previous"
branch_labels = None
depends_on = None


def upgrade():
    # 1. company_configs
    op.create_table(
        "company_configs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("accounting_period_type", sa.String(20), nullable=False),
        sa.Column("accounting_regime", sa.String(30), nullable=False),
        sa.Column("chart_of_accounts_type", sa.String(30), nullable=False),
        sa.Column("vat_rates", sa.JSON(), server_default="[0,5,10]", nullable=False),
        sa.Column("minimum_retention_years", sa.Integer, server_default="10", nullable=False),
        sa.Column("data_deletable", sa.Boolean, server_default="false", nullable=False),
        sa.Column("fiscal_year_start_month", sa.Integer, server_default="1", nullable=False),
        sa.Column("fiscal_year_start_day", sa.Integer, server_default="1", nullable=False),
        sa.Column("vat_settlement_cycle", sa.String(20), server_default="monthly", nullable=False),
        sa.Column("vat_method", sa.String(20), server_default="deduction", nullable=False),
        sa.Column("e_invoice_mode", sa.String(20), server_default="software_cert", nullable=False),
        sa.Column("ca_list", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("decimal_places", sa.Integer, server_default="2", nullable=False),
        sa.Column("default_currency", sa.String(3), server_default="VND", nullable=False),
        sa.Column("cost_center_required", sa.Boolean, server_default="false", nullable=False),
        sa.Column("multi_level_cost_centers", sa.Boolean, server_default="false", nullable=False),
        sa.Column("data_retention_years", sa.Integer, server_default="10", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.UUID(), nullable=False),
        sa.Column("config_version", sa.Integer, server_default="1", nullable=False),
        sa.Column("legal_reviewed_at", sa.DateTime()),
        sa.Column("legal_reviewed_by", sa.UUID()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", name="uq_company_configs"),
    )
    op.create_index("idx_configs_company", "company_configs", ["company_id"])

    # 2. audit_log
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("actor_user_id", sa.UUID()),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", sa.UUID()),
        sa.Column("before_value", sa.JSON()),
        sa.Column("after_value", sa.JSON()),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_log_company_time", "audit_log", ["company_id", "created_at"])

    # 3. period_locks
    op.create_table(
        "period_locks",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("accounting_period", sa.Integer, nullable=False),  # 1-12 or custom
        sa.Column("lock_type", sa.String(20), nullable=False),
        sa.Column("locked_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("locked_by", sa.UUID(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id", "fiscal_year", "accounting_period",
            name="uq_period_locks"
        ),
    )
    op.create_index("idx_period_locks_company", "period_locks", ["company_id", "fiscal_year", "accounting_period"])

    # 4. e_invoice_series
    op.create_table(
        "e_invoice_series",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("prefix", sa.String(20), nullable=False),
        sa.Column("next_sequence", sa.Integer, nullable=False),
        sa.Column("active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("ca_signer", sa.String(100)),
        sa.Column("declared_to_gdt_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "prefix", name="uq_invoice_series"),
        sa.CheckConstraint("next_sequence >= 1", name="chk_next_sequence_positive"),
    )
    op.create_index("idx_invoice_series_company", "e_invoice_series", ["company_id"])

    # 5. config_changes
    op.create_table(
        "config_changes",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("config_version", sa.Integer, nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=False),
        sa.Column("flag_name", sa.String(100), nullable=False),
        sa.Column("flag_type", sa.String(20), nullable=False),
        sa.Column("before_value", sa.JSON()),
        sa.Column("after_value", sa.JSON()),
        sa.Column("change_reason", sa.Text()),
        sa.Column("legal_reviewed", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_config_changes_company", "config_changes", ["company_id", "config_version"])

    # 6. invoice_series_log
    op.create_table(
        "invoice_series_log",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("series_id", sa.UUID(), nullable=False),
        sa.Column("seq_used", sa.Integer, nullable=False),
        sa.Column("actor", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_invoice_series_log", "invoice_series_log", ["series_id", "seq_used"])

    # 7. REVOKE DELETE on audit_log (PostgreSQL)
    op.execute("""
        REVOKE DELETE ON audit_log FROM PUBLIC;
        REVOKE UPDATE ON audit_log FROM PUBLIC;
    """)

    # 8. Trigger: max 15 active series per company (PostgreSQL)
    op.execute("""
        CREATE OR REPLACE FUNCTION check_max_series()
        RETURNS TRIGGER AS $$
        BEGIN
          IF (SELECT COUNT(*) FROM e_invoice_series
              WHERE company_id = NEW.company_id AND active = true)
            >= 15 THEN
            RAISE EXCEPTION 'Max 15 active e-invoice series per company (GDT)';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER tgr_max_series
        BEFORE INSERT OR UPDATE ON e_invoice_series
        FOR EACH ROW EXECUTE FUNCTION check_max_series();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS tgr_max_series ON e_invoice_series;")
    op.execute("DROP FUNCTION IF EXISTS check_max_series();")
    op.drop_table("invoice_series_log")
    op.drop_table("config_changes")
    op.drop_table("e_invoice_series")
    op.drop_table("period_locks")
    op.drop_table("audit_log")
    op.drop_table("company_configs")
```