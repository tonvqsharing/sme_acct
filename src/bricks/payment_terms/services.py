"""Payment Terms & Document Numbering services.

Business rules R-001..R-012 per docs/payment-terms/specs-payment-terms.md §5.
Pure Python — orchestrates repositories via contract ports. No Flask/SQLAlchemy.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.bricks.payment_terms.contract import (
    DocumentNumberingSeriesRepositoryPort,
    PaymentTermRepositoryPort,
)
from src.bricks.payment_terms.domain import (
    GENESIS_CHECKSUM,
    TT163_RE,
    ActorRequiredError,
    ApprovalRequest,
    DefaultAlreadyExistsError,
    DocumentNumberingSeries,
    DuplicatePaymentTermError,
    InvalidSeriesPrefixError,
    MaxSeriesExceededError,
    PaymentTerm,
    PaymentTermNotFoundError,
    PaymentTermStatus,
    PendingRequestExistsError,
    PrefixAlreadyExistsError,
    ReasonRequiredError,
    RequestType,
    SequenceAtMaxError,
    SeriesInactiveError,
    SeriesNotFoundError,
    SodViolationError,
    compute_checksum,
)

# Roles per spec §6.1 (Flask built-in enforcement at API layer; service re-checks)
READ_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR")
WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")
DEFAULT_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")

MAX_ACTIVE_SERIES = 15  # R-008, GDT Circular 163/2020/TT-BTC


def _require_actor_reason(actor: UUID | None, reason: str | None) -> tuple[UUID, str]:
    """R-003 / R-004 / EX-001. Returns narrowed (actor, reason)."""
    if not actor:
        raise ActorRequiredError("actor là bắt buộc")
    if not reason or not reason.strip():
        raise ReasonRequiredError("reason là bắt buộc")
    return actor, reason


def _stamp(
    term_or_series: PaymentTerm | DocumentNumberingSeries | ApprovalRequest,
    action: str,
    actor: UUID,
    reason: str,
) -> str:
    """R-010: chain SHA-256 checksum onto entity; returns new checksum."""
    return compute_checksum(
        prev=term_or_series.checksum or GENESIS_CHECKSUM,
        actor=actor,
        timestamp=term_or_series.created_at.isoformat(),
        action=action,
        reason=reason,
        entity_id=term_or_series.id,
    )


# ═══ PaymentTermService ════════════════════════════════════════════════════


class PaymentTermService:
    """Orchestrates payment term use cases."""

    def __init__(self, repo: PaymentTermRepositoryPort) -> None:
        self._repo = repo

    def create_payment_term(
        self,
        *,
        company_id: UUID,
        name: str,
        due_days: int,
        interest_rate: Decimal,
        actor: UUID | None,
        reason: str | None,
        is_default: bool = False,
    ) -> PaymentTerm:
        actor, reason = _require_actor_reason(actor, reason)
        if is_default and self._repo.get_default_by_company(company_id) is not None:
            raise DefaultAlreadyExistsError("Doanh nghiệp đã có default")
        if not self._repo.validate_name_unique(company_id, name):
            raise DuplicatePaymentTermError("Tên đã tồn tại")

        term = PaymentTerm(
            id=uuid.uuid4(),
            company_id=company_id,
            name=name.strip(),
            due_days=due_days,
            interest_rate=interest_rate,
            is_default=is_default,
        )
        term.checksum = _stamp(term, "CREATE", actor, reason)
        return self._repo.create(term)

    def get_payment_term(self, payment_term_id: UUID) -> PaymentTerm | None:
        return self._repo.get_by_id(payment_term_id)

    def list_by_company(self, company_id: UUID, status: str | None = None) -> list[PaymentTerm]:
        terms = self._repo.get_by_company(company_id)
        if status == "active":
            return [t for t in terms if t.status == PaymentTermStatus.ACTIVE]
        if status == "inactive":
            return [t for t in terms if t.status == PaymentTermStatus.INACTIVE]
        return terms

    def get_default(self, company_id: UUID) -> PaymentTerm | None:
        return self._repo.get_default_by_company(company_id)

    def update_payment_term(
        self,
        payment_term_id: UUID,
        *,
        actor: UUID | None,
        reason: str | None,
        **fields: object,
    ) -> PaymentTerm:
        actor, reason = _require_actor_reason(actor, reason)
        term = self._repo.get_by_id(payment_term_id)
        if term is None:
            raise PaymentTermNotFoundError("Không tìm thấy payment term")

        allowed = {"name", "due_days", "interest_rate"}
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"Cannot update fields: {sorted(unknown)}")
        for key, value in fields.items():
            setattr(term, key, value)

        term.checksum = _stamp(term, "UPDATE", actor, reason)
        return self._repo.update(term)

    def set_default_payment_term(
        self, payment_term_id: UUID, actor: UUID | None, reason: str | None
    ) -> PaymentTerm:
        """R-001 + AP-003: blocked while another default exists."""
        actor, reason = _require_actor_reason(actor, reason)
        term = self._repo.get_by_id(payment_term_id)
        if term is None:
            raise PaymentTermNotFoundError("Không tìm thấy payment term")
        current = self._repo.get_default_by_company(term.company_id)
        if current is not None and current.id != term.id:
            raise DefaultAlreadyExistsError("Doanh nghiệp đã có default")
        result = self._repo.set_default(payment_term_id, actor, reason)
        assert result is not None
        result.checksum = _stamp(result, "SET_DEFAULT", actor, reason)
        return self._repo.update(result)

    def deactivate_payment_term(
        self, payment_term_id: UUID, actor: UUID | None, reason: str | None
    ) -> PaymentTerm:
        """R-006 soft-deactivate; the active default cannot be dropped."""
        actor, reason = _require_actor_reason(actor, reason)
        term = self._repo.get_by_id(payment_term_id)
        if term is None:
            raise PaymentTermNotFoundError("Không tìm thấy payment term")
        if term.is_default:
            raise DefaultAlreadyExistsError("Không thể vô hiệu hóa payment term mặc định")
        term.status = PaymentTermStatus.INACTIVE
        term.checksum = _stamp(term, "DEACTIVATE", actor, reason)
        return self._repo.update(term)

    def validate_before_invoice_entry(self, company_id: UUID) -> PaymentTerm:
        """EX-009: invoice needs a default payment term."""
        default = self._repo.get_default_by_company(company_id)
        if default is None:
            from src.bricks.payment_terms.domain import PaymentTermsDomainError

            err = PaymentTermsDomainError("Chưa có payment term")
            err.code = "NO_PAYMENT_TERM"
            err.http_status = 400
            raise err
        return default


# ═══ DocumentNumberingSeriesService ════════════════════════════════════════


class DocumentNumberingSeriesService:
    """Orchestrates document numbering series use cases."""

    MAX_ACTIVE_SERIES = MAX_ACTIVE_SERIES

    def __init__(self, repo: DocumentNumberingSeriesRepositoryPort) -> None:
        self._repo = repo

    def create_series(
        self,
        *,
        company_id: UUID,
        prefix: str,
        actor: UUID | None,
        reason: str | None,
    ) -> DocumentNumberingSeries:
        actor, reason = _require_actor_reason(actor, reason)
        # EX-004 / R-007
        if not TT163_RE.match(prefix or ""):
            raise InvalidSeriesPrefixError("Định dạng prefix không hợp lệ")
        # AP-002 / R-009
        if not self._repo.validate_prefix_unique(company_id, prefix):
            raise PrefixAlreadyExistsError("Prefix đã tồn tại")
        # EX-005 / R-008 (new series defaults to active)
        if self._repo.check_max_series_limit(company_id):
            raise MaxSeriesExceededError("Đã đạt giới hạn 15 series active")

        series = DocumentNumberingSeries(
            id=uuid.uuid4(),
            company_id=company_id,
            prefix=prefix,
            next_sequence=1,
        )
        series.checksum = _stamp(series, "CREATE", actor, reason)
        return self._repo.create(series)

    def get_series(self, series_id: UUID) -> DocumentNumberingSeries | None:
        return self._repo.get_by_id(series_id)

    def list_by_company(
        self, company_id: UUID, active: bool | None = None
    ) -> list[DocumentNumberingSeries]:
        if active is True:
            return self._repo.get_active_by_company(company_id)
        return self._repo.get_by_company(company_id)

    def update_series(
        self,
        series_id: UUID,
        *,
        actor: UUID | None,
        reason: str | None,
        **fields: object,
    ) -> DocumentNumberingSeries:
        actor, reason = _require_actor_reason(actor, reason)
        series = self._repo.get_by_id(series_id)
        if series is None:
            raise SeriesNotFoundError("Không tìm thấy series")

        allowed = {"max_sequences"}
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"Cannot update fields: {sorted(unknown)}")
        for key, value in fields.items():
            setattr(series, key, value)

        series.checksum = _stamp(series, "UPDATE", actor, reason)
        return self._repo.update(series)

    def activate_series(
        self, series_id: UUID, actor: UUID | None, reason: str | None
    ) -> DocumentNumberingSeries:
        """SOD-gated at API layer; max-active guard here (AP-006)."""
        actor, reason = _require_actor_reason(actor, reason)
        series = self._repo.get_by_id(series_id)
        if series is None:
            raise SeriesNotFoundError("Không tìm thấy series")
        if not series.is_active and self._repo.check_max_series_limit(series.company_id):
            raise MaxSeriesExceededError("Đã đạt giới hạn 15 series active")
        result = self._repo.activate(series_id, actor, reason)
        assert result is not None
        result.checksum = _stamp(result, "ACTIVATE", actor, reason)
        return self._repo.update(result)

    def deactivate_series(
        self, series_id: UUID, actor: UUID | None, reason: str | None
    ) -> DocumentNumberingSeries:
        """R-011: soft-deactivate only."""
        actor, reason = _require_actor_reason(actor, reason)
        series = self._repo.get_by_id(series_id)
        if series is None:
            raise SeriesNotFoundError("Không tìm thấy series")
        result = self._repo.deactivate(series_id, actor, reason)
        assert result is not None
        result.checksum = _stamp(result, "DEACTIVATE", actor, reason)
        return self._repo.update(result)

    def increment_sequence(self, series_id: UUID, actor: UUID | None, reason: str | None) -> int:
        """R-010 atomic increment; EX-006/EX-008 guards. Returns sequence used."""
        actor, reason = _require_actor_reason(actor, reason)
        series = self._repo.get_by_id(series_id)
        if series is None:
            raise SeriesNotFoundError("Không tìm thấy series")
        if not series.is_active:
            raise SeriesInactiveError("Series không phải ACTIVE")  # EX-008
        try:
            seq_used = series.next_sequence
            series.increment_sequence()  # raises ValueError at max → map below
        except ValueError as exc:
            if str(exc) == "SEQUENCE_AT_MAX":
                raise SequenceAtMaxError("Số tiếp theo đã đạt giới hạn") from exc
            raise
        series.checksum = _stamp(series, "INCREMENT", actor, reason)
        self._repo.update(series)
        return seq_used


# ═══ SOD Approval Service (spec §11.1 / §11.2) ═════════════════════════════


class ApprovalRequestNotFoundError(PaymentTermNotFoundError):
    pass


class ApprovalService:
    """Two-actor gate for set-default & series activation.

    Flow: privileged actor requests → PENDING → second (different) actor
    approves/rejects. Approval applies the effect via the underlying
    services and appends audit events for REQUEST + decision.
    """

    def __init__(
        self,
        repo: Any,  # SQLAlchemyApprovalRequestRepository-like
        term_service: PaymentTermService,
        series_service: DocumentNumberingSeriesService,
        audit: Any | None = None,
    ) -> None:
        from src.bricks.payment_terms.storage import (  # noqa: F401
            SQLAlchemyApprovalRequestRepository,
        )

        self._repo = repo
        self._terms = term_service
        self._series = series_service
        self._audit = audit

    def _audit_append(self, action: str, entity_id: UUID, actor: UUID, reason: str) -> None:
        if self._audit is None:
            return
        self._audit.append(
            entity_type="pt_approval",
            entity_id=entity_id,
            action=action,
            actor_id=actor,
            reason=reason,
            after_value=None,
        )

    def request_set_default(
        self,
        term_id: UUID,
        actor: UUID | None,
        reason: str | None,
    ) -> ApprovalRequest:
        actor_x, reason_x = _require_actor_reason(actor, reason)
        term = self._terms.get_payment_term(term_id)
        if term is None:
            raise PaymentTermNotFoundError("Không tìm thấy payment term")
        if term.is_default:
            raise DefaultAlreadyExistsError("Đã là default")
        existing = self._repo.find_pending(RequestType.SET_DEFAULT, term_id)
        if existing is not None:
            raise PendingRequestExistsError("Đã có yêu cầu chờ duyệt")
        req = ApprovalRequest(
            id=uuid.uuid4(),
            company_id=term.company_id,
            request_type=RequestType.SET_DEFAULT,
            target_id=term_id,
            requested_by=actor_x,
            reason=reason_x,
        )
        req.checksum = _stamp(req, "DEFAULT_REQUEST", actor_x, reason_x)
        created: ApprovalRequest = self._repo.create(req)
        self._audit_append("DEFAULT_REQUEST", created.id, actor_x, reason_x)
        return created

    def request_activate_series(
        self, series_id: UUID, actor: UUID | None, reason: str | None
    ) -> ApprovalRequest | None:
        actor_x, reason_x = _require_actor_reason(actor, reason)
        series = self._series.get_series(series_id)
        if series is None:
            raise SeriesNotFoundError("Không tìm thấy series")
        if series.is_active:
            return None  # nothing to do; caller maps to 200 no-op
        if self._series._repo.check_max_series_limit(series.company_id):
            raise MaxSeriesExceededError("Đã đạt giới hạn 15 series active")
        existing = self._repo.find_pending(RequestType.ACTIVATE_SERIES, series_id)
        if existing is not None:
            raise PendingRequestExistsError("Đã có yêu cầu chờ duyệt")
        req = ApprovalRequest(
            id=uuid.uuid4(),
            company_id=series.company_id,
            request_type=RequestType.ACTIVATE_SERIES,
            target_id=series_id,
            requested_by=actor_x,
            reason=reason_x,
        )
        req.checksum = _stamp(req, "ACTIVATE_REQUEST", actor_x, reason_x)
        created: ApprovalRequest = self._repo.create(req)
        self._audit_append("ACTIVATE_REQUEST", created.id, actor_x, reason_x)
        return created

    def decide(
        self,
        request_id: UUID,
        approver: UUID | None,
        reason: str | None,
        approve: bool,
    ) -> ApprovalRequest:
        actor_x, reason_x = _require_actor_reason(approver, reason)
        req = self._repo.get_by_id(request_id)
        if req is None:
            raise ApprovalRequestNotFoundError("Không tìm thấy yêu cầu")
        if actor_x == req.requested_by:
            raise SodViolationError("Không thể tự phê duyệt yêu cầu của chính mình")
        try:
            decided = req.decide(actor_x, approve, reason_x)
        except ValueError as exc:
            code = str(exc)
            if code == "SOD_SAME_ACTOR":
                raise SodViolationError("Không thể tự phê duyệt yêu cầu của chính mình") from exc
            raise PendingRequestExistsError("Yêu cầu đã được xử lý") from exc

        action = (
            (
                "DEFAULT_APPROVE"
                if req.request_type == RequestType.SET_DEFAULT
                else "ACTIVATE_APPROVE"
            )
            if approve
            else ("REQUEST_REJECT")
        )
        decided.checksum = _stamp(decided, action, actor_x, reason_x)
        saved: ApprovalRequest = self._repo.update(decided)

        if approve:
            if req.request_type == RequestType.SET_DEFAULT:
                self._terms.set_default_payment_term(req.target_id, actor_x, f"SOD:{request_id}")
            else:
                self._series.activate_series(req.target_id, actor_x, f"SOD:{request_id}")
        self._audit_append(action, request_id, actor_x, reason_x)
        return saved

    def list_requests(self, status: str | None = None) -> list[ApprovalRequest]:
        out: list[ApprovalRequest] = self._repo.list_by_status(status)
        return out
