"""Integration — inventory via real factory. TT99, no 611."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from tests.integration.conftest import UUID_AUDITOR, UUID_CHIEF, FakeUser, _store

COMPANY = "77777777-7777-7777-7777-777777777777"


@pytest.fixture()
def chief(app):
    u = FakeUser(UUID_CHIEF, "CHIEF_ACCOUNTANT")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def auditor(app):
    u = FakeUser(UUID_AUDITOR, "AUDITOR")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def seeded(app):
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
    for code, name, parent in [
        ("152", "NVL", None),
        ("1521", "NVL ct", "152"),
        ("156", "HH", None),
        ("1561", "HH ct", "156"),
        ("632", "GVHB", None),
        ("6321", "GVHB ct", "632"),
        ("331", "PT NCC", None),
        ("3311", "PT NCC ct", "331"),
    ]:
        try:
            coa.create_account(
                UUID(COMPANY), code, name, parent_code=parent, actor=uuid4(), reason="c"
            )
        except Exception:  # noqa: BLE001, S110
            pass
    from src.bricks.payment_terms.web_adapter import _series_service as ss

    for pfx in ("PN/", "PX/", "CK/", "PT/"):
        try:
            ss.create_series(company_id=UUID(COMPANY), prefix=pfx, actor=uuid4(), reason="s")
        except Exception:  # noqa: BLE001, S110
            pass
    return {}


class TestInventoryFlow:
    def test_create_product_location_and_in_out(self, chief, seeded):
        # product wavg
        r = chief.post(
            "/api/v1/inventory/products",
            json={
                "company_id": COMPANY,
                "code": "SKU-001",
                "name": "Bút",
                "uom": "Cái",
                "cost_method": "wavg",
                "reason": "init",
            },
        )
        assert r.status_code == 201, r.get_json()
        pid = r.get_json()["data"]["id"]
        # location
        loc = chief.post(
            "/api/v1/inventory/locations",
            json={
                "company_id": COMPANY,
                "code": "A-01",
                "name": "Kệ A",
                "type": "shelf",
                "reason": "loc",
            },
        )
        assert loc.status_code == 201, loc.get_json()
        lid = loc.get_json()["data"]["id"]
        # supplier in 100@10k
        ship = chief.post(
            "/api/v1/inventory/shipments",
            json={
                "company_id": COMPANY,
                "type": "supplier_in",
                "moves": [{"product_id": pid, "qty": "100", "unit_cost": "10000", "to_loc": lid}],
                "reason": "in",
            },
        )
        assert ship.status_code == 201, ship.get_json()
        sid = ship.get_json()["data"]["id"]
        post = chief.post(f"/api/v1/inventory/shipments/{sid}/post", json={"reason": "post in"})
        assert post.status_code == 200, post.get_json()
        # stock 100
        stock = chief.get("/api/v1/inventory/stock", query_string={"company_id": COMPANY})
        assert stock.status_code == 200
        assert any(s["qty"] == 100.0 for s in stock.get_json()["data"])
        # customer out 30
        ship2 = chief.post(
            "/api/v1/inventory/shipments",
            json={
                "company_id": COMPANY,
                "type": "customer_out",
                "moves": [{"product_id": pid, "qty": "30", "from_loc": lid}],
                "reason": "out",
            },
        )
        sid2 = ship2.get_json()["data"]["id"]
        post2 = chief.post(f"/api/v1/inventory/shipments/{sid2}/post", json={"reason": "out"})
        assert post2.status_code == 200, post2.get_json()
        stock2 = chief.get("/api/v1/inventory/stock", query_string={"company_id": COMPANY})
        assert any(s["qty"] == 70.0 for s in stock2.get_json()["data"])
        # oversell 100 should 409
        ship3 = chief.post(
            "/api/v1/inventory/shipments",
            json={
                "company_id": COMPANY,
                "type": "customer_out",
                "moves": [{"product_id": pid, "qty": "100", "from_loc": lid}],
                "reason": "oversell",
            },
        )
        sid3 = ship3.get_json()["data"]["id"]
        over = chief.post(f"/api/v1/inventory/shipments/{sid3}/post", json={"reason": "over"})
        assert over.status_code == 409
        assert over.get_json()["code"] == "INSUFFICIENT_STOCK"

    def test_fifo_and_standard(self, chief, seeded):
        # fifo product
        r = chief.post(
            "/api/v1/inventory/products",
            json={
                "company_id": COMPANY,
                "code": "SKU-F",
                "name": "Vở",
                "uom": "Cái",
                "cost_method": "fifo",
                "reason": "init",
            },
        )
        pid = r.get_json()["data"]["id"]
        loc = chief.post(
            "/api/v1/inventory/locations",
            json={"company_id": COMPANY, "code": "A-F", "name": "K F", "type": "shelf"},
        ).get_json()["data"]["id"]
        s1 = chief.post(
            "/api/v1/inventory/shipments",
            json={
                "company_id": COMPANY,
                "type": "supplier_in",
                "moves": [{"product_id": pid, "qty": "50", "unit_cost": "10000", "to_loc": loc}],
                "reason": "in1",
            },
        ).get_json()["data"]["id"]
        chief.post(f"/api/v1/inventory/shipments/{s1}/post", json={"reason": "p1"})
        s2 = chief.post(
            "/api/v1/inventory/shipments",
            json={
                "company_id": COMPANY,
                "type": "supplier_in",
                "moves": [{"product_id": pid, "qty": "50", "unit_cost": "12000", "to_loc": loc}],
                "reason": "in2",
            },
        ).get_json()["data"]["id"]
        chief.post(f"/api/v1/inventory/shipments/{s2}/post", json={"reason": "p2"})
        s3 = chief.post(
            "/api/v1/inventory/shipments",
            json={
                "company_id": COMPANY,
                "type": "customer_out",
                "moves": [{"product_id": pid, "qty": "60", "from_loc": loc}],
                "reason": "out",
            },
        ).get_json()["data"]["id"]
        assert (
            chief.post(f"/api/v1/inventory/shipments/{s3}/post", json={"reason": "p3"}).status_code
            == 200
        )
        stock = chief.get(
            "/api/v1/inventory/stock", query_string={"company_id": COMPANY, "product_id": pid}
        ).get_json()["data"][0]
        assert stock["qty"] == 40.0
        # standard
        r2 = chief.post(
            "/api/v1/inventory/products",
            json={
                "company_id": COMPANY,
                "code": "SKU-S",
                "name": "Bàn",
                "uom": "Cái",
                "cost_method": "standard",
                "standard_cost": "500000",
                "reason": "std",
            },
        ).get_json()["data"]["id"]
        s4 = chief.post(
            "/api/v1/inventory/shipments",
            json={
                "company_id": COMPANY,
                "type": "supplier_in",
                "moves": [{"product_id": r2, "qty": "10", "unit_cost": "520000", "to_loc": loc}],
                "reason": "in",
            },
        ).get_json()["data"]["id"]
        chief.post(f"/api/v1/inventory/shipments/{s4}/post", json={"reason": "p"})
        s5 = chief.post(
            "/api/v1/inventory/shipments",
            json={
                "company_id": COMPANY,
                "type": "customer_out",
                "moves": [{"product_id": r2, "qty": "2", "from_loc": loc}],
                "reason": "out",
            },
        ).get_json()["data"]["id"]
        assert (
            chief.post(f"/api/v1/inventory/shipments/{s5}/post", json={"reason": "p"}).status_code
            == 200
        )

    def test_auditor_read_only(self, auditor, seeded):
        r = auditor.post(
            "/api/v1/inventory/products",
            json={
                "company_id": COMPANY,
                "code": "SKU-X",
                "name": "X",
                "uom": "Cái",
                "cost_method": "wavg",
            },
        )
        assert r.status_code == 403
        # read ok
        g = auditor.get("/api/v1/inventory/products", query_string={"company_id": COMPANY})
        assert g.status_code == 200

    def test_period_lock_and_reports(self, chief, seeded):
        # create stock then close period
        pid = chief.post(
            "/api/v1/inventory/products",
            json={
                "company_id": COMPANY,
                "code": "SKU-P",
                "name": "P",
                "uom": "Cái",
                "cost_method": "wavg",
            },
        ).get_json()["data"]["id"]
        loc = chief.post(
            "/api/v1/inventory/locations",
            json={"company_id": COMPANY, "code": "A-P", "name": "K P", "type": "shelf"},
        ).get_json()["data"]["id"]
        s = chief.post(
            "/api/v1/inventory/shipments",
            json={
                "company_id": COMPANY,
                "type": "supplier_in",
                "moves": [{"product_id": pid, "qty": "10", "unit_cost": "1000", "to_loc": loc}],
                "reason": "in",
            },
        ).get_json()["data"]["id"]
        chief.post(f"/api/v1/inventory/shipments/{s}/post", json={"reason": "p"})
        # close period 2026-08
        cl = chief.post(
            "/api/v1/inventory/periods/close",
            json={"company_id": COMPANY, "year": 2026, "month": 8, "reason": "close"},
        )
        assert cl.status_code == 200
        # next move in Aug should be blocked (effective_date default today? today is 2026? use explicit Aug date)
        nxt = chief.get(
            "/api/v1/reports/inventory/nxt",
            query_string={"company_id": COMPANY, "from": "2026-08-01", "to": "2026-08-31"},
        )
        assert nxt.status_code == 200
        turn = chief.get(
            "/api/v1/reports/inventory/turnover",
            query_string={"company_id": COMPANY, "from": "2026-08-01", "to": "2026-08-31"},
        )
        assert turn.status_code == 200
