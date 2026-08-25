"""Invoice service — orchestrates FY period gate, COA gate, numbering, terms."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal


def _d(v: Any) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


from typing import Any
from uuid import UUID

from src.bricks.invoice.domain import (
    GENESIS_CHECKSUM,
    Invoice,
    InvoiceItem,
)


class NoOpenPeriodError(Exception):
    """FY brick has no OPEN period covering issue_date."""


PeriodClosedError = NoOpenPeriodError  # alias for API mapping


class UnknownAccountError(Exception):
    pass


AggregateAccountError = UnknownAccountError  # refined below
InactiveAccountError = UnknownAccountError


class AlreadyPostedError(Exception):
    pass


class InvoiceNotFoundError(Exception):
    pass


class InvoiceService:
    """Depends on narrow ports only — never concrete bricks."""

    def __init__(
        self,
        *,
        fy: Any,
        coa: Any,
        numbering: Any,
        terms: Any,
        audit: Any,
        repo: Any | None = None,
        regime_of: Any | None = None,
        allowed_vat_rates: frozenset[str] | None = None,
        rate_gate: Any | None = None,
    ) -> None:
        self._fy = fy
        self._coa = coa
        self._numbering = numbering
        self._terms = terms
        self._audit = audit
        self._regime_of = regime_of

        raw = allowed_vat_rates if allowed_vat_rates is not None else {"0", "0.05", "0.08", "0.1"}
        self._allowed_vat_rates = frozenset(str(_d(r)) for r in raw)
        self._rate_gate = rate_gate
        self._repo = repo if repo is not None else _MemoryRepo()

    # ── create ──────────────────────────────────────────────────────────
    def create_invoice(
        self,
        *,
        company_id: UUID,
        customer_name: str,
        issue_date: Any,
        vat_rate: Any,
        items: list[dict[str, str]],
        payment_term_id: UUID | None = None,
        actor: UUID | str | None,
        reason: str | None,
    ) -> Invoice:
        actor_u: UUID = actor if isinstance(actor, UUID) else UUID(str(actor))
        if not actor or not reason or not str(reason).strip():
            raise ValueError("actor and reason are required")
        if not items:
            raise ValueError("items must not be empty")

        # Gate 1: posting period open
        if self._fy.find_open_period(company_id, issue_date) is None:
            raise NoOpenPeriodError("Kỳ sổ chưa mở cho ngày hạch toán")

        # Gate 0: the invoice-level VAT rate must come from the lawful
        # catalog (invoice carries one rate across its lines).
        rate_str = str(_d(vat_rate))
        if rate_str not in self._allowed_vat_rates:
            raise ValueError(f"vat_rate {rate_str} không thuộc catalog thuế suất")
        if self._rate_gate is not None and issue_date is not None:
            self._rate_gate(rate_str, issue_date)
        vat_rate = _d(vat_rate)

        # Gate 2: every line posts to an ACTIVE posting-level account,
        # validated under the company's own regime catalog.
        regime = self._regime_of(company_id) if self._regime_of else "tt133"
        for it in items:
            self._coa.validate_posting_account(company_id, it["account_code"], regime)

        # Number from document-numbering series
        number = self._numbering.issue(company_id)

        # Payment term → due date
        due_date = None
        term_ref = payment_term_id
        if payment_term_id is None and hasattr(self._terms, "get_default"):
            default_term = self._terms.get_default(company_id)
            term_ref = getattr(default_term, "id", None)
        if term_ref is not None:
            term = (
                self._terms.get_payment_term(term_ref)
                if hasattr(self._terms, "get_payment_term")
                else self._terms.get_default(company_id)
            )
            if term is not None:
                due_date = issue_date + timedelta(days=term.due_days)

        invoice = Invoice(
            company_id=company_id,
            number=number,
            issue_date=issue_date,
            customer_name=customer_name,
            items=[
                InvoiceItem(
                    account_code=i["account_code"],
                    description=i.get("description", ""),
                    amount=Decimal(str(i["amount"])),
                )
                for i in items
            ],
            vat_rate=vat_rate,
            due_date=due_date,
            payment_term_id=term_ref,
        )
        invoice.checksum = invoice.compute_checksum(GENESIS_CHECKSUM, actor_u, str(reason))
        return self._repo.save(invoice)

    # ── post ────────────────────────────────────────────────────────────
    def post_invoice(self, invoice_id: UUID, *, actor: UUID, reason: str) -> Invoice:
        inv = self._repo.get_by_id(invoice_id)
        if inv is None:
            raise InvoiceNotFoundError("Không tìm thấy hóa đơn")
        if inv.status.value == "POSTED":
            raise AlreadyPostedError("Hóa đơn đã được ghi sổ")
        from src.bricks.invoice.domain import InvoiceStatus

        object.__setattr__(inv, "_prev_status", inv.status)
        inv.status = InvoiceStatus.POSTED
        inv.checksum = inv.compute_checksum(inv.checksum, actor, str(reason))
        saved = self._repo.save(inv)
        if self._audit is not None:
            self._audit.append(
                entity_type="invoice",
                entity_id=inv.id,
                action="POST",
                actor_id=actor,
                reason=str(reason),
                after_value={"grand_total": float(inv.grand_total)},
            )
        return saved

    def get_invoice(self, invoice_id: UUID) -> Invoice | None:
        return self._repo.get_by_id(invoice_id)

    def list_invoices(self, company_id: UUID) -> list[Invoice]:
        return self._repo.get_by_company(company_id)


class _MemoryRepo:
    def __init__(self) -> None:
        self._rows: dict[UUID, Invoice] = {}

    def save(self, inv: Invoice) -> Invoice:
        self._rows[inv.id] = inv
        return inv

    def get_by_id(self, iid: UUID) -> Invoice | None:
        return self._rows.get(iid)

    def get_by_company(self, cid: UUID) -> list[Invoice]:
        return [i for i in self._rows.values() if i.company_id == cid]
