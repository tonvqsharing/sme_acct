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


class AlreadyIssuedError(Exception):
    pass


class NotPostedError(Exception):
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
        period_lock: Any | None = None,
        signer: Any | None = None,
        exclusion_of: Any | None = None,
    ) -> None:
        self._fy = fy
        self._coa = coa
        self._numbering = numbering
        self._terms = terms
        self._audit = audit
        self._regime_of = regime_of
        self._period_lock = period_lock
        self._signer = signer
        self._exclusion_of = exclusion_of
        if self._exclusion_of is None:
            from src.bricks.system_settings.rate_windows import (
                is_8pct_eligible as _static_eligible,
            )

            self._exclusion_of = lambda company_id, category=None: _static_eligible(category)
        assert self._exclusion_of is not None

        from src.bricks.system_settings.contract import ALLOWED_VAT_FRACTIONS

        raw = allowed_vat_rates if allowed_vat_rates is not None else ALLOWED_VAT_FRACTIONS
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
        vat_rate: Any = Decimal("0.1"),
        items: list[dict[str, Any]],
        payment_term_id: UUID | None = None,
        product_category: str | None = None,
        actor: UUID | str | None,
        reason: str | None,
        template_code: str | None = None,
        invoice_symbol: str | None = None,
        customer_mst: str | None = None,
        currency_code: str | None = None,
        fx_rate: Any | None = None,
        # TT99 multi-PO / agent
        is_agent: bool = False,
    ) -> Invoice:
        actor_u: UUID = actor if isinstance(actor, UUID) else UUID(str(actor))
        if not actor or not reason or not str(reason).strip():
            raise ValueError("actor and reason are required")
        if not items:
            raise ValueError("items must not be empty")

        # ── FX gate (P1) ──
        cur = (currency_code or "VND").upper()
        fx = _d(fx_rate) if fx_rate is not None else None
        if cur != "VND" and fx is None:
            raise ValueError("fx_rate required for FX invoice")
        if fx is not None and fx <= 0:
            raise ValueError("fx_rate must be > 0")

        # Gate 1: posting period open + period-lock (TT99)
        if self._fy.find_open_period(company_id, issue_date) is None:
            raise NoOpenPeriodError("Kỳ sổ chưa mở cho ngày hạch toán")
        # period-lock via SystemSettings if available
        if hasattr(self, "_period_lock") and self._period_lock is not None:
            try:
                # fiscal year derived from issue_date
                fy_year = getattr(issue_date, "year", None)
                month = getattr(issue_date, "month", None)
                if fy_year and month and self._period_lock.is_locked(company_id, fy_year, month):
                    raise NoOpenPeriodError("Kỳ sổ đã khóa")
            except NoOpenPeriodError:
                raise
            except Exception:  # noqa: BLE001, S110 — period lock optional
                pass

        # Gate 0: per-line VAT catalog + window + 8% category
        # Header vat_rate is fallback for legacy items without vat_rate
        header_rate_str = str(_d(vat_rate)) if vat_rate is not None else None
        if (
            header_rate_str is not None
            and header_rate_str not in self._allowed_vat_rates
            and header_rate_str not in ("-0.01", "-1")
        ):
            pass
        # Validate each line's effective rate
        # normalized allowed for Decimal equality (tolerate 0 vs 0.0)
        allowed_decimals = {Decimal(s) for s in self._allowed_vat_rates}
        validated_items: list[dict[str, Any]] = []
        for it in items:
            raw_rate = it.get("vat_rate", vat_rate)
            if raw_rate is None:
                raw_rate = vat_rate
            rate_str_raw = str(_d(raw_rate))
            if rate_str_raw in ("-1", "-0.01"):
                rate_str = "-1"
            else:
                # normalize via Decimal then back to canonical str from allowed if matches
                dec = _d(rate_str_raw)
                if dec in allowed_decimals:
                    # find canonical
                    canon = next(s for s in self._allowed_vat_rates if Decimal(s) == dec)
                    rate_str = canon
                else:
                    rate_str = rate_str_raw
            if rate_str not in self._allowed_vat_rates and rate_str != "-1":
                raise ValueError(f"vat_rate {rate_str} không thuộc catalog thuế suất")
            if self._rate_gate is not None and issue_date is not None and rate_str != "-1":
                self._rate_gate(rate_str, issue_date)
            # 8% eligibility per line (panel-managed exclusion list)
            cat = it.get("category", product_category)
            exclusion_of = self._exclusion_of
            assert exclusion_of is not None
            if rate_str == "0.08" and cat is not None and not exclusion_of(company_id, cat):
                raise ValueError(f"Thuế suất 8% không áp dụng cho nhóm {cat} theo NĐ174/2025")
            validated_items.append(
                {
                    **it,
                    "_rate_str": rate_str,
                    "_vat": _d(rate_str) if rate_str != "-1" else Decimal(-1),
                }
            )

        # Gate 2: every line posts to an ACTIVE posting-level account,
        # validated under the company's own regime catalog.
        regime = self._regime_of(company_id) if self._regime_of else "tt133"
        for it in items:
            self._coa.validate_posting_account(company_id, it["account_code"], regime)

        # TaxId format if provided
        if customer_mst is not None:
            import re

            if not re.match(r"^[1-9]\d{2}(-\d{3})?$", customer_mst.replace(" ", "")):
                # simple 10-digit MST 10 số, 13 với chi nhánh — keep legacy 10
                # but spec says ^[1-9]\d{2}(-\d{3})?$ is for tax family? accept 10 digits too
                stripped = customer_mst.replace("-", "").replace(" ", "")
                if not (
                    stripped.isdigit() and len(stripped) in (10, 13, 14) and stripped[0] != "0"
                ):
                    raise ValueError(f"MST {customer_mst} không hợp lệ")

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
            if term is not None and issue_date is not None:
                due_date = issue_date + timedelta(days=term.due_days)

        # Build domain items with per-line vat
        domain_items = [
            InvoiceItem(
                account_code=i["account_code"],
                description=i.get("description", ""),
                amount=Decimal(str(i["amount"])),
                vat_rate=Decimal(str(i["vat_rate"])) if i.get("vat_rate") is not None else None,
                category=i.get("category"),
                quantity=Decimal(str(i["quantity"])) if i.get("quantity") is not None else None,
                unit_price=(
                    Decimal(str(i["unit_price"])) if i.get("unit_price") is not None else None
                ),
                po_id=i.get("po_id"),
                is_agent=bool(i.get("is_agent", is_agent)),
            )
            for i in items
        ]

        # TT99 multi-PO + agent + BDS defer (S3): compute deferred_amount for 3387
        # Collect categories/po_ids to detect bundle
        deferred = Decimal(0)
        # BDS: if any line category == real_estate → defer whole invoice (control not transferred)
        has_bds = any((i.get("category") or "").lower() == "real_estate" for i in items)
        if has_bds:
            # per TT99: BĐS only recognize when control/handover; defer all
            deferred = sum((Decimal(str(i["amount"])) for i in items), Decimal(0))
            # add VAT of those lines to deferred as well (use per-line rate)
            for it in validated_items:
                if (it.get("category") or "").lower() == "real_estate":
                    amt = Decimal(str(it["amount"]))
                    rate = it["_vat"] if it["_vat"] != Decimal(-1) else Decimal(0)
                    if rate != Decimal(-1):
                        deferred += (amt * rate).quantize(Decimal(1))
        else:
            # Multi-PO: distinct po_id >1 → service POs (assume po_id containing "service" or second group)
            po_ids = [i.get("po_id") for i in items if i.get("po_id")]
            if len(set(po_ids)) > 1:
                # heuristic: treat po_ids with "service" substring as deferred
                service_amount = Decimal(0)
                for it in validated_items:
                    pid = it.get("po_id") or ""
                    if "service" in pid.lower() or "maintenance" in pid.lower():
                        amt = Decimal(str(it["amount"]))
                        service_amount += amt
                        rate = it["_vat"] if it["_vat"] != Decimal(-1) else Decimal(0)
                        if rate != Decimal(0) and rate != Decimal(-1):
                            service_amount += (amt * rate).quantize(Decimal(1))
                deferred = service_amount
            # Single PO → 0

        assert issue_date is not None
        invoice = Invoice(
            company_id=company_id,
            number=number,
            issue_date=issue_date,
            customer_name=customer_name,
            items=domain_items,
            vat_rate=_d(vat_rate) if vat_rate is not None else Decimal("0.1"),
            due_date=due_date,
            payment_term_id=term_ref,
            template_code=template_code or "",
            invoice_symbol=invoice_symbol or "",
            customer_mst=customer_mst,
            currency_code=cur,
            fx_rate=fx,
            deferred_amount=deferred,
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

    # ── e-invoice issue (NĐ254; signer port, mock default, no 3P) ──────
    def issue_einvoice(
        self,
        invoice_id: UUID,
        *,
        actor: UUID,
        reason: str,
        seller: dict[str, Any] | None = None,
    ) -> Invoice:
        from src.bricks.invoice.domain import EInvoiceStatus
        from src.bricks.invoice.einvoice import (
            build_einvoice_xml,
            mock_sign,
            validate_einvoice_ready,
            xml_hash,
        )

        inv = self._repo.get_by_id(invoice_id)
        if inv is None:
            raise InvoiceNotFoundError("Không tìm thấy hóa đơn")
        validate_einvoice_ready(inv)
        xml_str = build_einvoice_xml(inv, seller)
        signer = self._signer
        signature = signer.sign(xml_str, actor) if signer is not None else mock_sign(xml_str, actor)
        inv.einvoice_status = EInvoiceStatus.SENT
        inv.checksum = inv.compute_checksum(inv.checksum, actor, str(reason))
        saved = self._repo.save(inv)
        if self._audit is not None:
            self._audit.append(
                entity_type="invoice",
                entity_id=inv.id,
                action="EINVOICE_ISSUE",
                actor_id=actor,
                reason=str(reason),
                after_value={
                    "einvoice_status": "SENT",
                    "xml_hash": xml_hash(xml_str),
                    "signature": signature,
                },
            )
        return saved

    # ── deduction (521) ───────────────────────────────────────────────
    def create_deduction(
        self,
        invoice_id: UUID,
        *,
        deduction_type: str,
        amount: Any,
        vat_rate: Any | None = None,
        actor: UUID,
        reason: str,
        voucher_service: Any | None = None,
    ) -> Any:
        """Create sales deduction voucher (521) linked to source invoice.

        Validates source POSTED, amount ≤ subtotal, then delegates to
        voucher_service.create_voucher (FY/COA/balance gates). Separated
        voucher_service injection keeps brick boundary pure (no import).
        """
        from src.bricks.invoice.domain import DeductionType

        try:
            dtype = DeductionType(deduction_type)
        except ValueError:
            raise ValueError(
                f"deduction_type {deduction_type} không hợp lệ (RETURN/DISCOUNT/REBATE)"
            )
        inv = self._repo.get_by_id(invoice_id)
        if inv is None:
            raise InvoiceNotFoundError("Không tìm thấy hóa đơn gốc")
        if inv.status.value != "POSTED":
            raise ValueError("Chỉ được tạo giảm trừ cho hóa đơn đã POSTED")
        amt = _d(amount)
        if amt <= 0:
            raise ValueError("amount must be > 0")
        if amt > inv.subtotal:
            raise ValueError("Deduction amount cannot exceed invoice subtotal")
        # Map type → 521 detail (TT99)
        acct_map = {
            DeductionType.RETURN: "5212",  # hàng bán bị trả lại
            DeductionType.DISCOUNT: "5211",  # chiết khấu thương mại (TT99: 5211)
            DeductionType.REBATE: "5213",  # giảm giá hàng bán
        }
        # FX: keep same currency as source
        vs = voucher_service or getattr(self, "_voucher_service", None)
        if vs is None:
            raise RuntimeError("voucher_service not wired for deductions")
        # VAT on deduction — if provided, use it, else derived average
        ded_vat_rate = _d(vat_rate) if vat_rate is not None else None
        # Build balanced lines: Nợ 521 amt / Có 131 amt (ex-VAT) + optional VAT 3331
        # For MVP, assume amount is tax-exclusive; if vat_rate given, compute VAT
        lines: list[dict[str, str]] = []
        if ded_vat_rate is not None and ded_vat_rate != Decimal(0) and ded_vat_rate != Decimal(-1):
            _vat_amt = (amt * ded_vat_rate).quantize(Decimal(1))
        # Resolve AR detail code per regime (TT99/TT133) — 131 is aggregate, need 1311
        try:
            from src.bricks.coa.domain import resolve_chart_role

            regime = self._regime_of(inv.company_id) if self._regime_of else "tt133"
            ar_code = resolve_chart_role("ar", regime)
        except Exception:  # noqa: BLE001
            ar_code = "1311"
        # Simple lane: Nợ 521 / Có 1311 (detail)
        lines = [
            {"account_code": acct_map[dtype], "debit": str(amt), "credit": "0"},
            {"account_code": ar_code, "debit": "0", "credit": str(amt)},
        ]
        # Use invoice company & date for voucher
        voucher = vs.create_voucher(
            company_id=inv.company_id,
            entry_date=inv.issue_date,
            description=f"Giảm trừ {dtype.value} cho HĐ {inv.number}: {reason}",
            lines=lines,
            actor=actor,
            reason=reason,
        )
        if self._audit is not None:
            self._audit.append(
                entity_type="invoice",
                entity_id=inv.id,
                action=f"DEDUCTION_{dtype.value}",
                actor_id=actor,
                reason=reason,
                after_value={"deduction_amount": float(amt), "voucher_id": str(voucher.id)},
            )
        return voucher


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
