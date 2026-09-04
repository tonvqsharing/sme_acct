"""Integration — slice 3 TaxCode + Lot + PriceList."""

from __future__ import annotations

from uuid import UUID, uuid4

from tests.integration.conftest import UUID_CHIEF, FakeUser, _store

COMPANY = "AAAAaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _chief(app):
    u = FakeUser(UUID_CHIEF, "CHIEF_ACCOUNTANT")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


def test_tax_code_crud(app):
    chief = _chief(app)
    r = chief.post(
        "/api/v1/tax-codes",
        json={
            "company_id": COMPANY,
            "code": "VAT-10",
            "rate": 10,
            "type": "output",
            "account_code": "3331",
        },
    )
    assert r.status_code == 201, r.get_json()
    dup = chief.post(
        "/api/v1/tax-codes",
        json={
            "company_id": COMPANY,
            "code": "VAT-10",
            "rate": 10,
            "type": "output",
            "account_code": "3331",
        },
    )
    assert dup.status_code == 422
    lst = chief.get("/api/v1/tax-codes", query_string={"company_id": COMPANY})
    assert len(lst.get_json()["data"]) == 1


def test_lot_and_price_crud(app):
    chief = _chief(app)
    # need product for lot/price — seed FY + COA + series like inventory flow
    from datetime import date as _d

    app.fy_service.create_year(
        UUID(COMPANY),
        "2026",
        _d(2026, 1, 1),
        _d(2026, 12, 31),
        "MONTHLY",
        actor=uuid4(),
        reason="fy",
    )
    coa = app.coa_service
    for code, name, parent in [
        ("152", "NVL", None),
        ("1521", "NVL ct", "152"),
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
    # product
    prod = chief.post(
        "/api/v1/inventory/products",
        json={
            "company_id": COMPANY,
            "code": "SKU-LOT",
            "name": "Hàng lô",
            "uom": "Cái",
            "cost_method": "specific",
        },
    ).get_json()["data"]["id"]
    # lot
    lot = chief.post(
        "/api/v1/inventory/lots",
        json={"company_id": COMPANY, "product_id": prod, "lot_code": "LOT-001", "qty": "100"},
    )
    assert lot.status_code == 201, lot.get_json()
    lst = chief.get(
        "/api/v1/inventory/lots", query_string={"company_id": COMPANY, "product_id": prod}
    )
    assert len(lst.get_json()["data"]) == 1
    # price
    price = chief.post(
        "/api/v1/inventory/price-lists",
        json={
            "company_id": COMPANY,
            "product_id": prod,
            "price": "50000",
            "valid_from": "2026-08-10",
        },
    )
    assert price.status_code == 201, price.get_json()
    lst2 = chief.get(
        "/api/v1/inventory/price-lists", query_string={"company_id": COMPANY, "product_id": prod}
    )
    assert len(lst2.get_json()["data"]) == 1
    # shipment with lot_id
    loc = chief.post(
        "/api/v1/inventory/locations",
        json={"company_id": COMPANY, "code": "A-LOT", "name": "Kệ lot"},
    ).get_json()["data"]["id"]
    lot_id = lot.get_json()["data"]["id"]
    ship = chief.post(
        "/api/v1/inventory/shipments",
        json={
            "company_id": COMPANY,
            "type": "supplier_in",
            "moves": [
                {
                    "product_id": prod,
                    "qty": "10",
                    "unit_cost": "50000",
                    "to_loc": loc,
                    "lot_id": lot_id,
                }
            ],
        },
    )
    assert ship.status_code == 201, ship.get_json()
