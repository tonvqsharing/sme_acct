"""Shared in-memory fake repo for audit_log unit tests."""

from __future__ import annotations

from src.bricks.audit_log.contract import AuditLogPort


class FakeAuditRepo(AuditLogPort):
    def __init__(self):
        self.events: list = []

    def append(self, event):
        self.events.append(event)
        return event

    def get_by_entity(self, entity_type, entity_id):
        return [e for e in self.events if e.entity_type == entity_type and e.entity_id == entity_id]

    def last_checksum_for(self, entity_type, entity_id):
        rows = self.get_by_entity(entity_type, entity_id)
        return rows[-1].checksum if rows else None
