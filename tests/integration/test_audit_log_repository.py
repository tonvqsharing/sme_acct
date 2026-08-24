"""Integration: audit chain survives SQLite persistence + session boundaries."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.bricks.audit_log.services import AuditLogService
from src.bricks.audit_log.storage import (
    Base,
    SQLAlchemyAuditLogRepository,
)

ACTOR = uuid4()
ENTITY = uuid4()


@pytest.fixture()
def make_svc():
    def _make():
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine, SQLAlchemyAuditLogRepository(sessionmaker(bind=engine)())

    return _make


def test_chain_persists_and_verifies(make_svc):
    engine, repo = make_svc()
    svc = AuditLogService(repo)
    for act in ("CREATE", "UPDATE", "DEACTIVATE"):
        svc.append(
            entity_type="payment_term",
            entity_id=ENTITY,
            action=act,
            actor_id=ACTOR,
            reason=act.lower(),
        )
    assert svc.verify_chain("payment_term", ENTITY) is True
    assert len(svc.get_by_entity("payment_term", ENTITY)) == 3
    engine.dispose()


def test_new_session_sees_prior_events_and_extends_chain(make_svc):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    first = AuditLogService(SQLAlchemyAuditLogRepository(factory()))
    e1 = first.append(
        entity_type="series",
        entity_id=ENTITY,
        action="CREATE",
        actor_id=ACTOR,
        reason="go",
    )

    second = AuditLogService(SQLAlchemyAuditLogRepository(factory()))
    e2 = second.append(
        entity_type="series",
        entity_id=ENTITY,
        action="UPDATE",
        actor_id=uuid4(),
        reason="next",
    )
    assert e2.prev_checksum == e1.checksum
    assert second.verify_chain("series", ENTITY) is True
    engine.dispose()
