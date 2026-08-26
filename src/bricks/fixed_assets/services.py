"""FixedAsset service — CRUD + straight-line depreciation engine (§4)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.bricks.fixed_assets.domain import GENESIS_CHECKSUM, FixedAsset


class MissingActorError(Exception):
    code = "MISSING_ACTOR"


class DuplicateAssetCodeError(Exception):
    code = "DUPLICATE_ASSET_CODE"


class NotFoundError(Exception):
    code = "NOT_FOUND"


class AssetClosedError(Exception):
    code = "ASSET_CLOSED"


def _d(v: Any) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


def _require(actor: UUID | None) -> UUID:
    if actor is None:
        raise MissingActorError("actor là bắt buộc")
    return actor


def _stamp(asset: FixedAsset, action: str, actor: UUID) -> str:
    prev = asset.checksum or GENESIS_CHECKSUM
    return asset.compute_checksum(prev, actor, action)


class FixedAssetService:
    def __init__(
        self,
        repo: Any,
        *,
        coa_gate: Any | None = None,
        fy_gate: Any | None = None,
    ) -> None:
        self._repo = repo
        self._coa_gate = coa_gate
        self._fy_gate = fy_gate

    # ── create ──────────────────────────────────────────────────────────

    def create_asset(
        self,
        *,
        company_id: UUID,
        asset_code: str,
        name: str,
        category: str = "huu_hinh",
        original_cost: Decimal | str,
        acquisition_date: date,
        useful_life_months: int,
        depreciation_account: str = "6421",
        actor: UUID | None = None,
        reason: str = "",
    ) -> FixedAsset:
        actor_u: UUID = _require(actor)
        if self._repo.exists_duplicate(company_id, asset_code):
            raise DuplicateAssetCodeError(f"Trùng mã TSCĐ: {asset_code}")
        if self._coa_gate is not None:
            self._coa_gate.validate_posting_account(company_id, depreciation_account)

        fa = FixedAsset(
            company_id=company_id,
            asset_code=asset_code.strip(),
            name=name.strip(),
            category=category,
            original_cost=_d(original_cost),
            acquisition_date=acquisition_date,
            useful_life_months=int(useful_life_months),
            depreciation_account=depreciation_account,
        )
        fa.checksum = _stamp(fa, "CREATE", actor_u)
        created: FixedAsset = self._repo.create(fa)
        return created

    # ── queries ─────────────────────────────────────────────────────────

    def get_asset(self, aid: UUID) -> FixedAsset | None:
        found: FixedAsset | None = self._repo.get_by_id(aid)
        return found

    def list_by_company(self, cid: UUID) -> list[FixedAsset]:
        rows: list[FixedAsset] = self._repo.get_by_company(cid)
        return rows

    # ── lifecycle ───────────────────────────────────────────────────────

    def deactivate(self, aid: UUID, *, actor: UUID, reason: str) -> FixedAsset:
        _require(actor)
        fa = self._get_or_404(aid)
        fa.is_active = False
        fa.checksum = _stamp(fa, "DEACTIVATE", actor)
        deactivated: FixedAsset = self._repo.update(fa)
        return deactivated

    def validate_before_entry(self, company_id: UUID, aid: UUID) -> None:
        fa = self._get_or_404(aid)
        if fa.company_id != company_id:
            raise NotFoundError("TK không thuộc công ty")
        if not fa.is_active:
            raise AssetClosedError("TSCĐ đã đóng")

    def _get_or_404(self, aid: UUID) -> FixedAsset:
        acc: FixedAsset | None = self._repo.get_by_id(aid)
        if acc is None:
            raise NotFoundError("Không tìm thấy TSCĐ")
        return acc

    # ── depreciation engine ─────────────────────────────────────────────

    def compute_and_post(self, company_id: UUID, *, actor: UUID) -> dict[str, Any]:
        """Monthly batch: compute straight-line per ACTIVE asset with remaining.

        Updates each asset's accumulated_depreciation in-place.
        Returns {"entries": [...], "journal_groups": [...]}.
        """
        _require(actor)
        assets = self._repo.find_active_with_remaining(company_id)

        entries: list[dict[str, Any]] = []
        journal_groups: dict[str, list[dict[str, Any]]] = {}

        for fa in assets:
            monthly = fa.monthly_depreciation
            remaining = fa.original_cost - fa.accumulated_depreciation
            amount = min(monthly, remaining)

            if amount <= 0:
                continue

            entry: dict[str, Any] = {
                "asset_id": str(fa.id),
                "asset_code": fa.asset_code,
                "expense_account": fa.depreciation_account,
                "amount": str(amount),
                "accumulated_before": str(fa.accumulated_depreciation),
                "accumulated_after": str(fa.accumulated_depreciation + amount),
            }
            entries.append(entry)

            journal_groups.setdefault(fa.depreciation_account, []).append(
                {
                    "asset_code": fa.asset_code,
                    "amount": str(amount),
                }
            )

            fa.accumulated_depreciation += amount
            fa.checksum = _stamp(fa, "DEPRECIATE", actor)
            self._repo.update(fa)

        journal_group_list = [
            {
                "expense_account": acct,
                "lines": lines_list,
                "total": str(sum(_d(x["amount"]) for x in lines_list)),
            }
            for acct, lines_list in journal_groups.items()
        ]

        return {"entries": entries, "journal_groups": journal_group_list}


class NoRemainingDepreciationError(Exception):
    code = "NO_REMAINING_DEPRECIATION"
