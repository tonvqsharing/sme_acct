"""Audit log storage — append-only SQLAlchemy adapter."""

from __future__ import annotations

from typing import TypedDict


class JSONDict(TypedDict, total=False):
    pass


from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import JSON, Text

from src.bricks.audit_log.contract import AuditLogPort, AuditQueryResult
from src.bricks.audit_log.domain import AuditEvent


class Base(DeclarativeBase):
    pass


class AuditEventModel(Base):
    """audit_events table. No UPDATE/DELETE paths exist in this brick."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(50))
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    before_value: Mapped[JSONDict | None] = mapped_column(JSON, nullable=True)
    after_value: Mapped[JSONDict | None] = mapped_column(JSON, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    prev_checksum: Mapped[str] = mapped_column(String(64))
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    # Exact ISO string hashed into the checksum — datetime round-trip via
    # SQLite can lose microseconds/tz, which would silently break verify.
    ts_iso: Mapped[str] = mapped_column(String(64))
    # Per-entity insertion ordinal: deterministic chain ordering regardless
    # of clock resolution. Single-writer assumption (SQLite); revisit with a
    # DB sequence under Postgres.
    seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SQLAlchemyAuditLogRepository(AuditLogPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(m: AuditEventModel) -> AuditEvent:
        ev = AuditEvent(
            entity_type=m.entity_type,
            entity_id=UUID(m.entity_id),
            action=m.action,
            actor_id=UUID(m.actor_id),
            reason=m.reason,
            id=UUID(m.id),
            field_name=m.field_name,
            before_value=m.before_value,
            after_value=m.after_value,
            changed_at=datetime.fromisoformat(m.ts_iso),
            prev_checksum=m.prev_checksum,
        )
        # Restore persisted checksum (constructor recomputed it; same value
        # iff row untampered — which verify_chain checks independently).
        object.__setattr__(ev, "checksum", m.checksum)
        return ev

    def _next_seq(self, entity_type: str, entity_id: str) -> int:
        current = (
            self._session.query(AuditEventModel)
            .filter(
                AuditEventModel.entity_type == entity_type,
                AuditEventModel.entity_id == entity_id,
            )
            .count()
        )
        return current + 1

    def append(self, event: AuditEvent) -> AuditEvent:
        self._session.add(
            AuditEventModel(
                id=str(event.id),
                entity_type=event.entity_type,
                entity_id=str(event.entity_id),
                action=event.action,
                actor_id=str(event.actor_id),
                reason=event.reason,
                field_name=event.field_name,
                before_value=event.before_value,
                after_value=event.after_value,
                changed_at=event.changed_at,
                ts_iso=event.changed_at.isoformat(),
                prev_checksum=event.prev_checksum,
                checksum=event.checksum,
                seq=self._next_seq(event.entity_type, str(event.entity_id)),
            )
        )
        self._session.commit()
        return event

    def get_by_entity(self, entity_type: str, entity_id: object) -> list[AuditEvent]:
        rows = (
            self._session.query(AuditEventModel)
            .filter(
                AuditEventModel.entity_type == entity_type,
                AuditEventModel.entity_id == str(entity_id),
            )
            .order_by(AuditEventModel.seq.asc())
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def last_checksum_for(self, entity_type: str, entity_id: object) -> str | None:
        row = (
            self._session.query(AuditEventModel)
            .filter(
                AuditEventModel.entity_type == entity_type,
                AuditEventModel.entity_id == str(entity_id),
            )
            .order_by(AuditEventModel.seq.desc())
            .first()
        )
        return row.checksum if row else None

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
        q = self._session.query(AuditEventModel)
        if entity_type is not None:
            q = q.filter(AuditEventModel.entity_type == entity_type)
        if entity_id is not None:
            q = q.filter(AuditEventModel.entity_id == str(entity_id))
        if action is not None:
            q = q.filter(AuditEventModel.action == action)
        if actor_id is not None:
            q = q.filter(AuditEventModel.actor_id == str(actor_id))
        if field_name is not None:
            q = q.filter(AuditEventModel.field_name == field_name)
        if start_date is not None:
            q = q.filter(AuditEventModel.changed_at >= start_date)
        if end_date is not None:
            q = q.filter(AuditEventModel.changed_at <= end_date)
        total = q.count()
        rows = (
            q.order_by(AuditEventModel.seq.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return AuditQueryResult(
            items=[self._to_domain(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
