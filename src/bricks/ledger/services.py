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
    def __init__(self, *, source: Any) -> None:
        self._source = source

    # ── Sổ nhật ký chung ────────────────────────────────────────────────
    def general_journal(self, company_id: UUID, start: date, end: date) -> list[dict[str, Any]]:
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

        out: list[dict[str, Any]] = []
        for key in sorted(order):
            e = dict(grouped[key])
            e.pop("voucher_id")
            out.append(e)
        return out

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
