"""Unit + behavior tests for audit_log brick (service w/ fake repo)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.audit_log.services import (
    AuditEvent,
    AuditLogService,
)
from tests.unit.audit_log.fake_repo import FakeAuditRepo

ACTOR = uuid4()
ENTITY = uuid4()


def _append(svc, **kw):
    return svc.append(
        entity_type=kw.get("entity_type", "payment_term"),
        entity_id=kw.get("entity_id", ENTITY),
        action=kw.get("action", "CREATE"),
        actor_id=kw.get("actor_id", ACTOR),
        reason=kw.get("reason", "r"),
        field_name=kw.get("field_name"),
        before_value=kw.get("before_value"),
        after_value=kw.get("after_value"),
    )


class TestAppend:
    def test_event_gets_64_hex_checksum(self):
        svc = AuditLogService(FakeAuditRepo())
        ev = _append(svc)
        assert len(ev.checksum) == 64
        int(ev.checksum, 16)  # hex parse sanity

    def test_first_event_chains_from_genesis(self):
        from src.bricks.audit_log.domain import GENESIS_CHECKSUM

        svc = AuditLogService(FakeAuditRepo())
        ev = _append(svc)
        assert ev.prev_checksum == GENESIS_CHECKSUM

    def test_second_event_chains_from_first(self):
        repo = FakeAuditRepo()
        svc = AuditLogService(repo)
        e1 = _append(svc, action="CREATE")
        e2 = _append(svc, action="UPDATE", reason="second")
        assert e2.prev_checksum == e1.checksum

    @pytest.mark.parametrize("missing", ["entity_type", "entity_id", "action", "actor_id"])
    def test_required_fields_enforced(self, missing):
        svc = AuditLogService(FakeAuditRepo())
        kwargs = {
            "entity_type": "t",
            "entity_id": ENTITY,
            "action": "CREATE",
            "actor_id": ACTOR,
            "reason": "r",
        }
        kwargs[missing] = None
        with pytest.raises(ValueError, match=missing):
            svc.append(**kwargs)

    def test_before_after_json_round_trip(self):
        svc = AuditLogService(FakeAuditRepo())
        ev = _append(
            svc,
            action="UPDATE",
            before_value={"due_days": 30},
            after_value={"due_days": 45},
        )
        assert ev.before_value == {"due_days": 30}
        assert ev.after_value == {"due_days": 45}


class TestVerifyChain:
    def test_single_event_chain_valid(self):
        svc = AuditLogService(FakeAuditRepo())
        _append(svc)
        assert svc.verify_chain("payment_term", ENTITY) is True

    def test_multi_event_chain_valid(self):
        svc = AuditLogService(FakeAuditRepo())
        for act in ("CREATE", "UPDATE", "DEACTIVATE"):
            _append(svc, action=act, reason=act.lower())
        assert svc.verify_chain("payment_term", ENTITY) is True

    def test_tampered_action_breaks_chain(self):
        repo = FakeAuditRepo()
        svc = AuditLogService(repo)
        _append(svc, action="CREATE")
        _append(svc, action="UPDATE", reason="x")
        # Simulate raw-DB tampering, bypassing domain immutability
        object.__setattr__(repo.events[-1], "action", "TAMPERED")
        assert svc.verify_chain("payment_term", ENTITY) is False

    def test_tampered_prev_link_breaks_chain(self):
        repo = FakeAuditRepo()
        svc = AuditLogService(repo)
        _append(svc, action="CREATE")
        _append(svc, action="UPDATE")
        object.__setattr__(repo.events[-1], "prev_checksum", "f" * 64)
        assert svc.verify_chain("payment_term", ENTITY) is False

    def test_unknown_entity_is_valid_empty_chain(self):
        svc = AuditLogService(FakeAuditRepo())
        assert svc.verify_chain("ghost", uuid4()) is True


class TestRetrieval:
    def test_filter_by_entity(self):
        svc = AuditLogService(FakeAuditRepo())
        other = uuid4()
        _append(svc)
        _append(svc, entity_id=other)
        got = svc.get_by_entity("payment_term", ENTITY)
        assert len(got) == 1 and isinstance(got[0], AuditEvent)

    def test_immutability_no_update_delete_on_port(self):
        from src.bricks.audit_log.contract import AuditLogPort

        assert not hasattr(AuditLogPort, "update")
        assert not hasattr(AuditLogPort, "delete")
