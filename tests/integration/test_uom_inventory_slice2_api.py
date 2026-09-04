"""Integration — slice 2 UOM + Category + Warehouse."""

from __future__ import annotations

from tests.integration.conftest import UUID_CHIEF, FakeUser, _store

COMPANY = "99999999-9999-9999-9999-999999999999"


def _chief(app):
    u = FakeUser(UUID_CHIEF, "CHIEF_ACCOUNTANT")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


def test_uom_crud(app):
    chief = _chief(app)
    r = chief.post(
        "/api/v1/uoms", json={"company_id": COMPANY, "code": "Cai", "name": "Cái", "factor": "1"}
    )
    assert r.status_code == 201, r.get_json()
    # duplicate 409
    dup = chief.post("/api/v1/uoms", json={"company_id": COMPANY, "code": "Cai", "name": "Cái 2"})
    assert dup.status_code == 409
    # base uom Hop 10 Cai
    base_id = r.get_json()["data"]["id"]
    hop = chief.post(
        "/api/v1/uoms",
        json={
            "company_id": COMPANY,
            "code": "Hop",
            "name": "Hộp 10 cái",
            "factor": "10",
            "base_uom_id": base_id,
        },
    )
    assert hop.status_code == 201
    lst = chief.get("/api/v1/uoms", query_string={"company_id": COMPANY})
    assert len(lst.get_json()["data"]) == 2


def test_category_and_warehouse(app):
    chief = _chief(app)
    cat = chief.post(
        "/api/v1/inventory/categories",
        json={
            "company_id": COMPANY,
            "code": "CAT-001",
            "name": "Vật liệu",
            "cost_method": "wavg",
            "account_code": "1521",
            "tax_category": "manufacturing",
        },
    )
    assert cat.status_code == 201, cat.get_json()
    lst = chief.get("/api/v1/inventory/categories", query_string={"company_id": COMPANY})
    assert len(lst.get_json()["data"]) == 1
    wh = chief.post(
        "/api/v1/inventory/warehouses",
        json={"company_id": COMPANY, "code": "KHO-A", "name": "Kho A", "address": "Hà Nội"},
    )
    assert wh.status_code == 201, wh.get_json()
    lst2 = chief.get("/api/v1/inventory/warehouses", query_string={"company_id": COMPANY})
    assert len(lst2.get_json()["data"]) == 1
    # create location linked to warehouse
    wid = wh.get_json()["data"]["id"]
    loc = chief.post(
        "/api/v1/inventory/locations",
        json={
            "company_id": COMPANY,
            "code": "A-01",
            "name": "Kệ A",
            "type": "shelf",
            "warehouse_id": wid,
        },
    )
    assert loc.status_code == 201


def test_product_with_new_masters(app):
    chief = _chief(app)
    # create UOM and category first
    chief.post("/api/v1/uoms", json={"company_id": COMPANY, "code": "Cai2", "name": "Cái2"})
    chief.post(
        "/api/v1/inventory/categories",
        json={"company_id": COMPANY, "code": "CAT-002", "name": "Hàng hóa"},
    )
    # product still uses old free text uom, but should still work (FK next slice)
    prod = chief.post(
        "/api/v1/inventory/products",
        json={
            "company_id": COMPANY,
            "code": "SKU-NEW",
            "name": "Bút mới",
            "uom": "Cái2",
            "cost_method": "wavg",
        },
    )
    assert prod.status_code == 201


def test_product_links_uom_and_category_ids(app):
    chief = _chief(app)
    uom_id = chief.post(
        "/api/v1/uoms", json={"company_id": COMPANY, "code": "CaiLink", "name": "Cái link"}
    ).get_json()["data"]["id"]
    cat_id = chief.post(
        "/api/v1/inventory/categories",
        json={"company_id": COMPANY, "code": "CAT-LINK", "name": "Link cat"},
    ).get_json()["data"]["id"]
    prod = chief.post(
        "/api/v1/inventory/products",
        json={
            "company_id": COMPANY,
            "code": "SKU-LINK",
            "name": "Bút link",
            "uom": "Cái link",
            "uom_id": uom_id,
            "category_id": cat_id,
            "cost_method": "wavg",
        },
    )
    assert prod.status_code == 201, prod.get_json()
    data = prod.get_json()["data"]
    assert data["uom_id"] == uom_id
    assert data["category_id"] == cat_id
