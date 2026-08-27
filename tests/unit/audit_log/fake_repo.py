"""Shared in-memory fake repo for audit_log unit tests."""

from __future__ import annotations

from src.bricks.audit_log.contract import AuditLogPort, AuditQueryResult


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

    def query(
        self,
        *,
        entity_type=None,
        entity_id=None,
        action=None,
        actor_id=None,
        field_name=None,
        start_date=None,
        end_date=None,
        page=1,
        page_size=50,
    ):
        filtered = self.events
        if entity_type is not None:
            filtered = [e for e in filtered if e.entity_type == entity_type]
        if entity_id is not None:
            filtered = [e for e in filtered if e.entity_id == entity_id]
        if action is not None:
            filtered = [e for e in filtered if e.action == action]
        if actor_id is not None:
            filtered = [e for e in filtered if e.actor_id == actor_id]
        if field_name is not None:
            filtered = [e for e in filtered if e.field_name == field_name]
        if start_date is not None:
            filtered = [e for e in filtered if e.changed_at >= start_date]
        if end_date is not None:
            filtered = [e for e in filtered if e.changed_at <= end_date]
        total = len(filtered)
        start = (page - 1) * page_size
        items = filtered[start : start + page_size]
        return AuditQueryResult(items=items, total=total, page=page, page_size=page_size)
