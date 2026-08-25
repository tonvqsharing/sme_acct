"""Date-effective tax-rate windows — law events as data.

Base rates are statute (Luật Thuế GTGT 2024); reduced rates arrive via
decrees carrying validity windows. Storing windows lets validation gates
resolve by DOCUMENT DATE, so retroactive entries stay legal without code
changes and sunset automatically at decree expiry.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

VAT_REDUCTION_END = date(2026, 12, 31)  # NĐ 174/2025/NĐ-CP sunset


@dataclass(frozen=True)
class TaxRateWindow:
    """One lawful rate valid within [valid_from, valid_to] (None = open)."""

    rate_pct: int
    fraction: str
    valid_from: date | None
    valid_to: date | None
    decree_ref: str

    def covers(self, on: date) -> bool:
        if self.valid_from is not None and on < self.valid_from:
            return False
        return not (self.valid_to is not None and on > self.valid_to)


SEED_TAX_RATE_WINDOWS: tuple[TaxRateWindow, ...] = (
    TaxRateWindow(0, "0", None, None, "Luật Thuế GTGT 2024"),
    TaxRateWindow(5, "0.05", None, None, "Luật Thuế GTGT 2024"),
    TaxRateWindow(10, "0.1", None, None, "Luật Thuế GTGT 2024"),
    TaxRateWindow(
        8,
        "0.08",
        date(2025, 7, 1),
        VAT_REDUCTION_END,
        "NQ 204/2025/QH15 + NĐ 174/2025/NĐ-CP",
    ),
)


def make_rate_gate(
    windows: tuple[TaxRateWindow, ...] = SEED_TAX_RATE_WINDOWS,
) -> Any:
    """Factory for the injection seam used by invoice/purchase services.

    Returns callable(fraction: str, on_date: date) -> True, raising
    ValueError with a law citation on violation. Unknown fractions pass
    (the static catalog check upstream already rejects them).
    """

    def gate(fraction: str, on_date: date) -> bool:
        known = [w for w in windows if w.fraction == fraction]
        if any(w.covers(on_date) for w in known):
            return True
        if known:
            expired = next(w for w in known if w.valid_to is not None)
            raise ValueError(
                f"Thuế suất {fraction} đã hết hiệu lực từ "
                f"{expired.valid_to} theo {expired.decree_ref}; "
                "kiểm tra văn bản thay thế."
            )
        if any(
            w.valid_from is not None and on_date < w.valid_from
            for w in windows
            if w.fraction == fraction
        ):
            raise ValueError(f"Thuế suất {fraction} chưa có hiệu lực")
        return True

    return gate
