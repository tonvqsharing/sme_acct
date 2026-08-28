"""Financial Statements domain — report templates and computation. Pure Python."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class ReportTemplateType(Enum):
    """Report template types per TT99."""

    TRIAL_BALANCE = "S06-DN"
    BALANCE_SHEET = "B01-DN"
    INCOME_STATEMENT = "B02-DN"
    CASH_FLOW = "B03-DN"


class LineType(Enum):
    """Template line types."""

    HEADER = "header"
    ACCOUNT_AGGREGATE = "account_aggregate"
    FORMULA = "formula"
    TOTAL = "total"


@dataclass
class ReportTemplateLine:
    """One row in a report template."""

    template_id: UUID
    line_code: str
    line_name: str
    line_type: LineType
    account_codes: list[str] = field(default_factory=list)
    formula: str | None = None
    parent_code: str | None = None
    level: int = 0
    sort_order: int = 0
    sign: int = 1
    id: UUID = field(default_factory=uuid4)


@dataclass
class ReportTemplate:
    """Template definition for a financial statement."""

    code: str
    name: str
    description: str = ""
    company_id: UUID | None = None
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)
    lines: list[ReportTemplateLine] = field(default_factory=list)


@dataclass
class ReportInstanceLine:
    """Calculated value for one line."""

    instance_id: UUID
    line_code: str
    line_name: str
    value_current: Decimal = Decimal(0)
    value_prior: Decimal | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass
class ReportInstance:
    """Calculated snapshot of a report."""

    template_id: UUID
    company_id: UUID
    period_from: date
    period_to: date
    status: str = "DRAFT"
    id: UUID = field(default_factory=uuid4)
    lines: list[ReportInstanceLine] = field(default_factory=list)


@dataclass
class RetainedEarnings:
    """Retained earnings tracking across fiscal years."""

    company_id: UUID
    fiscal_year_id: UUID
    opening_balance: Decimal = Decimal(0)
    net_income: Decimal = Decimal(0)
    dividends: Decimal = Decimal(0)
    checksum: str = ""
    id: UUID = field(default_factory=uuid4)

    @property
    def closing_balance(self) -> Decimal:
        return self.opening_balance + self.net_income - self.dividends
