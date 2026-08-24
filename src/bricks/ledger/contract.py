"""Ledger source port — reads flattened posted voucher lines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any
from uuid import UUID


class LedgerSourcePort(ABC):
    @abstractmethod
    def get_posted_lines(self, company_id: UUID, start: date, end: date) -> list[dict[str, Any]]:
        """Flat rows: voucher_id, number, entry_date (ISO str),
        description, account_code, debit, credit — POSTED only."""
        ...
