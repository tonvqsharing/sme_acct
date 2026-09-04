"""Ledger reports — Sổ nhật ký chung + Bảng cân đối số phát sinh.

Reads only POSTED voucher lines via port. Primitives in/out.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

ZERO = Decimal(0)


class LedgerService:
    def __init__(self, *, source: Any, opening_balances: Any | None = None) -> None:
        self._source = source
        self._opening_balances = opening_balances

    # ── Sổ nhật ký chung ────────────────────────────────────────────────
    def general_journal(
        self, company_id: UUID, start: date, end: date, *, page: int = 1, page_size: int = 50
    ) -> list[dict[str, Any]]:
        # pagination guard (Misa/Fast/Bravo parity: max 200, default 50)
        page = max(1, int(page))
        page_size = min(200, max(1, int(page_size)))
        rows = self._source.get_posted_lines(company_id, start, end)
        grouped: dict[str, dict[str, Any]] = {}
        order: list[str] = []
        for r in rows:
            key = f"{r['entry_date']}|{r['number']}"
            if key not in grouped:
                grouped[key] = {
                    "voucher_id": r["voucher_id"],
                    "number": r["number"],
                    "entry_date": r["entry_date"],
                    "description": r["description"],
                    "lines": [],
                    "total_debit": ZERO,
                }
                order.append(key)
            grouped[key]["lines"].append(
                {
                    "account_code": r["account_code"],
                    "debit": r["debit"],
                    "credit": r["credit"],
                }
            )
            grouped[key]["total_debit"] += r["debit"]

        sorted_keys = sorted(order)
        # paginate on grouped entries (journal entries, not lines)
        start_idx = (page - 1) * page_size
        paged_keys = sorted_keys[start_idx : start_idx + page_size]
        out: list[dict[str, Any]] = []
        for key in paged_keys:
            e = dict(grouped[key])
            e.pop("voucher_id")
            out.append(e)
        return out

    def ar_aging(self, company_id: UUID, as_of: date) -> list[dict[str, Any]]:
        """AR aging buckets for 131 — reads posted voucher AR lines.
        Buckets: current, 1-30, 31-60, 61-90, 90+.
        """

        rows = self._source.get_posted_lines(company_id, date(2000, 1, 1), as_of)
        # aggregate per voucher by entry_date for aging
        buckets = {"current": ZERO, "1-30": ZERO, "31-60": ZERO, "61-90": ZERO, "90+": ZERO}
        # simplistic: sum net AR per entry age
        for r in rows:
            if r["account_code"] not in ("131", "1311"):
                continue
            ed = r["entry_date"]
            if isinstance(ed, str):
                from datetime import date as _d

                ed = _d.fromisoformat(ed)
            age = (as_of - ed).days if hasattr(ed, "__sub__") else 0
            net = r["debit"] - r["credit"]
            if age <= 0:
                buckets["current"] += net
            elif age <= 30:
                buckets["1-30"] += net
            elif age <= 60:
                buckets["31-60"] += net
            elif age <= 90:
                buckets["61-90"] += net
            else:
                buckets["90+"] += net
        # opening balances (locked batches) age as current
        if self._opening_balances is not None:
            for o in self._opening_balances(company_id):
                if o["account_code"] not in ("131", "1311"):
                    continue
                signed = o["amount"] if o["side"] == "debit" else -o["amount"]
                buckets["current"] += signed
        return [{"bucket": k, "amount": v} for k, v in buckets.items()]

    # ── Bảng cân đối số phát sinh ───────────────────────────────────────
    def trial_balance(self, company_id: UUID, start: date, end: date) -> list[dict[str, Any]]:
        rows: Iterable[dict[str, Any]] = self._source.get_posted_lines(company_id, start, end)
        agg: dict[str, dict[str, Decimal]] = {}
        for r in rows:
            acct = r["account_code"]
            slot = agg.setdefault(acct, {"debit": ZERO, "credit": ZERO})
            slot["debit"] += r["debit"]
            slot["credit"] += r["credit"]

        result = []
        for code in sorted(agg):
            d, c = agg[code]["debit"], agg[code]["credit"]
            result.append(
                {
                    "account_code": code,
                    "debit": d,
                    "credit": c,
                    "net_debit": d - c,
                }
            )
        return result
