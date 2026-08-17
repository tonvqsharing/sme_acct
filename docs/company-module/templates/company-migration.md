# Template: Database Migration — Add Company Module

## Migration: 013_add_company.py (Flask-Migrate / Alembic)

```python
"""add_company

Revision ID: 013_company
Revises: 012_previous
Create Date: 2026-08-17

Scope:
  1. CREATE TABLE companies
  2. ADD COLUMN company_id to partners (nullable)
  3. ADD COLUMN company_id to invoices (nullable)
  4. ADD COLUMN company_id to vouchers (nullable)
  5. CREATE UNIQUE INDEX on companies.mst
  6. CREATE INDEX on companies.status
"""

from alembic import op
import sqlalchemy as sa

revision = "013_company"
down_revision = "012_previous"
branch_labels = None
depends_on = None


def upgrade():
    # 1. companies table
    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=False),
        sa.Column("mst", sa.String(20), nullable=False),
        sa.Column("headquarters_address", sa.String(500), nullable=False, default=""),
        sa.Column("legal_representative", sa.String(255), nullable=False, default=""),
        sa.Column("business_reg_number", sa.String(100)),
        sa.Column("business_reg_date", sa.Date()),
        sa.Column("business_fields", sa.JSON(), server_default="[]"),
        sa.Column("company_type", sa.String(30), nullable=False, default="multi_llc"),
        sa.Column("accounting_regime", sa.String(30), nullable=False, default="tt99"),
        sa.Column("status", sa.String(30), nullable=False, default="active"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("fiscal_year_start_month", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("fiscal_year_start_day", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("responsible_accountant_name", sa.String(255), nullable=False, default=""),
        sa.Column("responsible_accountant_license", sa.String(100)),
        sa.Column("tax_agency", sa.String(300), nullable=False, default=""),
        sa.Column("controlling_tax_office", sa.String(300), nullable=False, default=""),
        sa.Column("bhxh_code", sa.String(50)),
        sa.Column("bhxh_agency", sa.String(300)),
        sa.Column("authorized_capital", sa.Numeric(18, 2), server_default="0"),
        sa.Column("phone", sa.String(30), nullable=False, default=""),
        sa.Column("email", sa.String(120), nullable=False, default=""),
        sa.Column("website", sa.String(255), nullable=False, default=""),
        sa.Column("short_name", sa.String(100)),
        sa.Column("bank_accounts", sa.JSON(), server_default="[]"),
        sa.Column("created_at", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("updated_at", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("updated_by", sa.UUID(), nullable=False),
        sa.Column("config_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("legal_reviewed_at", sa.Date()),
        sa.Column("legal_reviewed_by", sa.UUID()),
        sa.Column("mst_changed_at", sa.Date()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mst", name="uq_companies_mst"),
        sa.CheckConstraint("fiscal_year_start_month BETWEEN 1 AND 12", name="chk_fy_month"),
        sa.CheckConstraint("fiscal_year_start_day BETWEEN 1 AND 31", name="chk_fy_day"),
    )
    op.create_index("idx_companies_mst", "companies", ["mst"])
    op.create_index("idx_companies_status", "companies", ["status", "is_active"])

    # 2. Add company_id to partners (nullable for backfill)
    op.add_column("partners", sa.Column("company_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_partners_company", "partners", "companies", ["company_id"], ["id"])

    # 3. Add company_id to invoices
    op.add_column("invoices", sa.Column("company_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_invoices_company", "invoices", "companies", ["company_id"], ["id"])

    # 4. Add company_id to vouchers
    op.add_column("vouchers", sa.Column("company_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_vouchers_company", "vouchers", "companies", ["company_id"], ["id"])


def downgrade():
    op.drop_constraint("fk_vouchers_company", "vouchers", type_="foreignkey")
    op.drop_column("vouchers", "company_id")
    op.drop_constraint("fk_invoices_company", "invoices", type_="foreignkey")
    op.drop_column("invoices", "company_id")
    op.drop_constraint("fk_partners_company", "partners", type_="foreignkey")
    op.drop_column("partners", "company_id")
    op.drop_index("idx_companies_status", table_name="companies")
    op.drop_index("idx_companies_mst", table_name="companies")
    op.drop_table("companies")
```

---

## Post-Migration Backfill Steps

1. Insert a single default company (for existing single-company deployments):
```sql
INSERT INTO companies (legal_name, mst, headquarters_address, legal_representative,
                       company_type, accounting_regime, status, created_by, updated_by)
VALUES ('Default Company', '0000000000', '', '', 'multi_llc', 'tt99', 'active',
        'system', 'system');
```

2. Identify and backfill existing records:
```sql
-- For single-company deployments, all existing records belong to default company
UPDATE partners SET company_id = '<default-uuid>' WHERE company_id IS NULL;
UPDATE invoices SET company_id = '<default-uuid>' WHERE company_id IS NULL;
UPDATE vouchers SET company_id = '<default-uuid>' WHERE company_id IS NULL;
```

3. After backfill verified, add NOT NULL constraint:
```sql
ALTER TABLE partners ALTER COLUMN company_id SET NOT NULL;
ALTER TABLE invoices ALTER COLUMN company_id SET NOT NULL;
ALTER TABLE vouchers ALTER COLUMN company_id SET NOT NULL;
```

---