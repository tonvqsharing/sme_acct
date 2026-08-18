"""RevaluationService — period-end FX revaluation.

Clean Architecture: depends only on repository ports + domain entities.
Docs: specs-currencies.md §4, rules R2/R3/D6-D9.

Algorithm (spec §4):
1. Guard: period unlocked (D8) else PeriodLockedError.
2. Closing rate = TRANSFER rate ≤ rate_date (tỷ giá mua bán chuyển khoản trung
   bình, R2). Fallback chain documented in ExchangeRateService.
3. Per monetary item: new_vnd = balance_original × closing_rate;
   diff = new_vnd − old_vnd.
4. Balanced journal: gain → 515 (Có), loss → 635 (Nợ) (R3, direct path).
5. Idempotent: re-run reverses prior POSTED run (D7).
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from src.application.ports import (
    ExchangeRateRepositoryPort,
    RevaluationRepositoryPort,
)
from src.domain.entities.base import PostingSide, RateType, RevaluationStatus
from src.domain.entities.currency import FXDifference, RevaluationEntry, RevaluationRun
from src.domain.exceptions import (
    PeriodLockedError,
    RateNotFoundError,
    RevaluationError,
)

logger = logging.getLogger(__name__)

# Direct path accounts (R3). Configurable via fx_gain_account / fx_loss_account
# CompanyConfig flags (specs §2.3) — passed at construction for now.
DEFAULT_GAIN_ACCOUNT = "5151"
DEFAULT_LOSS_ACCOUNT = "6351"


class RevaluationService:
    """Orchestrates period-end revaluation lifecycle."""

    def __init__(
        self,
        revaluation_repo: RevaluationRepositoryPort,
        rate_repo: ExchangeRateRepositoryPort,
        fx_gain_account: str = DEFAULT_GAIN_ACCOUNT,
        fx_loss_account: str = DEFAULT_LOSS_ACCOUNT,
    ) -> None:
        self._revaluation_repo = revaluation_repo
        self._rate_repo = rate_repo
        self._fx_gain_account = fx_gain_account
        self._fx_loss_account = fx_loss_account

    # ── Create (spec §4) ───────────────────────────────────────────────────

    def create_run(
        self,
        company_id: UUID,
        period_start: date,
        period_end: date,
        rate_date: date,
        monetary_items: list[dict],
        actor: UUID,
    ) -> RevaluationRun:
        """Create a DRAFT revaluation run for the period.

        monetary_items: list of {account_code, currency_code, balance_original,
        old_vnd}. Reverses prior POSTED run first (D7). Raises
        PeriodLockedError if the period is locked (D8).
        """
        if self._revaluation_repo.period_is_locked(company_id, period_start, period_end):
            raise PeriodLockedError(
                f"Kỳ kế toán {period_start} → {period_end} đang khóa; không thể đánh giá lại"
            )

        # Compute entries FIRST: if any rate is missing the new run fails
        # before we destroy the prior POSTED run (D7 — no data loss on error).
        entries = self._compute_entries(monetary_items, rate_date)

        prior = self._revaluation_repo.get_posted_run(company_id, period_start, period_end)
        if prior is not None:
            prior.reverse()
            self._revaluation_repo.save_run(prior)

        run = RevaluationRun(
            company_id=company_id,
            period_start=period_start,
            period_end=period_end,
            rate_date=rate_date,
            actor=actor,
            entries=entries,
        )
        return self._revaluation_repo.create_run(run)

    def _compute_entries(
        self, monetary_items: list[dict], rate_date: date
    ) -> list[RevaluationEntry]:
        """Build balanced journal entries from monetary items (spec §4.4-4.5)."""
        required = ("account_code", "currency_code", "balance_original", "old_vnd")
        entries: list[RevaluationEntry] = []
        for item in monetary_items:
            missing = [k for k in required if not item.get(k)]
            if missing:
                raise ValueError(f"monetary_items thiếu trường: {', '.join(missing)}")
            currency_code = item["currency_code"]
            closing_rate = self._resolve_closing_rate(currency_code, rate_date)
            balance = Decimal(item["balance_original"])
            old_vnd = Decimal(item["old_vnd"])
            new_vnd = balance * closing_rate
            diff = new_vnd - old_vnd

            if diff > 0:
                # gain → item debit, offset credit on fx_gain_account (R3)
                entries.append(
                    RevaluationEntry(
                        account_code=item["account_code"],
                        currency_code=currency_code,
                        balance_original=balance,
                        rate_applied=closing_rate,
                        old_vnd=old_vnd,
                        new_vnd=new_vnd,
                        difference=diff,
                        posting_side=PostingSide.DEBIT,
                    )
                )
                entries.append(
                    RevaluationEntry(
                        account_code=self._fx_gain_account,
                        currency_code=currency_code,
                        balance_original=Decimal("0"),
                        rate_applied=closing_rate,
                        old_vnd=Decimal("0"),
                        new_vnd=Decimal("0"),
                        difference=-diff,
                        posting_side=PostingSide.CREDIT,
                    )
                )
            elif diff < 0:
                # loss → item credit, offset debit on fx_loss_account (R3)
                entries.append(
                    RevaluationEntry(
                        account_code=item["account_code"],
                        currency_code=currency_code,
                        balance_original=balance,
                        rate_applied=closing_rate,
                        old_vnd=old_vnd,
                        new_vnd=new_vnd,
                        difference=diff,
                        posting_side=PostingSide.CREDIT,
                    )
                )
                entries.append(
                    RevaluationEntry(
                        account_code=self._fx_loss_account,
                        currency_code=currency_code,
                        balance_original=Decimal("0"),
                        rate_applied=closing_rate,
                        old_vnd=Decimal("0"),
                        new_vnd=Decimal("0"),
                        difference=-diff,
                        posting_side=PostingSide.DEBIT,
                    )
                )
            # diff == 0: no posting needed (R4: non-monetary / no movement)
        return entries

    def _resolve_closing_rate(self, currency_code: str, rate_date: date) -> Decimal:
        rate = self._rate_repo.get_latest(currency_code, RateType.TRANSFER, rate_date)
        if rate is None:
            # Fallback to BUY (tỷ giá mua) when no transfer rate configured
            rate = self._rate_repo.get_latest(currency_code, RateType.BUY, rate_date)
        if rate is None:
            raise RateNotFoundError(
                f"Không có tỷ giá chốt kỳ (TRANSFER/BUY) cho {currency_code} "
                f"tại ngày {rate_date}"
            )
        return rate.rate

    # ── State machine (D9) ─────────────────────────────────────────────────

    def approve_run(self, run_id: UUID, approver: UUID) -> RevaluationRun:
        """Approve a run (CHIEF_ACCOUNTANT, 2nd-approval pattern)."""
        run = self._get_run(run_id)
        if run.actor == approver:
            raise RevaluationError("Người tạo đợt đánh giá lại không được tự duyệt (SOD, D9)")
        if run.status == RevaluationStatus.DRAFT:
            run.submit_for_approval()  # convenience: DRAFT → PENDING → APPROVED
        run.approve(approver)
        return self._revaluation_repo.save_run(run)

    def post_run(self, run_id: UUID) -> RevaluationRun:
        """Post journal entries. Requires APPROVED + balanced (D6, D9)."""
        run = self._get_run(run_id)
        run.post()
        return self._revaluation_repo.save_run(run)

    def reverse_run(self, run_id: UUID) -> RevaluationRun:
        """Reverse a POSTED run (D7 re-run path)."""
        run = self._get_run(run_id)
        run.reverse()
        return self._revaluation_repo.save_run(run)

    def get_run(self, run_id: UUID) -> RevaluationRun:
        return self._get_run(run_id)

    def list_fx_differences(
        self, company_id: UUID, period_start: date, period_end: date
    ) -> list[FXDifference]:
        """FX difference report rows for the period."""
        return self._revaluation_repo.list_fx_differences(company_id, period_start, period_end)

    def _get_run(self, run_id: UUID) -> RevaluationRun:
        run = self._revaluation_repo.get_run(run_id)
        if run is None:
            raise RevaluationError(f"Đợt đánh giá lại {run_id} không tồn tại")
        return run
