"""Public port for audit_log brick. Append-only by design (NFR-1)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.audit_log.domain import AuditEvent


class AuditLogPort(ABC):
    @abstractmethod
    def append(self, event: AuditEvent) -> AuditEvent:
        """Persist one immutable event."""
        ...

    @abstractmethod
    def get_by_entity(self, entity_type: str, entity_id: UUID) -> list[AuditEvent]:
        """Chronological events for an entity."""
        ...

    @abstractmethod
    def last_checksum_for(self, entity_type: str, entity_id: UUID) -> str | None:
        """Tip of the chain for an entity; None when empty."""
        ...
