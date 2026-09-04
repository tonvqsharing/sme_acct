"""Integration — party via real factory. MST + SOD + RBAC."""

from __future__ import annotations

from tests.integration.conftest import UUID_AUDITOR, UUID_CHIEF, FakeUser, _store

COMPANY = "88888888-8888-8888-8888-888888888888"


def _chief(app):
    u = FakeUser(UUID_CHIEF, "CHIEF_ACCOUNTANT")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


def _auditor(app):
    u = FakeUser(UUID_AUDITOR, "AUDITOR")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


def test_create_and_list_party(app):
    chief = _chief(app)
    r = chief.post(
        "/api/v1/parties",
        json={
            "company_id": COMPANY,
            "code": "KH-001",
            "name": "Cty A",
            "mst": "0101234567",
            "is_customer": True,
        },
    )
    assert r.status_code == 201, r.get_json()
    assert r.get_json()["data"]["mst"] == "0101234567"
    # duplicate code 409
    dup = chief.post(
        "/api/v1/parties",
        json={"company_id": COMPANY, "code": "KH-001", "name": "B", "is_customer": True},
    )
    assert dup.status_code == 409
    # duplicate mst 409
    dup_mst = chief.post(
        "/api/v1/parties",
        json={
            "company_id": COMPANY,
            "code": "KH-002",
            "name": "B",
            "mst": "0101234567",
            "is_customer": True,
        },
    )
    assert dup_mst.status_code == 409
    # list customer
    lst = chief.get("/api/v1/parties", query_string={"company_id": COMPANY, "role": "customer"})
    assert lst.status_code == 200
    assert len(lst.get_json()["data"]) == 1


def test_auditor_cannot_create(app):
    chief = _chief(app)
    auditor = _auditor(app)
    # chief creates one to ensure list works
    chief.post(
        "/api/v1/parties",
        json={"company_id": COMPANY, "code": "NCC-001", "name": "NCC", "is_supplier": True},
    )
    r = auditor.post(
        "/api/v1/parties",
        json={"company_id": COMPANY, "code": "KH-002", "name": "B", "is_customer": True},
    )
    assert r.status_code == 403
    # auditor can read
    g = auditor.get("/api/v1/parties", query_string={"company_id": COMPANY})
    assert g.status_code == 200


def test_invalid_mst_422(app):
    chief = _chief(app)
    r = chief.post(
        "/api/v1/parties",
        json={
            "company_id": COMPANY,
            "code": "KH-003",
            "name": "B",
            "mst": "0000000000",
            "is_customer": True,
        },
    )
    assert r.status_code == 422


def test_department_crud(app):
    chief = _chief(app)
    r = chief.post(
        "/api/v1/departments", json={"company_id": COMPANY, "code": "PB-KT", "name": "Kế toán"}
    )
    assert r.status_code == 201, r.get_json()
    lst = chief.get("/api/v1/departments", query_string={"company_id": COMPANY})
    assert lst.status_code == 200
    assert len(lst.get_json()["data"]) == 1
