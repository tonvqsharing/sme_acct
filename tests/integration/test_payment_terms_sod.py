"""§11.2 series activation SOD + reject path + audit chain verification."""

from __future__ import annotations

from uuid import UUID

from tests.integration.conftest import UUID_ACCOUNTANT, UUID_CHIEF

SERIES = {
    "company_id": "11111111-1111-1111-1111-111111111111",
    "prefix": "HD/",
    "reason": "setup",
}


class TestSeriesActivationSod:
    def test_request_then_approve_activates(self, chief_client, accountant_client):
        probe = chief_client.post(
            "/api/v1/document-numbering",
            json={**SERIES, "actor": UUID_CHIEF},
        )
        assert probe.status_code == 201, (probe.status_code, probe.get_json())
        sid = probe.get_json()["data"]["id"]
        chief_client.post(
            f"/api/v1/document-numbering/{sid}/deactivate",
            json={"actor": UUID_CHIEF, "reason": "setup"},
        )
        req_id = chief_client.post(
            f"/api/v1/approval-requests/activate-series/{sid}",
            json={"actor": UUID_CHIEF, "reason": "reopen"},
        ).get_json()["data"]["id"]

        resp = accountant_client.post(
            f"/api/v1/approval-requests/{req_id}/approve",
            json={"actor": UUID_ACCOUNTANT, "reason": "ok"},
        )
        assert resp.status_code == 200
        detail = chief_client.get(f"/api/v1/document-numbering/{sid}")
        assert detail.get_json()["data"]["is_active"] is True

    def test_reject_keeps_state_409(self, chief_client, accountant_client):
        tid = chief_client.post(
            "/api/v1/payment-terms",
            json={
                "company_id": SERIES["company_id"],
                "name": "Net 7",
                "due_days": 7,
                "interest_rate": 0,
                "actor": UUID_CHIEF,
                "reason": "x",
            },
        ).get_json()["data"]["id"]
        req_id = chief_client.post(
            f"/api/v1/approval-requests/set-default/{tid}",
            json={"actor": UUID_CHIEF, "reason": "try 7"},
        ).get_json()["data"]["id"]
        resp = accountant_client.post(
            f"/api/v1/approval-requests/{req_id}/reject",
            json={"actor": UUID_ACCOUNTANT, "reason": "too short"},
        )
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "REQUEST_REJECTED"
        assert (
            chief_client.get(f"/api/v1/payment-terms/{tid}").get_json()["data"]["is_default"]
            is False
        )

    def test_double_decide_blocked(self, chief_client, accountant_client):
        tid = chief_client.post(
            "/api/v1/payment-terms",
            json={
                "company_id": SERIES["company_id"],
                "name": "N9",
                "due_days": 9,
                "interest_rate": 0,
                "actor": UUID_CHIEF,
                "reason": "x",
            },
        ).get_json()["data"]["id"]
        rid = chief_client.post(
            f"/api/v1/approval-requests/set-default/{tid}",
            json={"actor": UUID_CHIEF, "reason": "r"},
        ).get_json()["data"]["id"]
        accountant_client.post(
            f"/api/v1/approval-requests/{rid}/approve",
            json={"actor": UUID_ACCOUNTANT, "reason": "a"},
        )
        again = accountant_client.post(
            f"/api/v1/approval-requests/{rid}/approve",
            json={"actor": UUID_ACCOUNTANT, "reason": "again"},
        )
        assert again.status_code == 409

    def test_audit_chain_captures_sod_events(self, chief_client, accountant_client):

        from src.bricks.payment_terms.web_adapter import _approval_service

        tid = chief_client.post(
            "/api/v1/payment-terms",
            json={
                "company_id": SERIES["company_id"],
                "name": "NA",
                "due_days": 5,
                "interest_rate": 0,
                "actor": UUID_CHIEF,
                "reason": "x",
            },
        ).get_json()["data"]["id"]
        rid = chief_client.post(
            f"/api/v1/approval-requests/set-default/{tid}",
            json={"actor": UUID_CHIEF, "reason": "r2"},
        ).get_json()["data"]["id"]
        accountant_client.post(
            f"/api/v1/approval-requests/{rid}/approve",
            json={"actor": UUID_ACCOUNTANT, "reason": "fine"},
        )
        audit = _approval_service._audit
        events = audit.get_by_entity("pt_approval", UUID(rid))
        actions = [e.action for e in events]
        assert actions[0] == "DEFAULT_REQUEST"
        assert "DEFAULT_APPROVE" in actions
        assert audit.verify_chain("pt_approval", UUID(rid)) is True
