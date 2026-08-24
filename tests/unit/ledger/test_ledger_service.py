"""Ledger report unit tests — fake voucher source."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.ledger.services import LedgerService

COMPANY = uuid4()


def _row(number, entry_date, acct, dr, cr):
    return {
        "voucher_id": "11111111-1111-1111-1111-111111111111",
        "number": number,
        "entry_date": entry_date,
        "description": "d",
        "account_code": acct,
        "debit": Decimal(dr),
        "credit": Decimal(cr),
    }


class FakeSource:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def get_posted_lines(self, company_id, start, end):
        self.calls.append((company_id, start, end))
        return [r for r in self.rows if start <= date.fromisoformat(r["entry_date"]) <= end]


ROWS = [
    _row("PT/000001", "2026-08-01", "1121", "11000000", "0"),
    _row("PT/000001", "2026-08-01", "5111", "0", "11000000"),
    _row("PT/000002", "2026-08-15", "1311", "5000000", "0"),
    _row("PT/000002", "2026-08-15", "5111", "0", "5000000"),
    _row("PC/000001", "2026-09-01", "1121", "0", "2000000"),
    _row("PC/000001", "2026-09-01", "6421", "2000000", "0"),
]


@pytest.fixture()
def svc():
    src = FakeSource(ROWS)
    return LedgerService(source=src), src


class TestGeneralJournal:
    def test_chronological_with_lines(self, svc):
        ledger, _ = svc
        entries = ledger.general_journal(COMPANY, date(2026, 8, 1), date(2026, 9, 30))
        assert [e["number"] for e in entries] == [
            "PT/000001",
            "PT/000002",
            "PC/000001",
        ]
        assert len(entries[0]["lines"]) == 2
        assert entries[0]["total_debit"] == Decimal(11000000)

    def test_date_range_filters(self, svc):
        ledger, src = svc
        entries = ledger.general_journal(COMPANY, date(2026, 8, 1), date(2026, 8, 31))
        assert len(entries) == 2  # September excluded
        assert src.calls[-1][1:] == (
            date(2026, 8, 1),
            date(2026, 8, 31),
        )


class TestTrialBalance:
    def test_aggregates_per_account(self, svc):
        ledger, _ = svc
        tb = ledger.trial_balance(COMPANY, date(2026, 8, 1), date(2026, 9, 30))
        by_code = {r["account_code"]: r for r in tb}
        assert by_code["1121"]["debit"] == Decimal(11000000)
        assert by_code["1121"]["credit"] == Decimal(2000000)
        assert by_code["5111"]["debit"] == Decimal(0)
        assert by_code["5111"]["credit"] == Decimal(16000000)
        # 33311 absent (no activity)
        assert "33311" not in by_code

    def test_totals_balance(self, svc):
        """Report sanity: Σ debit == Σ credit across all accounts."""
        ledger, _ = svc
        tb = ledger.trial_balance(COMPANY, date(2026, 8, 1), date(2026, 9, 30))
        total_dr = sum((r["debit"] for r in tb), Decimal(0))
        total_cr = sum((r["credit"] for r in tb), Decimal(0))
        assert total_dr == total_cr

    def test_net_movement_by_normal_side(self, svc):
        ledger, _ = svc
        balances = {
            r["account_code"]: r["net_debit"]
            for r in ledger.trial_balance(COMPANY, date(2026, 8, 1), date(2026, 9, 30))
        }
        # Asset 1121: net debit positive; Revenue 5111: net debit negative
        assert balances["1121"] == Decimal(9000000)
        assert balances["5111"] == Decimal(-16000000)
