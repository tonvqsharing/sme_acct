"""Voucher post mirrors journal lines into cash balances (core loop)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    UUID_CHIEF,
    FakeUser,
    _store,
)

COMPANY = "99999999-1111-2222-3333-444444444444"


def _client(app, uid, role):
    u = FakeUser(uid, role)
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def seeded(app):
    from src.bricks.payment_terms.web_adapter import _series_service as ss

    app.fy_service.create_year(
        UUID(COMPANY),
        "2026",
        date(2026, 1, 1),
        date(2026, 12, 31),
        "MONTHLY",
        actor=uuid4(),
        reason="fy",
    )
    coa = app.coa_service
    for code, name in (("5111", "Doanh thu"),):
        coa.create_account(UUID(COMPANY), code, name, actor=uuid4(), reason="c")
    coa.create_account(UUID(COMPANY), "111", "Tiền mặt (agg)", actor=uuid4(), reason="c")
    coa.create_account(UUID(COMPANY), "131", "Phải thu KH", actor=uuid4(), reason="c")
    coa.create_account(
        UUID(COMPANY),
        "1311",
        "Phải thu chi tiết",
        parent_code="131",
        actor=uuid4(),
        reason="c",
    )
    for pfx in ("PT/", "PC/"):
        ss.create_series(company_id=UUID(COMPANY), prefix=pfx, actor=uuid4(), reason="s")
    from src.bricks.bank_cash.web_adapter import _cash_service as cash_svc

    cash_svc.create_cash_account(
        company_id=UUID(COMPANY),
        code="1111",
        name="Quỹ tổng",
        opening_balance=Decimal(1000000),
        actor=uuid4(),
        reason="seed",
    )
    coa.create_account(
        UUID(COMPANY),
        "1111",
        "Tiền mặt chi tiết",
        parent_code="111",
        actor=uuid4(),
        reason="c",
    )


RECEIPT = {
    "company_id": COMPANY,
    "entry_date": "2026-08-01",
    "description": "Thu tiền mặt",
    "lines": [
        {"account_code": "1111", "debit": "500000", "credit": "0"},
        {"account_code": "5111", "debit": "0", "credit": "500000"},
    ],
}


class TestVoucherCashLink:
    def test_receipt_increases_cash(self, app, seeded):
        acc = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
        r = acc.post("/api/v1/vouchers", json=RECEIPT)
        assert r.status_code == 201
        vid = r.get_json()["data"]["id"]

        p = acc.post(f"/api/v1/vouchers/{vid}/post", json={"reason": "ok"})
        assert p.status_code == 200

        from src.bricks.bank_cash.web_adapter import _cash_service as cs

        cash = cs.get_by_code(UUID(COMPANY), "1111")
        assert cash is not None
        assert cash.current_balance == Decimal(1500000)

    def test_overdraw_blocks_post_and_keeps_draft(self, app, seeded):
        acc = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
        bad = {
            **RECEIPT,
            "lines": [
                {"account_code": "1111", "debit": "0", "credit": "1500000"},
                {"account_code": "5111", "debit": "1500000", "credit": "0"},
            ],
        }
        r = acc.post("/api/v1/vouchers", json=bad)
        vid = r.get_json()["data"]["id"]
        p = acc.post(f"/api/v1/vouchers/{vid}/post", json={"reason": "chi"})
        assert p.status_code == 409
        assert p.get_json()["code"] == "NEGATIVE_BALANCE"
        # voucher remains DRAFT — no partial state
        detail = acc.get(f"/api/v1/vouchers/{vid}").get_json()["data"]
        assert detail["status"] == "DRAFT"

    def test_chief_may_overdraw_and_post(self, app, seeded):
        chief = _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT")
        bad = {
            **RECEIPT,
            "lines": [
                {"account_code": "1111", "debit": "0", "credit": "1500000"},
                {"account_code": "5111", "debit": "1500000", "credit": "0"},
            ],
        }
        vid = chief.post("/api/v1/vouchers", json=bad).get_json()["data"]["id"]
        p = chief.post(f"/api/v1/vouchers/{vid}/post", json={"reason": "approved"})
        assert p.status_code == 200
        from src.bricks.bank_cash.web_adapter import _cash_service as cs

        cash = cs.get_by_code(UUID(COMPANY), "1111")
        assert cash is not None
        assert cash.current_balance == Decimal(-500000)  # chief-approved overdraft

    def test_non_cash_lines_untouched(self, app, seeded):
        acc = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
        v = {
            "company_id": COMPANY,
            "entry_date": "2026-08-02",
            "description": "không liên quỹ",
            "lines": [
                {"account_code": "1311", "debit": "10", "credit": "0"},
                {"account_code": "5111", "debit": "0", "credit": "10"},
            ],
        }
        vid = acc.post("/api/v1/vouchers", json=v).get_json()["data"]["id"]
        assert acc.post(f"/api/v1/vouchers/{vid}/post", json={"reason": "ok"}).status_code == 200
        from src.bricks.bank_cash.web_adapter import _cash_service as cs

        cash = cs.get_by_code(UUID(COMPANY), "1111")
        assert cash is not None
        assert cash.current_balance == Decimal(1000000)


class TestAggregateCashBlocked:
    def test_journal_line_on_111_rejected(self, app, seeded):
        from tests.integration.test_voucher_cash_link import _client

        acc = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
        r = acc.post(
            "/api/v1/vouchers",
            json={
                "company_id": COMPANY,
                "entry_date": "2026-08-03",
                "description": "aggregate không được đăng ký",
                "lines": [
                    {"account_code": "111", "debit": "10", "credit": "0"},
                    {"account_code": "5111", "debit": "0", "credit": "10"},
                ],
            },
        )
        assert r.status_code == 422
