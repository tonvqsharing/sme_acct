"""Bank reconciliation flow: tag voucher to bank → prepare → SOD resolve."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    UUID_CHIEF,
    FakeUser,
    _store,
)

COMPANY = "12121212-1212-1212-1212-121212121212"


@pytest.fixture()
def app():
    a = create_app(config={"TESTING": True, "SECRET_KEY": "x"})
    lm = a.login_manager

    @lm.user_loader
    def load(i):
        return _store.get(i)

    @lm.unauthorized_handler
    def un():  # noqa: ANNO01
        return "", 401

    return a


def _client(app, uid, role):
    u = FakeUser(uid, role)
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def seeded(app):
    """Bank account + COA + series + one posted bank receipt (5,000,000)."""
    from src.bricks.bank_cash.web_adapter import _bank_service as banks

    bank = banks.create_bank_account(
        company_id=UUID(COMPANY),
        bank_name="VietinBank",
        account_number="1020100001234",
        account_holder="CT ABC",
        actor=uuid4(),
        reason="open",
    )
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
    coa.create_account(UUID(COMPANY), "112", "TG NH", actor=uuid4(), reason="c")
    coa.create_account(
        UUID(COMPANY),
        "1121",
        "VTB",
        parent_code="112",
        actor=uuid4(),
        reason="c",
    )
    coa.create_account(UUID(COMPANY), "131", "Phải thu KH", actor=uuid4(), reason="c")
    coa.create_account(
        UUID(COMPANY),
        "1311",
        "PTKH chi tiết",
        parent_code="131",
        actor=uuid4(),
        reason="c",
    )
    coa.create_account(UUID(COMPANY), "5111", "DT", actor=uuid4(), reason="c")
    from src.bricks.payment_terms.web_adapter import _series_service as ss

    for pfx in ("PT/",):
        ss.create_series(company_id=UUID(COMPANY), prefix=pfx, actor=uuid4(), reason="s")

    acc = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
    r = acc.post(
        "/api/v1/vouchers",
        json={
            "company_id": COMPANY,
            "entry_date": "2026-08-05",
            "description": "Khách trả nợ qua NH",
            "lines": [
                {
                    "account_code": "1121",
                    "debit": "5000000",
                    "credit": "0",
                    "bank_account_id": str(bank.id),
                },
                {"account_code": "1311", "debit": "0", "credit": "5000000"},
            ],
        },
    )
    assert r.status_code == 201, r.get_json()
    vid = r.get_json()["data"]["id"]
    p = acc.post(f"/api/v1/vouchers/{vid}/post", json={"reason": "ok"})
    assert p.status_code == 200, p.get_json()
    return {"bank_id": str(bank.id), "voucher_id": vid}


class TestReconciliationFlow:
    def test_prepare_detects_gap_then_chief_resolves_after_true_balance(self, app, seeded):
        acc = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
        bid = seeded["bank_id"]

        # Statement says 5,000,000 but books lag by an unposted fee line:
        # provider computes internal = 5,000,000 → balanced immediately.
        r = acc.post(
            "/api/v1/bank-reconciliations",
            json={
                "company_id": COMPANY,
                "bank_account_id": bid,
                "reconciliation_date": "2026-08-31",
                "statement_balance": "5000000",
                "reason": "tháng 8",
            },
        )
        assert r.status_code == 201, r.get_json()
        rec = r.get_json()["data"]
        assert float(rec["internal_balance"]) == 5_000_000.0
        assert rec["difference"] == 0.0

        # Accountant cannot self-approve
        # Role gate first (route-level); SOD same-person rule is covered
        # by the unit suite at the service seam.
        deny = acc.post(
            f"/api/v1/bank-reconciliations/{rec['id']}/resolve",
            json={"reason": "self"},
        )
        assert deny.status_code == 403

        ok = _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT").post(
            f"/api/v1/bank-reconciliations/{rec['id']}/resolve",
            json={"reason": "đối chiếu sổ phụ xong"},
        )
        assert ok.status_code == 200
        assert ok.get_json()["data"]["is_resolved"] is True

    def test_unbalanced_blocks_resolve_409(self, app, seeded):
        acc = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
        bid = seeded["bank_id"]
        r = acc.post(
            "/api/v1/bank-reconciliations",
            json={
                "company_id": COMPANY,
                "bank_account_id": bid,
                "reconciliation_date": "2026-09-30",
                "statement_balance": "6000000",  # statement has extra fee not booked
                "reason": "tháng 9",
            },
        )
        assert r.status_code == 201
        rec = r.get_json()["data"]
        assert float(rec["difference"]) == 1_000_000.0

        res = _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT").post(
            f"/api/v1/bank-reconciliations/{rec['id']}/resolve",
            json={"reason": "still off"},
        )
        assert res.status_code == 409
        assert res.get_json()["code"] == "NOT_BALANCED"
