"""Integration: audit log API — POST create, GET query, GET verify."""

from __future__ import annotations

from uuid import uuid4


class TestCreateAuditLog:
    def test_post_creates_record(self, accountant_client):
        r = accountant_client.post(
            "/api/v1/audit-log",
            json={
                "entity_type": "company",
                "entity_id": str(uuid4()),
                "action": "CREATE",
                "reason": "New company",
            },
        )
        assert r.status_code == 201
        data = r.get_json()["data"]
        assert data["entity_type"] == "company"
        assert data["action"] == "CREATE"
        assert len(data["checksum"]) == 64

    def test_post_with_custom_actor(self, accountant_client):
        actor = str(uuid4())
        r = accountant_client.post(
            "/api/v1/audit-log",
            json={
                "entity_type": "payment_term",
                "entity_id": str(uuid4()),
                "action": "UPDATE",
                "actor_id": actor,
                "reason": "Changed terms",
                "field_name": "due_days",
                "before_value": {"due_days": 30},
                "after_value": {"due_days": 45},
            },
        )
        assert r.status_code == 201
        data = r.get_json()["data"]
        assert data["field_name"] == "due_days"
        assert data["before_value"] == {"due_days": 30}
        assert data["after_value"] == {"due_days": 45}

    def test_post_missing_field_422(self, accountant_client):
        r = accountant_client.post(
            "/api/v1/audit-log",
            json={"entity_type": "company"},
        )
        assert r.status_code == 422

    def test_post_invalid_entity_id_422(self, accountant_client):
        r = accountant_client.post(
            "/api/v1/audit-log",
            json={
                "entity_type": "company",
                "entity_id": "not-a-uuid",
                "action": "CREATE",
                "reason": "r",
            },
        )
        assert r.status_code == 422

    def test_post_unauthenticated_401(self, app):
        c = app.test_client()
        r = c.post(
            "/api/v1/audit-log",
            json={
                "entity_type": "company",
                "entity_id": str(uuid4()),
                "action": "CREATE",
                "reason": "r",
            },
        )
        assert r.status_code == 401


class TestQueryAuditLog:
    def _seed_events(self, client, n=3):
        ids = [uuid4() for _ in range(n)]
        for eid in ids:
            client.post(
                "/api/v1/audit-log",
                json={
                    "entity_type": "payment_term",
                    "entity_id": str(eid),
                    "action": "CREATE",
                    "reason": "seed",
                },
            )
        return ids

    def test_get_returns_all(self, accountant_client):
        ids = self._seed_events(accountant_client)
        r = accountant_client.get("/api/v1/audit-log")
        assert r.status_code == 200
        body = r.get_json()
        assert body["pagination"]["total"] >= len(ids)
        assert len(body["data"]) >= len(ids)

    def test_get_filter_entity_id(self, accountant_client):
        ids = self._seed_events(accountant_client)
        r = accountant_client.get(f"/api/v1/audit-log?entity_id={ids[0]}")
        assert r.status_code == 200
        body = r.get_json()
        assert body["pagination"]["total"] == 1
        assert body["data"][0]["entity_id"] == str(ids[0])

    def test_get_filter_action(self, accountant_client):
        eid = uuid4()
        accountant_client.post(
            "/api/v1/audit-log",
            json={
                "entity_type": "company",
                "entity_id": str(eid),
                "action": "UPDATE",
                "reason": "update",
            },
        )
        r = accountant_client.get("/api/v1/audit-log?action=UPDATE")
        assert r.status_code == 200
        for ev in r.get_json()["data"]:
            assert ev["action"] == "UPDATE"

    def test_get_pagination(self, accountant_client):
        self._seed_events(accountant_client, n=5)
        r = accountant_client.get("/api/v1/audit-log?page=1&page_size=2")
        body = r.get_json()
        assert len(body["data"]) == 2
        assert body["pagination"]["total"] == 5
        assert body["pagination"]["page"] == 1
        assert body["pagination"]["page_size"] == 2

    def test_get_page2(self, accountant_client):
        self._seed_events(accountant_client, n=5)
        r = accountant_client.get("/api/v1/audit-log?page=2&page_size=2")
        body = r.get_json()
        assert len(body["data"]) == 2  # items 3,4

    def test_get_bad_page_ignores(self, accountant_client):
        self._seed_events(accountant_client, n=3)
        r = accountant_client.get("/api/v1/audit-log?page=abc&page_size=xyz")
        assert r.status_code == 200
        assert r.get_json()["pagination"]["page"] == 1
        assert r.get_json()["pagination"]["page_size"] == 50

    def test_get_invalid_entity_id_422(self, accountant_client):
        r = accountant_client.get("/api/v1/audit-log?entity_id=bad")
        assert r.status_code == 422

    def test_get_unauthenticated_401(self, app):
        c = app.test_client()
        r = c.get("/api/v1/audit-log")
        assert r.status_code == 401


class TestVerifyAuditChain:
    def test_verify_valid_chain(self, accountant_client):
        eid = uuid4()
        for act in ("CREATE", "UPDATE", "DEACTIVATE"):
            accountant_client.post(
                "/api/v1/audit-log",
                json={
                    "entity_type": "payment_term",
                    "entity_id": str(eid),
                    "action": act,
                    "reason": act.lower(),
                },
            )
        r = accountant_client.get(
            f"/api/v1/audit-log/verify?entity_type=payment_term&entity_id={eid}"
        )
        assert r.status_code == 200
        body = r.get_json()["data"]
        assert body["valid"] is True
        assert body["checked_records"] == 3
        assert len(body["root_hash"]) == 64

    def test_verify_empty_entity(self, accountant_client):
        eid = uuid4()
        r = accountant_client.get(f"/api/v1/audit-log/verify?entity_type=ghost&entity_id={eid}")
        assert r.status_code == 200
        assert r.get_json()["data"]["valid"] is True
        assert r.get_json()["data"]["checked_records"] == 0

    def test_verify_missing_params_422(self, accountant_client):
        r = accountant_client.get("/api/v1/audit-log/verify")
        assert r.status_code == 422

    def test_verify_invalid_entity_id_422(self, accountant_client):
        r = accountant_client.get("/api/v1/audit-log/verify?entity_type=t&entity_id=bad")
        assert r.status_code == 422

    def test_verify_unauthenticated_401(self, app):
        c = app.test_client()
        r = c.get("/api/v1/audit-log/verify?entity_type=t&entity_id=1")
        assert r.status_code == 401
