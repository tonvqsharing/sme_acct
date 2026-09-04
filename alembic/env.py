"""Alembic environment — aggregates all brick Base.metadata objects."""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import every brick's Base so their metadata tables are registered.
from src.bricks.audit_log.storage import Base as AuditBase
from src.bricks.bank_cash.storage import Base as BankBase
from src.bricks.coa.storage import Base as CoaBase
from src.bricks.company.storage import Base as CompanyBase
from src.bricks.cost_centers.storage import Base as CcBase
from src.bricks.currencies.storage import Base as CurBase
from src.bricks.document_conversion.storage import Base as DocConvBase
from src.bricks.financial_statements.storage import Base as FsBase
from src.bricks.fiscal_year_period.storage import Base as FyBase
from src.bricks.fixed_assets.storage import Base as Fabase
from src.bricks.inventory.storage import Base as InvtyBase
from src.bricks.invoice.storage import Base as InvBase
from src.bricks.party.storage import Base as PartyBase
from src.bricks.uom.storage import Base as UOMBase
from src.bricks.payment_terms.storage import Base as PtBase
from src.bricks.purchases.storage import Base as PurchBase
from src.bricks.system_settings.storage import Base as SetBase
from src.bricks.tools_equipment.storage import Base as TeBase
from src.bricks.user_master_data.storage import Base as UserBase
from src.bricks.voucher.storage import Base as VchBase

config = context.config
import os

db_url = os.environ.get("DATABASE_URL", "sqlite:///./sme_acct.db")
config.set_main_option("sqlalchemy.url", db_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = [
    CompanyBase.metadata,
    PtBase.metadata,
    AuditBase.metadata,
    FyBase.metadata,
    CoaBase.metadata,
    CcBase.metadata,
    Fabase.metadata,
    InvBase.metadata,
    InvtyBase.metadata,
    PartyBase.metadata,
    UOMBase.metadata,
    BankBase.metadata,
    PurchBase.metadata,
    SetBase.metadata,
    CurBase.metadata,
    VchBase.metadata,
    UserBase.metadata,
    TeBase.metadata,
    FsBase.metadata,
    DocConvBase.metadata,
]


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — SQL script without DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with a DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
