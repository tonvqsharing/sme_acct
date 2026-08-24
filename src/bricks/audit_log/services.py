"""Audit log service — append + tamper-evident chain verification (FR-3)."""

from __future__ import annotations

from typing import TypedDict


class JSONDict(TypedDict, total=False):
    pass

import re
from uuid import UUID

from src.bricks.audit_log.contract import AuditLogPort
from src.bricks.audit_log.domain import AuditEvent, compute_event_checksum

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class AuditChainBrokenError(Exception):
    """Raised when verify detects a recomputed checksum mismatch."""


class AuditLogService:
    def __init__(self, repo: AuditLogPort) -> None:
        self._repo = repo

    def append(
        self,
        *,
        entity_type: str,
        entity_id: UUID,
        action: str,
        actor_id: UUID,
        reason: str,
        field_name: str | None = None,
        before_value: JSONDict | None = None,
        after_value: JSONDict | None = None,
    ) -> AuditEvent:
        for name, val in (
            ("entity_type", entity_type),
            ("entity_id", entity_id),
            ("action", action),
            ("actor_id", actor_id),
        ):
            if val is None or val == "":
                raise ValueError(f"{name} is required")

        event = AuditEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            reason=reason,
            field_name=field_name,
            before_value=before_value,
            after_value=after_value,
            prev_checksum=self._repo.last_checksum_for(entity_type, entity_id) or "0" * 64,
        )
        return self._repo.append(event)

    def get_by_entity(self, entity_type: str, entity_id: UUID) -> list[AuditEvent]:
        return self._repo.get_by_entity(entity_type, entity_id)

    def verify_chain(self, entity_type: str, entity_id: UUID) -> bool:
        events = self._repo.get_by_entity(entity_type, entity_id)
        prev = "0" * 64
        for ev in events:
            if ev.prev_checksum != prev:
                return False
            expected = compute_event_checksum(
                prev=ev.prev_checksum,
                entity_type=ev.entity_type,
                entity_id=ev.entity_id,
                action=ev.action,
                actor_id=ev.actor_id,
                changed_at=ev.changed_at.isoformat(),
                reason=ev.reason,
                field_name=ev.field_name,
                before_value=ev.before_value,
                after_value=ev.after_value,
            )
            if not _HEX64.match(ev.checksum) or ev.checksum != expected:
                return False
            prev = ev.checksum
        return True
