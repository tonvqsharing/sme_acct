"""Opening balance service — batch lifecycle + trial gate + voucher guard."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from src.bricks.opening_balance.domain import (
    GENESIS_CHECKSUM,
    TOLERANCE,
    AssetOpening,
    BankOpening,
    BatchSource,
    BatchState,
    CounterpartyBalance,
    GLBalance,
    OpeningBatch,
    StockOpening,
)


class BatchLockedError(Exception):
    pass


class UnbalancedOpeningError(Exception):
    pass


class NotFoundError(Exception):
    pass


def _d(v: Any) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


class OpeningService:
    def __init__(
        self,
        *,
        repo: Any,
        fy_years: Any,
        coa: Any,
        regime_of: Any | None = None,
        audit: Any | None = None,
        party_lookup: Any | None = None,
        inventory: Any | None = None,
        fixed_assets: Any | None = None,
        ccdc: Any | None = None,
    ) -> None:
        self._repo = repo
        self._fy_years = fy_years
        self._coa = coa
        self._regime_of = regime_of
        self._audit = audit
        self._party_lookup = party_lookup
        self._inventory = inventory
        self._fixed_assets = fixed_assets
        self._ccdc = ccdc

    # ── helpers ───────────────────────────────────────────────────────
    def _regime(self, company_id: UUID) -> str:
        return self._regime_of(company_id) if self._regime_of else "tt133"

    def _log(self, action: str, entity_id: UUID, actor: UUID, reason: str) -> None:
        if self._audit is not None:
            self._audit.append(
                entity_type="opening_batch",
                entity_id=entity_id,
                action=action,
                actor_id=actor,
                reason=reason,
                after_value=None,
            )

    def _get_draft(self, batch_id: UUID) -> OpeningBatch:
        b = self._repo.get_batch(batch_id)
        if b is None:
            raise NotFoundError("Không tìm thấy batch số dư đầu kỳ")
        assert isinstance(b, OpeningBatch)
        if b.state != BatchState.DRAFT:
            raise BatchLockedError("Batch is LOCKED")
        return b

    # ── batch ─────────────────────────────────────────────────────────
    def create_batch(
        self,
        *,
        company_id: UUID,
        fiscal_year_id: UUID,
        source: str = "MANUAL",
        actor: UUID,
        reason: str,
    ) -> OpeningBatch:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        fy = self._fy_years.get_by_id(fiscal_year_id)
        if fy is None or fy.company_id != company_id:
            raise NotFoundError("fiscal year not found in company")
        try:
            src = BatchSource(source)
        except ValueError:
            raise ValueError(f"source {source} invalid (MANUAL/EXCEL/YEAR_ROLL)")
        b = OpeningBatch(company_id=company_id, fiscal_year_id=fiscal_year_id, source=src)
        b.checksum = b.compute_checksum(GENESIS_CHECKSUM, actor, reason)
        self._repo.create_batch(b)
        self._log("CREATE", b.id, actor, reason)
        return b

    # ── rows ──────────────────────────────────────────────────────────
    def post_gl(
        self, batch_id: UUID, *, lines: list[dict[str, Any]], actor: UUID, reason: str
    ) -> None:
        b = self._get_draft(batch_id)
        regime = self._regime(b.company_id)
        for ln in lines:
            self._coa.validate_posting_account(b.company_id, ln["account_code"], regime)
            row = GLBalance(
                batch_id=b.id,
                account_code=ln["account_code"],
                debit=_d(ln.get("debit", "0") or "0"),
                credit=_d(ln.get("credit", "0") or "0"),
                currency_code=ln.get("currency_code", "VND"),
            )
            self._repo.add_gl(row)
        b.checksum = b.compute_checksum(b.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_batch(b)
        self._log("POST_GL", b.id, actor, reason)

    def post_bank(
        self, batch_id: UUID, *, rows: list[dict[str, Any]], actor: UUID, reason: str
    ) -> None:
        b = self._get_draft(batch_id)
        for r in rows:
            row = BankOpening(
                batch_id=b.id,
                bank_account_id=UUID(str(r["bank_account_id"])),
                amount=_d(r["amount"]),
            )
            self._repo.add_bank(row)
        b.checksum = b.compute_checksum(b.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_batch(b)
        self._log("POST_BANK", b.id, actor, reason)

    def post_counterparty(
        self, batch_id: UUID, *, rows: list[dict[str, Any]], actor: UUID, reason: str
    ) -> None:
        b = self._get_draft(batch_id)
        regime = self._regime(b.company_id)
        for r in rows:
            self._coa.validate_posting_account(b.company_id, r["account_code"], regime)
            pid = UUID(str(r["party_id"]))
            party = self._party_lookup(pid) if self._party_lookup is not None else None
            if party is None:
                raise NotFoundError(f"Không tìm thấy đối tác {r['party_id']}")
            if party.company_id != b.company_id:
                raise ValueError("Đối tác không thuộc công ty")
            if not party.active:
                raise ValueError("Đối tác đã ngừng hoạt động")
            row = CounterpartyBalance(
                batch_id=b.id,
                account_code=r["account_code"],
                party_id=pid,
                side=r.get("side", "debit"),
                amount=_d(r["amount"]),
                proof=bool(r.get("proof", False)),
            )
            self._repo.add_counterparty(row)
        b.checksum = b.compute_checksum(b.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_batch(b)
        self._log("POST_COUNTERPARTY", b.id, actor, reason)

    def post_stock(
        self, batch_id: UUID, *, rows: list[dict[str, Any]], actor: UUID, reason: str
    ) -> None:
        from datetime import date as _date

        b = self._get_draft(batch_id)
        if self._inventory is None:
            raise RuntimeError("inventory port not wired")
        for r in rows:
            pid = UUID(str(r["product_id"]))
            wid = UUID(str(r["warehouse_id"]))
            qty = _d(r["qty"])
            value = _d(r["total_value"])
            if qty <= 0:
                raise ValueError("qty must be > 0")
            if value < 0:
                raise ValueError("total_value must be >= 0")
            prod = self._inventory.get_product(pid)
            if prod is None or prod.company_id != b.company_id:
                raise NotFoundError(f"Không tìm thấy vật tư {r['product_id']}")
            if not prod.active:
                raise ValueError(f"Vật tư {prod.code} ngừng hoạt động")
            loc = self._inventory.get_location(wid)
            if loc is None or loc.company_id != b.company_id:
                raise NotFoundError(f"Không tìm thấy kho {r['warehouse_id']}")
            method = r.get("cost_method") or prod.cost_method.value
            if method in ("fifo", "specific") and (
                not r.get("receipt_date") or r.get("unit_cost") is None
            ):
                raise ValueError("FIFO/specific rows need receipt_date and unit_cost")
            unit = (
                _d(r["unit_cost"])
                if r.get("unit_cost") is not None
                else (value / qty if qty != 0 else Decimal(0))
            )
            row = StockOpening(
                batch_id=b.id,
                product_id=pid,
                warehouse_id=wid,
                qty=qty,
                total_value=value,
                lot_code=r.get("lot_code"),
                expiry_date=(
                    _date.fromisoformat(r["expiry_date"]) if r.get("expiry_date") else None
                ),
                receipt_date=(
                    _date.fromisoformat(r["receipt_date"]) if r.get("receipt_date") else None
                ),
                receipt_doc=r.get("receipt_doc"),
                unit_cost=unit,
            )
            self._repo.add_stock(row)
            self._inventory.post_opening_move(
                company_id=b.company_id,
                product_id=pid,
                location_id=wid,
                qty=qty,
                unit_cost=unit,
                effective_date=r.get("effective_date") or _date.today(),  # noqa: DTZ011
                actor=actor,
                reason=reason,
            )
        b.checksum = b.compute_checksum(b.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_batch(b)
        self._log("POST_STOCK", b.id, actor, reason)

    def post_assets(
        self, batch_id: UUID, *, rows: list[dict[str, Any]], actor: UUID, reason: str
    ) -> None:
        from datetime import date as _date

        b = self._get_draft(batch_id)
        for r in rows:
            kind = r.get("kind", "fixed_asset")
            if kind not in ("fixed_asset", "ccdc"):
                raise ValueError(f"kind must be fixed_asset|ccdc, got {kind}")
            original = _d(r["original_cost"])
            remaining = _d(r["remaining_value"])
            months_left = int(r["months_left"])
            regime = self._regime(b.company_id)
            row = AssetOpening(
                batch_id=b.id,
                kind=kind,
                code=str(r["code"]).strip(),
                name=str(r["name"]).strip(),
                original_cost=original,
                remaining_value=remaining,
                months_left=months_left,
                expense_account=r["expense_account"],
            )
            self._repo.add_asset(row)
            acquired = (
                _date.fromisoformat(r["acquisition_date"])
                if r.get("acquisition_date")
                else _date.today()  # noqa: DTZ011
            )
            if kind == "ccdc":
                if self._ccdc is None:
                    raise RuntimeError("ccdc port not wired")
                life = int(r.get("useful_life_months", months_left))
                self._ccdc.open_ccdc_with_history(
                    company_id=b.company_id,
                    code=row.code,
                    name=row.name,
                    category=r.get("category", "Khác"),
                    purchase_date=(
                        _date.fromisoformat(r["purchase_date"])
                        if r.get("purchase_date")
                        else acquired
                    ),
                    purchase_price=original,
                    useful_life_months=life,
                    expense_account_code=row.expense_account,
                    actor_id=actor,
                    remaining_value=remaining,
                    months_left=months_left,
                )
                continue
            if self._fixed_assets is None:
                raise RuntimeError("fixed_assets port not wired")
            self._coa.validate_posting_account(b.company_id, row.expense_account, regime)
            # Materialize asset at go-live with prior depreciation carried over.
            # Useful life unknown from book state alone: effective life =
            # max(declared useful_life, months_left) so SL never over-charges.
            life = max(int(r.get("useful_life_months", months_left)), months_left)
            self._fixed_assets.create_asset(
                company_id=b.company_id,
                asset_code=row.code,
                name=row.name,
                category=r.get("category", "huu_hinh"),
                original_cost=original,
                acquisition_date=acquired,
                useful_life_months=life,
                depreciation_account=row.expense_account,
                actor=actor,
                reason=reason,
                accumulated_depreciation=original - remaining,
            )
        b.checksum = b.compute_checksum(b.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_batch(b)
        self._log("POST_ASSETS", b.id, actor, reason)

    # ── reconcile + lock ──────────────────────────────────────────────
    def reconcile(self, batch_id: UUID) -> dict[str, Any]:
        b = self._repo.get_batch(batch_id)
        if b is None:
            raise NotFoundError("Không tìm thấy batch số dư đầu kỳ")
        gl = self._repo.list_gl(batch_id)
        debit = sum((r.debit for r in gl), Decimal(0))
        credit = sum((r.credit for r in gl), Decimal(0))
        bank = self._repo.list_bank(batch_id)
        bank_total = sum((r.amount for r in bank), Decimal(0))
        cp = self._repo.list_counterparty(batch_id)
        cp_total = sum((r.amount for r in cp), Decimal(0))
        stock = self._repo.list_stock(batch_id)
        stock_total = sum((r.total_value for r in stock), Decimal(0))
        assets = self._repo.list_assets(batch_id)
        assets_total = sum((r.remaining_value for r in assets), Decimal(0))
        fa_total = sum((r.remaining_value for r in assets if r.kind == "fixed_asset"), Decimal(0))
        ccdc_total = sum((r.remaining_value for r in assets if r.kind == "ccdc"), Decimal(0))
        gl_112 = sum(
            (r.debit - r.credit for r in gl if r.account_code.startswith("112")),
            Decimal(0),
        )
        gl_fa_net = sum(
            (r.debit - r.credit for r in gl if r.account_code.startswith(("211", "214"))),
            Decimal(0),
        )
        gl_242 = sum(
            (r.debit - r.credit for r in gl if r.account_code.startswith("242")),
            Decimal(0),
        )
        balanced = abs(debit - credit) <= TOLERANCE
        return {
            "balanced": balanced,
            "debit_total": debit,
            "credit_total": credit,
            "checks": {
                "bank_total": bank_total,
                "bank_gl_112": gl_112,
                "gl_lines": len(gl),
                "counterparty_total": cp_total,
                "counterparty_lines": len(cp),
                "stock_total": stock_total,
                "stock_lines": len(stock),
                "assets_total": assets_total,
                "assets_lines": len(assets),
                "fa_total": fa_total,
                "fa_gl_net": gl_fa_net,
                "ccdc_total": ccdc_total,
                "gl_242": gl_242,
            },
        }

    def ar_opening_lines(self, company_id: UUID) -> list[dict[str, Any]]:
        """Primitives for ledger AR aging: locked batches' 131 rows as current."""
        out: list[dict[str, Any]] = []
        for b in self._repo.list_batches(company_id):
            if b.state != BatchState.LOCKED:
                continue
            for r in self._repo.list_counterparty(b.id):
                if r.account_code not in ("131", "1311"):
                    continue
                out.append(
                    {
                        "account_code": r.account_code,
                        "side": r.side,
                        "amount": r.amount,
                    }
                )
        return out

    def _verify_stock_tie(self, batch_id: UUID) -> None:
        """R-O02: SKU detail must tie to GL per warehouse account."""
        if self._inventory is None:
            return
        gl_net: dict[str, Decimal] = {}
        for r in self._repo.list_gl(batch_id):
            gl_net[r.account_code] = gl_net.get(r.account_code, Decimal(0)) + r.debit - r.credit
        stock_net: dict[str, Decimal] = {}
        for r in self._repo.list_stock(batch_id):
            prod = self._inventory.get_product(r.product_id)
            if prod is None or prod.category_id is None:
                continue
            cat = self._inventory.get_category(prod.category_id)
            if cat is None or not cat.account_code:
                continue
            stock_net[cat.account_code] = (
                stock_net.get(cat.account_code, Decimal(0)) + r.total_value
            )
        for acct, total in stock_net.items():
            if abs(total - gl_net.get(acct, Decimal(0))) > TOLERANCE:
                raise UnbalancedOpeningError(
                    f"Tồn kho {acct} {total} ≠ sổ cái {gl_net.get(acct, Decimal(0))}"
                )

    def _verify_counterparty_tie(self, batch_id: UUID) -> None:
        """R-O03: counterparty detail must tie to GL per account."""
        gl_net: dict[str, Decimal] = {}
        for r in self._repo.list_gl(batch_id):
            gl_net[r.account_code] = gl_net.get(r.account_code, Decimal(0)) + r.debit - r.credit
        cp_net: dict[str, Decimal] = {}
        for r in self._repo.list_counterparty(batch_id):
            signed = r.amount if r.side == "debit" else -r.amount
            cp_net[r.account_code] = cp_net.get(r.account_code, Decimal(0)) + signed
        for acct, total in cp_net.items():
            if abs(total - gl_net.get(acct, Decimal(0))) > TOLERANCE:
                raise UnbalancedOpeningError(
                    f"Chi tiết đối tác {acct} {total} ≠ sổ cái {gl_net.get(acct, Decimal(0))}"
                )

    def _verify_bank_tie(self, batch_id: UUID) -> None:
        """Bank detail must tie to GL 112x debit."""
        gl_112 = sum(
            (
                r.debit - r.credit
                for r in self._repo.list_gl(batch_id)
                if r.account_code.startswith("112")
            ),
            Decimal(0),
        )
        bank_total = sum((r.amount for r in self._repo.list_bank(batch_id)), Decimal(0))
        if abs(bank_total - gl_112) > TOLERANCE:
            raise UnbalancedOpeningError(f"Chi tiết ngân hàng 112 {bank_total} ≠ sổ cái {gl_112}")

    def _verify_asset_tie(self, batch_id: UUID) -> None:
        """R-O04: FA remaining (NG−HK) ↔ GL 211−214; CCDC remaining ↔ GL 242."""
        gl = self._repo.list_gl(batch_id)
        assets = self._repo.list_assets(batch_id)
        gl_fa = sum(
            (r.debit - r.credit for r in gl if r.account_code.startswith(("211", "214"))),
            Decimal(0),
        )
        fa_total = sum((r.remaining_value for r in assets if r.kind == "fixed_asset"), Decimal(0))
        if (fa_total != 0 or gl_fa != 0) and abs(fa_total - gl_fa) > TOLERANCE:
            raise UnbalancedOpeningError(f"GTCL TSCĐ 211 {fa_total} ≠ sổ cái {gl_fa}")
        gl_242 = sum(
            (r.debit - r.credit for r in gl if r.account_code.startswith("242")),
            Decimal(0),
        )
        ccdc_total = sum((r.remaining_value for r in assets if r.kind == "ccdc"), Decimal(0))
        if (ccdc_total != 0 or gl_242 != 0) and abs(ccdc_total - gl_242) > TOLERANCE:
            raise UnbalancedOpeningError(f"GTCL CCDC 242 {ccdc_total} ≠ sổ cái {gl_242}")

    def lock(self, batch_id: UUID, *, actor: UUID, reason: str) -> OpeningBatch:
        b = self._get_draft(batch_id)
        rep = self.reconcile(batch_id)
        if not rep["balanced"]:
            raise UnbalancedOpeningError(f"Nợ {rep['debit_total']} ≠ Có {rep['credit_total']}")
        self._verify_counterparty_tie(batch_id)
        self._verify_stock_tie(batch_id)
        self._verify_bank_tie(batch_id)
        self._verify_asset_tie(batch_id)
        b.state = BatchState.LOCKED
        b.checksum = b.compute_checksum(b.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_batch(b)
        self._log("LOCK", b.id, actor, reason)
        return b

    def reopen(
        self, batch_id: UUID, *, actor: UUID, reason: str, is_chief: bool = False
    ) -> OpeningBatch:
        if not is_chief:
            raise PermissionError("Only CHIEF_ACCOUNTANT can reopen")
        b = self._repo.get_batch(batch_id)
        if b is None:
            raise NotFoundError("Không tìm thấy batch số dư đầu kỳ")
        assert isinstance(b, OpeningBatch)
        b.state = BatchState.DRAFT
        b.checksum = b.compute_checksum(b.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_batch(b)
        self._log("REOPEN", b.id, actor, reason)
        return b

    def rollover(
        self, batch_id: UUID, *, new_fiscal_year_id: UUID, actor: UUID, reason: str
    ) -> OpeningBatch:
        """Year-roll: copy a LOCKED batch's rows into a fresh DRAFT batch.

        Row data only — masters (FA/CCDC/products) already went live, so no
        materialization re-runs. New row IDs to keep audit chains distinct.
        """
        src = self._repo.get_batch(batch_id)
        if src is None:
            raise NotFoundError("Không tìm thấy batch số dư đầu kỳ")
        assert isinstance(src, OpeningBatch)
        if src.state != BatchState.LOCKED:
            raise BatchLockedError("Only LOCKED batches roll over")
        fy = self._fy_years.get_by_id(new_fiscal_year_id)
        if fy is None or fy.company_id != src.company_id:
            raise NotFoundError("Năm tài chính mới không thuộc công ty")
        dest = self.create_batch(
            company_id=src.company_id,
            fiscal_year_id=new_fiscal_year_id,
            source=src.source.value,
            actor=actor,
            reason=reason,
        )
        for r in self._repo.list_gl(batch_id):
            self._repo.add_gl(
                GLBalance(
                    id=uuid4(),
                    batch_id=dest.id,
                    account_code=r.account_code,
                    debit=r.debit,
                    credit=r.credit,
                    currency_code=r.currency_code,
                )
            )
        for r in self._repo.list_bank(batch_id):
            self._repo.add_bank(
                BankOpening(
                    id=uuid4(), batch_id=dest.id, bank_account_id=r.bank_account_id, amount=r.amount
                )
            )
        for r in self._repo.list_counterparty(batch_id):
            self._repo.add_counterparty(
                CounterpartyBalance(
                    id=uuid4(),
                    batch_id=dest.id,
                    account_code=r.account_code,
                    party_id=r.party_id,
                    side=r.side,
                    amount=r.amount,
                    proof=r.proof,
                )
            )
        for r in self._repo.list_stock(batch_id):
            self._repo.add_stock(
                StockOpening(
                    id=uuid4(),
                    batch_id=dest.id,
                    product_id=r.product_id,
                    warehouse_id=r.warehouse_id,
                    qty=r.qty,
                    total_value=r.total_value,
                    lot_code=r.lot_code,
                    expiry_date=r.expiry_date,
                    receipt_date=r.receipt_date,
                    receipt_doc=r.receipt_doc,
                    unit_cost=r.unit_cost,
                )
            )
        for r in self._repo.list_assets(batch_id):
            self._repo.add_asset(
                AssetOpening(
                    id=uuid4(),
                    batch_id=dest.id,
                    kind=r.kind,
                    code=r.code,
                    name=r.name,
                    original_cost=r.original_cost,
                    remaining_value=r.remaining_value,
                    months_left=r.months_left,
                    expense_account=r.expense_account,
                )
            )
        self._log("ROLLOVER", dest.id, actor, reason)
        return dest

    def is_locked(self, company_id: UUID) -> bool | None:
        """Voucher gate: None = no batches (skip); True only when every batch LOCKED."""
        batches = self._repo.list_batches(company_id)
        if not batches:
            return None
        return all(b.state == BatchState.LOCKED for b in batches)
