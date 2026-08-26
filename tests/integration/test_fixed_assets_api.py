"""Fixed Assets integration tests — real create_app + SQLite."""

from __future__ import annotations

from uuid import UUID

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    FakeUser,
    _store,
)

COMPANY = "19191919-1919-1919-1919-191919191919"


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
    from uuid import uuid4 as _u

    app.coa_service.create_account(UUID(COMPANY), "6421", "Chi QLDN", actor=_u(), reason="c")


@pytest.fixture()
def accountant(app, seeded):
    return _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")


BODY = {
    "company_id": COMPANY,
    "asset_code": "TSCD/0001",
    "name": "Máy Photocopy Ricoh",
    "category": "huu_hinh",
    "original_cost": "50000000",
    "acquisition_date": "2026-01-15",
    "useful_life_months": 60,
    "depreciation_account": "6421",
}


class TestFAIntegration:
    def test_create_and_get_roundtrip(self, accountant):
        r = accountant.post("/api/v1/fixed-assets", json=BODY)
        assert r.status_code == 201, r.get_json()
        d = r.get_json()["data"]
        assert d["monthly_depreciation"] == 833333.0
        assert len(d["checksum"]) == 64

        g = accountant.get(f"/api/v1/fixed-assets/{d['id']}")
        assert g.status_code == 200
        assert g.get_json()["data"]["book_value"] == 50_000_000.0

    def test_duplicate_409(self, accountant):
        accountant.post("/api/v1/fixed-assets", json=BODY)
        dup = accountant.post("/api/v1/fixed-assets", json=BODY)
        assert dup.status_code == 409
        assert dup.get_json()["code"] == "DUPLICATE_ASSET_CODE"

    def test_auditor_cannot_write(self, app):
        from tests.integration.conftest import UUID_AUDITOR

        aud = _client(app, UUID_AUDITOR, "AUDITOR")
        assert aud.post("/api/v1/fixed-assets", json=BODY).status_code == 403
