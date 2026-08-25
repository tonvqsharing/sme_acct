"""Settings API — tax-rates catalog + SOD series add via real factory."""

from __future__ import annotations

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    UUID_ADMIN,
    UUID_CHIEF,
    FakeUser,
    _store,
)

COMPANY = "14141414-1414-1414-1414-141414141414"


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


class TestSettingsApi:
    def test_tax_rate_catalog_public_to_authenticated(self, app):
        c = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
        r = c.get("/api/v1/system-settings/tax-rates")
        assert r.status_code == 200
        names = {x["name"] for x in r.get_json()["data"]}
        assert names == {"VAT_0", "VAT_5", "VAT_10", "NOT_TAXED"}

    def test_unauthenticated_401(self, app):
        r = app.test_client().get("/api/v1/system-settings/tax-rates")
        assert r.status_code == 401

    def test_default_config_has_law_rates(self, app):
        c = _client(app, UUID_ADMIN, "ADMIN")
        r = c.get(f"/api/v1/system-settings/config/{COMPANY}")
        assert r.status_code == 200
        assert r.get_json()["data"]["vat_rates"] == [0, 5, 10]

    def test_add_series_sod_flow(self, app):
        chief = _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT")
        admin_id = UUID_ADMIN
        # admin requests (actor), chief approves (approver)
        admin = _client(app, UUID_ADMIN, "ADMIN")
        r = admin.post(
            "/api/v1/system-settings/e-invoice-series",
            json={
                "company_id": COMPANY,
                "prefix": "HD/",
                "ca_signer": "VNPT",
                "approver": admin_id,  # self → SOD
            },
        )
        assert r.status_code == 403
        assert r.get_json()["code"] == "SOD_VIOLATION"

        # actor = chief session; approver = ADMIN id (distinct person)
        sys_actor_admin_id = UUID_ADMIN
        ok = chief.post(
            "/api/v1/system-settings/e-invoice-series",
            json={
                "company_id": COMPANY,
                "prefix": "HD/",
                "ca_signer": "VNPT",
                "approver": sys_actor_admin_id,
            },
        )
        assert ok.status_code == 201, ok.get_json()
        cfg = chief.get(f"/api/v1/system-settings/config/{COMPANY}").get_json()["data"]
        assert any(s["prefix"] == "HD/" for s in cfg["e_invoice_series"])

    def test_accountant_cannot_add_series(self, app):
        acc = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
        r = acc.post(
            "/api/v1/system-settings/e-invoice-series",
            json={
                "company_id": COMPANY,
                "prefix": "AB/",
                "approver": UUID_CHIEF,
            },
        )
        assert r.status_code == 403
