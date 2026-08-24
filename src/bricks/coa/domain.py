"""Chart of Accounts domain — Vietnamese TT133 / Circular 99-2025 codes. Pure Python."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

# ── Regime-aware account-code rules ────────────────────────────────────────
# TT133/TT58 (DN nhỏ và vừa / siêu nhỏ): 3-4 chữ số, không bắt đầu bằng 0.
# TT99 (enterprise, 2026 COA spec §AccountCode): 10 digits
#   ^[1-9]\d{2}\d{3}\d{3}$ with optional -NNN suffix.
# Verified against mof.gov.vn/vbpl.vn as of 2026-08.

TT133_CODE_RE = re.compile(r"^[1-9]\d{2}$|^[1-9]\d{3}$")
TT99_CODE_RE = re.compile(r"^[1-9]\d{9}(?:-\d{1,3})?$")

REGIME_CODE_RES: dict[str, re.Pattern[str]] = {
    "tt133": TT133_CODE_RE,
    "tt58_micro": TT133_CODE_RE,
    "tt99": TT99_CODE_RE,
}

DEFAULT_REGIME = "tt133"

# Kept for backward-compatible imports; resolves to the TT133 pattern.
ACCOUNT_CODE_PATTERN = r"^[1-9]\d{2}$|^[1-9]\d{3}$"
CODE_RE = TT133_CODE_RE

# Semantic roles → native codes per regime catalog.
CHART_TEMPLATES: dict[str, dict[str, str]] = {
    "tt133": {
        "cash": "111",
        "bank": "1121",
        "ar": "1311",
        "revenue": "5111",
        "vat_output": "3331",
    },
}
CHART_TEMPLATES["tt58_micro"] = CHART_TEMPLATES["tt133"]
CHART_TEMPLATES["tt99"] = {
    "cash": "1110000000",
    "bank": "1121000000",
    "ar": "1310000000",
    "revenue": "5110000000",
    "vat_output": "3331100000",
}


def resolve_chart_role(role: str, regime: str = DEFAULT_REGIME) -> str:
    """Map a semantic journal role to the regime's canonical account code."""
    template = CHART_TEMPLATES.get(regime)
    if template is None:
        raise ValueError(f"Unknown accounting regime: {regime}")
    try:
        return template[role]
    except KeyError as exc:
        raise ValueError(f"Unknown chart role: {role}") from exc


class AccountStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class NormalBalance(Enum):
    DEBIT = "debit"
    CREDIT = "credit"


@dataclass
class Account:
    company_id: UUID
    code: str
    name: str
    normal_balance: NormalBalance = NormalBalance.DEBIT
    parent_code: str | None = None
    regime: str = DEFAULT_REGIME
    id: UUID = field(default_factory=__import__("uuid").uuid4)
    status: AccountStatus = AccountStatus.ACTIVE

    def _validate_code(self, code: str) -> bool:
        return bool(REGIME_CODE_RES[self.regime].match(code))

    def __post_init__(self) -> None:
        if self.regime not in REGIME_CODE_RES:
            raise ValueError(f"Unknown accounting regime: {self.regime}")
        if not self._validate_code(self.code or ""):
            raise ValueError(
                f"code must match {self.regime} pattern "
                f"{REGIME_CODE_RES[self.regime].pattern}, got '{self.code}'"
            )
        if not self.name or not self.name.strip():
            raise ValueError("name is required")
        if self.parent_code is not None and not self._validate_code(self.parent_code):
            raise ValueError("parent_code must be a valid account code")

    @property
    def is_detail(self) -> bool:
        """Posting-level rule per regime.

        TT133 family: 4-digit codes post; 3-digit are aggregates.
        TT99: only fully-specified 10-digit codes post; shorter prefixes
        stay aggregate.
        """
        bare = self.code.split("-")[0]
        if self.regime == "tt99":
            return len(bare) == 10 and bare[6:] != "0000"
        return len(bare) == 4
