"""ExchangeRateService — rate maintenance + booking rate resolution.

Clean Architecture: depends only on repository ports + domain entities.
Docs: specs-currencies.md §3, §7; rules R1/D5 (bình quân gia quyền).
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from src.application.ports import CurrencyRepositoryPort, ExchangeRateRepositoryPort
from src.domain.entities.base import PostingSide, RateType
from src.domain.entities.currency import ExchangeRate
from src.domain.exceptions import (
    CurrencyNotFoundError,
    FXImportError,
    InvalidRateError,
    RateNotFoundError,
)

logger = logging.getLogger(__name__)


class ExchangeRateService:
    """Orchestrates exchange rate lifecycle and booking-rate resolution."""

    def __init__(
        self,
        rate_repo: ExchangeRateRepositoryPort,
        currency_repo: CurrencyRepositoryPort,
    ) -> None:
        self._rate_repo = rate_repo
        self._currency_repo = currency_repo

    # ── Rate maintenance ───────────────────────────────────────────────────

    def create_rate(
        self,
        currency_code: str,
        rate_date: date,
        rate_type: RateType,
        rate: Decimal | str,
        source: str,
        actor: UUID,
        note: str | None = None,
    ) -> ExchangeRate:
        """Insert a new rate row (append-only, D3). Validates currency exists."""
        if not self._currency_repo.exists(currency_code):
            raise CurrencyNotFoundError(
                f"Tiền tệ '{currency_code}' chưa được cấu hình trong danh mục"
            )
        rate_value = Decimal(rate)
        if rate_value <= 0:
            raise InvalidRateError("Tỷ giá phải > 0")
        exchange_rate = ExchangeRate(
            currency_code=currency_code,
            rate_date=rate_date,
            rate_type=rate_type,
            rate=rate_value,
            source=source,
            actor=actor,
            note=note,
        )
        return self._rate_repo.create(exchange_rate)

    def list_history(
        self,
        currency_code: str | None = None,
        rate_type: RateType | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[ExchangeRate]:
        return self._rate_repo.list_history(currency_code, rate_type, from_date, to_date)

    # ── Booking rate resolution (R1, D5) ───────────────────────────────────

    def resolve_booking_rate(
        self,
        entry_side: PostingSide,
        currency_code: str,
        rate_date: date,
        actual_rate: Decimal | None = None,
        open_fx_balance: list[tuple[Decimal, Decimal]] | None = None,
        rate_type: RateType = RateType.BUY,
    ) -> Decimal:
        """Resolve booking rate per TT 99/2025 (R1).

        Nợ (debit): tỷ giá giao dịch thực tế (actual) — else last rate ≤ date.
        Có (credit): bình quân gia quyền Σ(amt×rate)/Σ(amt) over open FX
            balance of the account (D5) — else actual/last rate.
        """
        if entry_side == PostingSide.CREDIT and open_fx_balance:
            total_original = sum((amt for amt, _ in open_fx_balance), Decimal("0"))
            if total_original > 0:
                weighted = (
                    sum((amt * r for amt, r in open_fx_balance), Decimal("0")) / total_original
                )
                return weighted

        if actual_rate is not None:
            return Decimal(actual_rate)

        latest = self._rate_repo.get_latest(currency_code, rate_type, rate_date)
        if latest is None:
            raise RateNotFoundError(
                f"Không có tỷ giá {rate_type.value} cho {currency_code} tại ngày {rate_date}"
            )
        return latest.rate

    # ── CSV import (specs §7) ──────────────────────────────────────────────

    def import_csv(self, content: str, actor: UUID) -> dict:
        """Import rates from CSV. Atomic by default: all-or-nothing (specs §7).

        Any row error → FXImportError, nothing imported.
        Returns {"imported": n, "errors": []}.
        """
        rows = self._parse_csv(content)
        errors: list[dict] = []
        for i, row in enumerate(rows, start=2):  # row 1 = header
            error = self._validate_row(row)
            if error:
                errors.append({"row": i, "error": error})

        if errors:
            raise FXImportError(
                f"CSV không hợp lệ: {len(errors)} lỗi — không import dòng nào (atomic)"
            )

        imported = 0
        for row in rows:
            self.create_rate(
                currency_code=row["currency"],
                rate_date=date.fromisoformat(row["rate_date"]),
                rate_type=RateType(row["rate_type"].lower()),
                rate=row["rate"],
                source=row.get("source") or "CSV_IMPORT",
                actor=actor,
                note=row.get("note"),
            )
            imported += 1
        return {"imported": imported, "errors": []}

    def _parse_csv(self, content: str) -> list[dict]:
        reader = csv.DictReader(io.StringIO(content))
        rows = []
        for raw in reader:
            rows.append({k.strip(): (v.strip() if v else "") for k, v in raw.items()})
        return rows

    def _validate_row(self, row: dict) -> str | None:
        """Validate one CSV row per specs §7. Returns error message or None."""
        try:
            date.fromisoformat(row.get("rate_date", ""))
        except (ValueError, TypeError):
            return f"rate_date '{row.get('rate_date')}' không hợp lệ (YYYY-MM-DD)"
        currency = row.get("currency", "")
        if len(currency) != 3 or not currency.isalpha() or not currency.isupper():
            return f"currency '{currency}' không hợp lệ (ISO 4217, 3 chữ hoa)"
        if not self._currency_repo.exists(currency):
            return f"currency '{currency}' chưa được cấu hình"
        try:
            RateType(row.get("rate_type", "").lower())
        except ValueError:
            return f"rate_type '{row.get('rate_type')}' không hợp lệ"
        try:
            rate = Decimal(row.get("rate", ""))
            if rate <= 0:
                return "rate phải > 0"
        except Exception:
            return f"rate '{row.get('rate')}' không phải số"
        return None
