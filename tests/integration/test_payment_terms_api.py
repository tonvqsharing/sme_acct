"""API contract tests for payment_terms brick via real create_app()."""

from __future__ import annotations

from uuid import uuid4

from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    UUID_ADMIN,
    UUID_AUDITOR,
    UUID_CHIEF,
)

COMPANY = str(uuid4())
TERM_BODY = {
    "company_id": COMPANY,
    "name": "Net 30",
    "due_days": 30,
    "interest_rate": 0,
    "actor": UUID_ADMIN,
    "reason": "init setup",
}


# ═══ Payment Terms API ════════════════════════════════════════════════════


class TestPaymentTermAuthAndRoles:
    def test_unauthenticated_list_401(self, app):
        resp = app.test_client().get("/api/v1/payment-terms")
        assert resp.status_code == 401

    def test_unauthenticated_create_401(self, app):
        resp = app.test_client().post("/api/v1/payment-terms", json=TERM_BODY)
        assert resp.status_code == 401

    def test_auditor_read_allowed(self, auditor_client, admin_client):
        admin_client.post("/api/v1/payment-terms", json=TERM_BODY)
        resp = auditor_client.get("/api/v1/payment-terms", query_string={"company_id": COMPANY})
        assert resp.status_code == 200

    def test_auditor_write_blocked_EX007(self, auditor_client):
        """EX-007: AUDITOR read-only."""
        resp = auditor_client.post("/api/v1/payment-terms", json=TERM_BODY)
        assert resp.status_code == 403
        assert resp.get_json()["code"] == "AUDITOR_READ_ONLY"

    def test_accountant_can_create(self, accountant_client):
        resp = accountant_client.post("/api/v1/payment-terms", json=TERM_BODY)
        assert resp.status_code == 201

    def test_set_default_requires_chief_or_admin(self, admin_client, accountant_client):
        """DEFAULT_ROLES excludes ACCOUNTANT (SOD R-011)."""
        created = admin_client.post("/api/v1/payment-terms", json=TERM_BODY).get_json()["data"]
        tid = created["id"]

        resp = accountant_client.post(
            f"/api/v1/payment-terms/{tid}/set-default",
            json={"actor": UUID_ACCOUNTANT, "reason": "try"},
        )
        assert resp.status_code == 403


class TestPaymentTermContract:
    def test_create_returns_201_with_serialized_data(self, admin_client):
        resp = admin_client.post("/api/v1/payment-terms", json=TERM_BODY)
        assert resp.status_code == 201
        data = resp.get_json()["data"]
        assert data["name"] == "Net 30"
        assert data["due_days"] == 30
        assert data["status"] == "active"
        assert len(data["checksum"]) == 64  # R-010 stamped

    def test_duplicate_name_409_with_EX002_code(self, admin_client):
        admin_client.post("/api/v1/payment-terms", json=TERM_BODY)
        dup = {**TERM_BODY, "due_days": 45}
        resp = admin_client.post("/api/v1/payment-terms", json=dup)
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "DUPLICATE_PAYMENT_TERM"

    def test_missing_actor_400_with_EX001_code(self, admin_client):
        bad = {k: v for k, v in TERM_BODY.items() if k != "actor"}
        resp = admin_client.post("/api/v1/payment-terms", json=bad)
        assert resp.status_code == 400
        assert resp.get_json()["code"] == "MISSING_ACTOR"

    def test_missing_reason_400_R004(self, admin_client):
        bad = {**TERM_BODY, "reason": ""}
        resp = admin_client.post("/api/v1/payment-terms", json=bad)
        assert resp.status_code == 400

    def test_get_unknown_404(self, admin_client):
        resp = admin_client.get(f"/api/v1/payment-terms/{uuid4()}")
        assert resp.status_code == 404

    def test_second_default_409_with_EX003_code(self, admin_client):
        first = admin_client.post("/api/v1/payment-terms", json=TERM_BODY).get_json()["data"]
        # Establish the first default via its SOD route
        set_resp = admin_client.post(
            f"/api/v1/payment-terms/{first['id']}/set-default",
            json={"actor": UUID_ADMIN, "reason": "initial default"},
        )
        assert set_resp.status_code == 200

        second_body = {
            **TERM_BODY,
            "name": "Net 15",
            "due_days": 15,
            "is_default": True,
        }
        second_resp = admin_client.post("/api/v1/payment-terms", json=second_body)
        # Creation of a default while one exists → EX-003 at create too
        assert second_resp.status_code == 409
        assert second_resp.get_json()["code"] == "DEFAULT_ALREADY_EXISTS"

    def test_full_flow_HP002_sod(self, chief_client, accountant_client):
        """HP-002: chief requests, accountant approves, default applied."""
        created = chief_client.post(
            "/api/v1/payment-terms", json={**TERM_BODY, "actor": UUID_CHIEF}
        )
        assert created.status_code == 201
        tid = created.get_json()["data"]["id"]

        req_resp = chief_client.post(
            f"/api/v1/approval-requests/set-default/{tid}",
            json={"actor": UUID_CHIEF, "reason": "company standard"},
        )
        assert req_resp.status_code == 202
        req_id = req_resp.get_json()["data"]["id"]
        assert req_resp.get_json()["data"]["status"] == "PENDING"

        # SOD: chief cannot self-approve
        self_resp = chief_client.post(
            f"/api/v1/approval-requests/{req_id}/approve",
            json={"actor": UUID_CHIEF, "reason": "self"},
        )
        assert self_resp.status_code == 403
        assert self_resp.get_json()["code"] == "SOD_VIOLATION"

        resp = accountant_client.post(
            f"/api/v1/approval-requests/{req_id}/approve",
            json={"actor": UUID_ACCOUNTANT, "reason": "reviewed ok"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "APPROVED"
        assert resp.get_json()["data"]["applied"]["is_default"] is True

        detail = chief_client.get(f"/api/v1/payment-terms/{tid}")
        assert detail.get_json()["data"]["is_default"] is True


# ═══ Document Numbering API ═══════════════════════════════════════════════


SERIES_BODY = {
    "company_id": COMPANY,
    "prefix": "HD/",
    "actor": UUID_CHIEF,
    "reason": "e-invoice series",
}


class TestSeriesAuthAndRoles:
    def test_unauthenticated_increment_401(self, app):
        resp = app.test_client().post(f"/api/v1/document-numbering/{uuid4()}/increment")
        assert resp.status_code == 401

    def test_auditor_cannot_increment(self, auditor_client, chief_client):
        series = chief_client.post("/api/v1/document-numbering", json=SERIES_BODY).get_json()[
            "data"
        ]
        resp = auditor_client.post(
            f"/api/v1/document-numbering/{series['id']}/increment",
            json={"actor": UUID_AUDITOR, "reason": "peek"},
        )
        assert resp.status_code == 403
        assert resp.get_json()["code"] == "AUDITOR_READ_ONLY"


class TestSeriesContract:
    def test_create_valid_prefix_201_next_sequence_one(self, chief_client):
        """HP-003."""
        resp = chief_client.post("/api/v1/document-numbering", json=SERIES_BODY)
        assert resp.status_code == 201
        data = resp.get_json()["data"]
        assert data["prefix"] == "HD/"
        assert data["next_sequence"] == 1

    def test_invalid_prefix_422_with_EX004_code(self, chief_client):
        bad = {**SERIES_BODY, "prefix": "not-valid"}
        resp = chief_client.post("/api/v1/document-numbering", json=bad)
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "INVALID_SERIES_PREFIX"

    def test_duplicate_prefix_409_AP002(self, chief_client):
        chief_client.post("/api/v1/document-numbering", json=SERIES_BODY)
        resp = chief_client.post("/api/v1/document-numbering", json=SERIES_BODY)
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "PREFIX_ALREADY_EXISTS"

    def test_increment_returns_sequence_and_persists_HP004(self, chief_client):
        """HP-004: sequence issued then persisted."""
        series = chief_client.post("/api/v1/document-numbering", json=SERIES_BODY).get_json()[
            "data"
        ]
        sid = series["id"]

        resp = chief_client.post(
            f"/api/v1/document-numbering/{sid}/increment",
            json={"actor": UUID_CHIEF, "reason": "invoice HD/000001"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["sequence_used"] == 1
        assert resp.get_json()["data"]["document_number"] == "HD/000001"

        detail = chief_client.get(f"/api/v1/document-numbering/{sid}")
        assert detail.get_json()["data"]["next_sequence"] == 2

    def test_increment_inactive_series_409_EX008(self, chief_client):
        sid = chief_client.post("/api/v1/document-numbering", json=SERIES_BODY).get_json()["data"][
            "id"
        ]
        chief_client.post(
            f"/api/v1/document-numbering/{sid}/deactivate",
            json={"actor": UUID_CHIEF, "reason": "pause"},
        )
        resp = chief_client.post(
            f"/api/v1/document-numbering/{sid}/increment",
            json={"actor": UUID_CHIEF, "reason": "invoice"},
        )
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "SERIES_INACTIVE"

    def test_activate_after_deactivate_round_trip(self, chief_client):
        sid = chief_client.post(
            "/api/v1/document-numbering",
            json={**SERIES_BODY, "prefix": "PN/"},
        ).get_json()["data"]["id"]
        chief_client.post(
            f"/api/v1/document-numbering/{sid}/deactivate",
            json={"actor": UUID_CHIEF, "reason": "pause"},
        )
        resp = chief_client.post(
            f"/api/v1/document-numbering/{sid}/activate",
            json={"actor": UUID_CHIEF, "reason": "resume"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["is_active"] is True
