"""Audit log domain — immutable, checksum-chained events. Pure Python."""

from __future__ import annotations

from typing import TypedDict


class JSONDict(TypedDict, total=False):
    pass

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

GENESIS_CHECKSUM = "0" * 64


def _canonical(
    *,
    prev: str,
    entity_type: str,
    entity_id: UUID,
    action: str,
    actor_id: UUID,
    changed_at: str,
    reason: str,
    field_name: str | None,
    before_value: JSONDict | None,
    after_value: JSONDict | None,
) -> str:
    payload = json.dumps(
        {
            "prev": prev,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "action": action,
            "actor_id": str(actor_id),
            "changed_at": changed_at,
            "reason": reason,
            "field_name": field_name,
            "before_value": before_value,
            "after_value": after_value,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return payload


def compute_event_checksum(**parts: object) -> str:
    canonical = _canonical(**parts)  # type: ignore[arg-type]
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class AuditEvent:
    """Immutable audit record per docs/audit-log/specs-audit-log.md §1.1."""

    entity_type: str
    entity_id: UUID
    action: str
    actor_id: UUID
    reason: str
    id: UUID = field(default_factory=uuid4)
    field_name: str | None = None
    before_value: JSONDict | None = None
    after_value: JSONDict | None = None
    changed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    prev_checksum: str = GENESIS_CHECKSUM
    checksum: str = ""

    def __post_init__(self) -> None:
        if not self.entity_type:
            raise ValueError("entity_type is required")
        if not isinstance(self.entity_id, UUID):
            raise TypeError("entity_id must be a UUID")
        if not self.action:
            raise ValueError("action is required")
        if not isinstance(self.actor_id, UUID):
            raise TypeError("actor_id must be a UUID")

        self.checksum = compute_event_checksum(
            prev=self.prev_checksum,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            action=self.action,
            actor_id=self.actor_id,
            changed_at=self.changed_at.isoformat(),
            reason=self.reason,
            field_name=self.field_name,
            before_value=self.before_value,
            after_value=self.after_value,
        )

    def __setattr__(self, name: str, value: object) -> None:
        # NFR-1 immutability after construction (checksum computed in init)
        if getattr(self, "checksum", "") != "" and name in (
            "entity_type",
            "entity_id",
            "action",
            "actor_id",
            "reason",
            "field_name",
            "before_value",
            "after_value",
            "prev_checksum",
            "checksum",
            "changed_at",
        ):
            raise AttributeError("AuditEvent is immutable")
        object.__setattr__(self, name, value)
