"""Purchases repo integration — SQLite round-trip incl. dedup key."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.bricks.purchases.domain import (
    PaymentMethod,
    PurchaseStatus,
    SupplierInvoice,
    SupplierLine,
)
from src.bricks.purchases.storage import (
    Base,
    SQLAlchemySupplierInvoiceRepository,
)

C = uuid4()


@pytest.fixture()
def repo():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield SQLAlchemySupplierInvoiceRepository(sessionmaker(bind=engine)())
    engine.dispose()


def _inv(**over):
    base = {
        "company_id": C,
        "supplier_name": "NCC A",
        "supplier_mst": "0101234567",
        "invoice_number": "0001234",
        "invoice_symbol": "1C26TYY",
        "invoice_date": date(2026, 8, 20),
        "entry_date": date(2026, 8, 21),
        "lines": [SupplierLine("6421", "VP", Decimal(2000000), Decimal("0.1"))],
        "payment_method": PaymentMethod.BANK,
        "payment_proof": True,
    }
    base.update(over)
    return SupplierInvoice(**base)


class TestRepo:
    def test_round_trip_preserves_fields_and_lines(self, repo):
        created = repo.create(_inv())
        loaded = repo.get_by_id(created.id)
        assert loaded is not None
        assert loaded.supplier_name == "NCC A"
        assert loaded.subtotal == Decimal(2000000)
        assert loaded.total_payment == Decimal(2200000)
        assert loaded.lines[0].expense_account == "6421"
        assert loaded.status == PurchaseStatus.DRAFT

    def test_duplicate_key_detected(self, repo):
        repo.create(_inv())
        assert repo.exists_duplicate(C, "0101234567", "0001234", "1C26TYY") is True
        assert repo.exists_duplicate(C, "0101234567", "0001235", "1C26TYY") is False

    def test_tenant_scoped_duplicate_check(self, repo):
        other = uuid4()
        repo.create(_inv())
        assert repo.exists_duplicate(other, "0101234567", "0001234", "1C26TYY") is False

    def test_update_status_only_projection(self, repo):
        inv = repo.create(_inv())
        from src.bricks.purchases.domain import PurchaseStatus as PS

        inv.status = PS.POSTED
        repo.update(inv)
        loaded = repo.get_by_id(inv.id)
        assert loaded is not None and loaded.status == PS.POSTED
