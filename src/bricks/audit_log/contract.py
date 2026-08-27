"""Public port for audit_log brick. Append-only by design (NFR-1)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple

from src.bricks.audit_log.domain import AuditEvent


class AuditQueryResult(NamedTuple):
    """Paginated query result."""

    items: list[AuditEvent]
    total: int
    page: int
    page_size: int


class AuditLogPort(ABC):
    @abstractmethod
    def append(self, event: AuditEvent) -> AuditEvent:
        """Persist one immutable event."""
        ...

    @abstractmethod
    def get_by_entity(self, entity_type: str, entity_id: object) -> list[AuditEvent]:
        """Chronological events for an entity."""
        ...

    @abstractmethod
    def last_checksum_for(self, entity_type: str, entity_id: object) -> str | None:
        """Tip of the chain for an entity; None when empty."""
        ...

    @abstractmethod
    def query(
        self,
        *,
        entity_type: str | None = None,
        entity_id: object | None = None,
        action: str | None = None,
        actor_id: object | None = None,
        field_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AuditQueryResult:
        """Filtered, paginated query across all audit events (FR-2.1, FR-2.3)."""
        ...
