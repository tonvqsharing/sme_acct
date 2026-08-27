"""XML ingest API — integration tests through real create_app()."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from uuid import uuid4

import pytest

from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    FakeUser,
    _store,
)

COMPANY = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _client(app, uid: str, role: str):
    u = FakeUser(uid, role)
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def accountant(app):
    return _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")


@pytest.fixture()
def seeded(app):
    """Create fiscal year and COA for tests (same pattern as test_purchases_api)."""
    app.fy_service.create_year(
        COMPANY,
        "2026",
        date(2026, 1, 1),
        date(2026, 12, 31),
        "MONTHLY",
        actor=uuid4(),
        reason="fy",
    )
    coa = app.coa_service
    coa.create_account(COMPANY, "642", "Chi QLDN", actor=uuid4(), reason="c")
    coa.create_account(
        COMPANY,
        "6421",
        "Chi VP",
        parent_code="642",
        actor=uuid4(),
        reason="c",
    )


GOOD_XML = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n'
    b"<DLHDon>\n"
    b"  <HDon>\n"
    b"    <SHDon>00009876</SHDon>\n"
    b"    <KHMSHDon>AA</KHMSHDon>\n"
    b"    <KMHHDON>1</KMHHDON>\n"
    b"    <NLap>2026-08-15</NLap>\n"
    b"    <NBan>\n"
    b"      <Ten>CTCP Hao Binh</Ten>\n"
    b"      <MST>0101234567</MST>\n"
    b"    </NBan>\n"
    b"    <NMua>\n"
    b"      <Ten>Test XML Ingest Co</Ten>\n"
    b"      <MST>0123456789</MST>\n"
    b"    </NMua>\n"
    b"    <HHDVu>\n"
    b"      <HH>\n"
    b"        <Ten>Giay A4</Ten>\n"
    b"        <DVTinh>rei</DVTinh>\n"
    b"        <SLuong>10</SLuong>\n"
    b"        <DGia>50000</DGia>\n"
    b"        <ThTien>500000</ThTien>\n"
    b"        <TSuat>10</TSuat>\n"
    b"      </HH>\n"
    b"    </HHDVu>\n"
    b"    <TongCong>550000</TongCong>\n"
    b"  </HDon>\n"
    b"</DLHDon>\n"
)


# ─── Single ingest ──────────────────────────────────────────────────────


class TestIngestSingleAPI:
    def test_upload_success(self, seeded, accountant):
        data = {
            "file": (BytesIO(GOOD_XML), "invoice.xml"),
            "company_id": COMPANY,
            "default_expense_account": "6421",
            "entry_date": "2026-08-20",
            "reason": "integration test",
        }
        resp = accountant.post(
            "/api/v1/xml-ingest/single",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["invoice_number"] == "00009876"
        assert body["data"]["supplier_name"] == "CTCP Hao Binh"
        assert body["data"]["supplier_mst"] == "0101234567"

    def test_upload_no_file(self, seeded, accountant):
        resp = accountant.post(
            "/api/v1/xml-ingest/single",
            data={"company_id": COMPANY},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "NO_FILE"

    def test_upload_no_company_id(self, seeded, accountant):
        data = {"file": (BytesIO(GOOD_XML), "invoice.xml")}
        resp = accountant.post(
            "/api/v1/xml-ingest/single",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "MISSING_COMPANY_ID"

    def test_upload_malformed_xml(self, seeded, accountant):
        data = {
            "file": (BytesIO(b"<not valid xml"), "bad.xml"),
            "company_id": COMPANY,
            "reason": "test",
        }
        resp = accountant.post(
            "/api/v1/xml-ingest/single",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 422
        assert resp.get_json()["success"] is False

    def test_unauthenticated(self, app):
        resp = app.test_client().post("/api/v1/xml-ingest/single")
        assert resp.status_code == 401


# ─── Batch ingest ───────────────────────────────────────────────────────


GOOD_XML_2 = GOOD_XML.replace(b"00009876", b"00009877")


class TestIngestBatchAPI:
    def test_batch_upload_success(self, seeded, accountant):
        data = {
            "files": [
                (BytesIO(GOOD_XML), "inv1.xml"),
                (BytesIO(GOOD_XML_2), "inv2.xml"),
            ],
            "company_id": COMPANY,
            "default_expense_account": "6421",
            "entry_date": "2026-08-20",
            "reason": "batch test",
        }
        resp = accountant.post(
            "/api/v1/xml-ingest/batch",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["total_files"] == 2
        assert body["success_count"] == 2
        assert body["error_count"] == 0

    def test_batch_no_files(self, seeded, accountant):
        resp = accountant.post(
            "/api/v1/xml-ingest/batch",
            data={"company_id": COMPANY},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "NO_FILES"

    def test_batch_no_company_id(self, seeded, accountant):
        data = {"files": (BytesIO(GOOD_XML), "inv.xml")}
        resp = accountant.post(
            "/api/v1/xml-ingest/batch",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 422
