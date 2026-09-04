"""add master tables party/uom/inventory/tax (slices 1-3)

Revision ID: f4a9c1d2e7b5
Revises: 9c1a2b3d4e5f
Create Date: 2026-09-04

Hand-written: `alembic revision --autogenerate` is broken repo-wide
(pre-existing `tools_equipment.cost_center_id → cost_centers` FK error),
so master tables from slices 1-3 ship here explicitly. Mirrors model
definitions; new columns are nullable so existing rows stay valid.

Two DB lineages exist: app-created DBs (via `Base.create_all`) already
have the new tables but lack the new columns; alembic-only DBs may lack
whole tables (inventory brick predates migrations). Every step is
guarded → safe on both, and re-runnable.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "f4a9c1d2e7b5"
down_revision = "9c1a2b3d4e5f"
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


def _create_table(name: str, *columns, indexes: tuple = ()) -> None:
    if _has_table(name):
        return
    op.create_table(name, *columns)
    for ix_name, ix_cols in indexes:
        op.create_index(ix_name, name, ix_cols)


def upgrade() -> None:
    # -- inventory link columns (slice 4) + hot index (slice 6) -------------
    if _has_table("inventory_products"):
        if not _has_column("inventory_products", "uom_id"):
            op.add_column(
                "inventory_products", sa.Column("uom_id", sa.String(length=36), nullable=True)
            )
        if not _has_column("inventory_products", "category_id"):
            op.add_column(
                "inventory_products",
                sa.Column("category_id", sa.String(length=36), nullable=True),
            )
    if _has_table("inventory_moves"):
        if not _has_column("inventory_moves", "lot_id"):
            op.add_column(
                "inventory_moves", sa.Column("lot_id", sa.String(length=36), nullable=True)
            )
        if not _has_index("ix_moves_company_product_state"):
            op.create_index(
                "ix_moves_company_product_state",
                "inventory_moves",
                ["company_id", "product_id", "state"],
            )

    # -- parties (slice 1) -------------------------------------------------
    _create_table(
        "parties",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("mst", sa.String(length=14), nullable=True),
        sa.Column("address", sa.String(length=300), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("is_customer", sa.Boolean(), nullable=False),
        sa.Column("is_supplier", sa.Boolean(), nullable=False),
        sa.Column("is_employee", sa.Boolean(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        indexes=(
            ("ix_parties_company_id", ["company_id"]),
            ("ix_parties_code", ["code"]),
            ("ix_parties_mst", ["mst"]),
        ),
    )

    # -- departments (slice 1) ---------------------------------------------
    _create_table(
        "departments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("manager_id", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        indexes=(("ix_departments_company_id", ["company_id"]),),
    )

    # -- uoms (slice 2) ----------------------------------------------------
    _create_table(
        "uoms",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("factor", sa.Numeric(18, 6), nullable=False),
        sa.Column("base_uom_id", sa.String(length=36), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        indexes=(
            ("ix_uoms_company_id", ["company_id"]),
            ("ix_uoms_code", ["code"]),
        ),
    )

    # -- inventory_categories (slice 2) ------------------------------------
    _create_table(
        "inventory_categories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("cost_method", sa.String(length=20), nullable=True),
        sa.Column("account_code", sa.String(length=10), nullable=True),
        sa.Column("tax_category", sa.String(length=30), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        indexes=(
            ("ix_inventory_categories_company_id", ["company_id"]),
            ("ix_inventory_categories_code", ["code"]),
        ),
    )

    # -- inventory_warehouses (slice 2) ------------------------------------
    _create_table(
        "inventory_warehouses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=300), nullable=True),
        sa.Column("manager_id", sa.String(length=36), nullable=True),
        sa.Column("account_code", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        indexes=(
            ("ix_inventory_warehouses_company_id", ["company_id"]),
            ("ix_inventory_warehouses_code", ["code"]),
        ),
    )

    # -- inventory_lots (slice 3) ------------------------------------------
    _create_table(
        "inventory_lots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("lot_code", sa.String(length=30), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("qty", sa.Numeric(18, 2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        indexes=(
            ("ix_inventory_lots_company_id", ["company_id"]),
            ("ix_inventory_lots_product_id", ["product_id"]),
            ("ix_inventory_lots_lot_code", ["lot_code"]),
        ),
    )

    # -- inventory_price_lists (slice 3) -----------------------------------
    _create_table(
        "inventory_price_lists",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("uom_id", sa.String(length=36), nullable=True),
        sa.Column("price", sa.Numeric(18, 2), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        indexes=(
            ("ix_inventory_price_lists_company_id", ["company_id"]),
            ("ix_inventory_price_lists_product_id", ["product_id"]),
        ),
    )

    # -- tax_codes (slice 3) -----------------------------------------------
    _create_table(
        "tax_codes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("rate", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("account_code", sa.String(length=10), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        indexes=(
            ("ix_tax_codes_company_id", ["company_id"]),
            ("ix_tax_codes_code", ["code"]),
        ),
    )


def _drop_table(name: str, indexes: tuple = ()) -> None:
    if not _has_table(name):
        return
    for ix_name in indexes:
        if _has_index(ix_name):
            op.drop_index(ix_name, table_name=name)
    op.drop_table(name)


def downgrade() -> None:
    if _has_table("inventory_moves"):
        if _has_index("ix_moves_company_product_state"):
            op.drop_index("ix_moves_company_product_state", table_name="inventory_moves")
        if _has_column("inventory_moves", "lot_id"):
            op.drop_column("inventory_moves", "lot_id")
    if _has_column("inventory_products", "category_id"):
        op.drop_column("inventory_products", "category_id")
    if _has_column("inventory_products", "uom_id"):
        op.drop_column("inventory_products", "uom_id")
    _drop_table("tax_codes", ("ix_tax_codes_code", "ix_tax_codes_company_id"))
    _drop_table(
        "inventory_price_lists",
        ("ix_inventory_price_lists_product_id", "ix_inventory_price_lists_company_id"),
    )
    _drop_table(
        "inventory_lots",
        (
            "ix_inventory_lots_lot_code",
            "ix_inventory_lots_product_id",
            "ix_inventory_lots_company_id",
        ),
    )
    _drop_table(
        "inventory_warehouses",
        ("ix_inventory_warehouses_code", "ix_inventory_warehouses_company_id"),
    )
    _drop_table(
        "inventory_categories",
        ("ix_inventory_categories_code", "ix_inventory_categories_company_id"),
    )
    _drop_table("uoms", ("ix_uoms_code", "ix_uoms_company_id"))
    _drop_table("departments", ("ix_departments_company_id",))
    _drop_table("parties", ("ix_parties_mst", "ix_parties_code", "ix_parties_company_id"))
