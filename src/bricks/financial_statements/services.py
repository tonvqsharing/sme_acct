"""Financial Statements services — ReportEngine + PeriodCloseService. Pure Python."""

from __future__ import annotations

from decimal import Decimal

from src.bricks.financial_statements.domain import (
    ClosingEntry,
    ClosingEntryType,
    LineType,
    ReportInstanceLine,
    ReportTemplate,
    ReportTemplateLine,
)

ZERO = Decimal(0)


class CircularFormulaError(Exception):
    """Raised when a FORMULA line references itself or creates a cycle."""


class UnknownLineReferenceError(Exception):
    """Raised when a FORMULA references a line_code that doesn't exist."""


class BalanceSheetImbalanceError(Exception):
    """Raised when Assets != Liabilities + Equity."""


class ReportEngine:
    """Compute report values from template lines + account balances.

    Pure Python — no Flask/SQLAlchemy imports. Primitives in/out.
    """

    def compute(
        self,
        template: ReportTemplate,
        account_balances: dict[str, dict[str, Decimal]],
        cash_flow_values: dict[str, Decimal] | None = None,
    ) -> list[ReportInstanceLine]:
        """Compute all lines for a report instance.

        Args:
            template: Report template with lines.
            account_balances: {account_code: {"debit": Decimal, "credit": Decimal}}
            cash_flow_values: {line_code: net_amount} — for CASH_FLOW_ITEM lines.

        Returns:
            List of computed ReportInstanceLine values.
        """
        cf_vals = cash_flow_values or {}
        lines_by_code = {line.line_code: line for line in template.lines}
        computed: dict[str, Decimal] = {}
        result_lines: list[ReportInstanceLine] = []

        for line in template.lines:
            value = self._compute_line(
                line, lines_by_code, account_balances, cf_vals, computed, trail=set()
            )
            computed[line.line_code] = value
            result_lines.append(
                ReportInstanceLine(
                    instance_id=None,  # type: ignore[arg-type]
                    line_code=line.line_code,
                    line_name=line.line_name,
                    value_current=value,
                )
            )

        return result_lines

    def _compute_line(
        self,
        line: ReportTemplateLine,
        lines_by_code: dict[str, ReportTemplateLine],
        account_balances: dict[str, dict[str, Decimal]],
        cash_flow_values: dict[str, Decimal],
        computed: dict[str, Decimal],
        trail: set[str],
    ) -> Decimal:
        """Compute a single line value."""
        if line.line_type == LineType.HEADER:
            return ZERO

        if line.line_type == LineType.ACCOUNT_AGGREGATE:
            return self._compute_account_aggregate(line, account_balances)

        if line.line_type == LineType.CASH_FLOW_ITEM:
            return cash_flow_values.get(line.line_code, ZERO)

        if line.line_type == LineType.TOTAL:
            return self._compute_total(
                line, lines_by_code, account_balances, cash_flow_values, computed, trail
            )

        if line.line_type == LineType.FORMULA:
            return self._compute_formula(
                line, lines_by_code, account_balances, cash_flow_values, computed, trail
            )

        return ZERO

    def _compute_account_aggregate(
        self,
        line: ReportTemplateLine,
        account_balances: dict[str, dict[str, Decimal]],
    ) -> Decimal:
        """Sum specified account codes. sign=-1 for contra accounts."""
        total = ZERO
        for code in line.account_codes:
            bal = account_balances.get(code)
            if bal is None:
                continue
            # For asset/liability: net = debit - credit
            # For revenue/expense: use credit balance (revenue) or debit balance (expense)
            # The sign field on the line controls direction.
            net = bal.get("debit", ZERO) - bal.get("credit", ZERO)
            total += net * line.sign
        return total

    def _compute_total(
        self,
        line: ReportTemplateLine,
        lines_by_code: dict[str, ReportTemplateLine],
        account_balances: dict[str, dict[str, Decimal]],
        cash_flow_values: dict[str, Decimal],
        computed: dict[str, Decimal],
        trail: set[str],
    ) -> Decimal:
        """Sum of child lines (lines whose parent_code == this line's line_code)."""
        total = ZERO
        for child_code, child_line in lines_by_code.items():
            if child_line.parent_code == line.line_code:
                # Recursively compute child if not yet computed
                if child_code not in computed:
                    computed[child_code] = self._compute_line(
                        child_line,
                        lines_by_code,
                        account_balances,
                        cash_flow_values,
                        computed,
                        trail,
                    )
                total += computed[child_code]
        return total

    def _compute_formula(
        self,
        line: ReportTemplateLine,
        lines_by_code: dict[str, ReportTemplateLine],
        account_balances: dict[str, dict[str, Decimal]],
        cash_flow_values: dict[str, Decimal],
        computed: dict[str, Decimal],
        trail: set[str],
    ) -> Decimal:
        """Evaluate arithmetic formula on other lines.

        Supported syntax: line_code references separated by + or -
        Example: "100+200-300" means line_100 + line_200 - line_300
        """
        if not line.formula:
            return ZERO

        # Cycle detection
        if line.line_code in trail:
            raise CircularFormulaError(
                f"Circular reference detected involving line '{line.line_code}'"
            )
        trail = trail | {line.line_code}

        # Parse formula: split by + and - while preserving operators
        tokens = self._parse_formula(line.formula)
        result = ZERO

        for op, ref_code in tokens:
            if ref_code not in lines_by_code:
                raise UnknownLineReferenceError(
                    f"Formula '{line.formula}' references unknown line '{ref_code}'"
                )

            # Recursively compute if not yet done
            if ref_code not in computed:
                ref_line = lines_by_code[ref_code]
                computed[ref_code] = self._compute_line(
                    ref_line, lines_by_code, account_balances, cash_flow_values, computed, trail
                )

            value = computed[ref_code]
            if op == "+":
                result += value
            elif op == "-":
                result -= value

        return result

    def _parse_formula(self, formula: str) -> list[tuple[str, str]]:
        """Parse formula string into [(operator, line_code), ...].

        Example: "100+200-300" → [("+", "100"), ("+", "200"), ("-", "300")]
        """
        tokens: list[tuple[str, str]] = []
        current_op = "+"
        current_code = ""

        for ch in formula:
            if ch in ("+", "-"):
                if current_code:
                    tokens.append((current_op, current_code))
                    current_code = ""
                current_op = ch
            elif ch.strip():  # Skip whitespace
                current_code += ch

        if current_code:
            tokens.append((current_op, current_code))

        return tokens


class BalanceSheetService:
    """Compute Balance Sheet (B01-DN) from account balances.

    Pure Python — no Flask/SQLAlchemy imports.
    """

    def __init__(self) -> None:
        self._engine = ReportEngine()

    def compute(
        self,
        template: ReportTemplate,
        account_balances: dict[str, dict[str, Decimal]],
    ) -> list[ReportInstanceLine]:
        """Compute all Balance Sheet lines.

        Args:
            template: B01-DN template with lines.
            account_balances: {account_code: {"debit": Decimal, "credit": Decimal}}

        Returns:
            List of computed ReportInstanceLine values.

        Raises:
            BalanceSheetImbalanceError: If Assets != Liabilities + Equity.
        """
        lines = self._engine.compute(template, account_balances)

        # Validate balance check
        check_line = next((l for l in lines if l.line_code == "CHECK"), None)
        if check_line is not None and check_line.value_current != ZERO:
            raise BalanceSheetImbalanceError(
                f"Balance sheet imbalance: Assets - (Liabilities + Equity) = "
                f"{check_line.value_current}"
            )

        return lines


class IncomeStatementService:
    """Compute Income Statement (B02-DN) from account balances.

    Pure Python — no Flask/SQLAlchemy imports.
    """

    def __init__(self) -> None:
        self._engine = ReportEngine()

    def compute(
        self,
        template: ReportTemplate,
        account_balances: dict[str, dict[str, Decimal]],
    ) -> list[ReportInstanceLine]:
        """Compute all Income Statement lines.

        Args:
            template: B02-DN template with lines.
            account_balances: {account_code: {"debit": Decimal, "credit": Decimal}}

        Returns:
            List of computed ReportInstanceLine values.
        """
        return self._engine.compute(template, account_balances)


class CashFlowService:
    """Compute Cash Flow Statement (B03-DN) from cash flow data.

    Uses the public ReportEngine API — no private method access.
    Pure Python — no Flask/SQLAlchemy imports.
    """

    def __init__(self) -> None:
        self._engine = ReportEngine()

    def compute(
        self,
        template: ReportTemplate,
        cash_flow_amounts: dict[str, Decimal],
        opening_cash: Decimal = ZERO,
    ) -> list[ReportInstanceLine]:
        """Compute all Cash Flow Statement lines.

        Args:
            template: B03-DN template with lines.
            cash_flow_amounts: {line_code: net_amount}
                e.g., {"A1": Decimal(500), "A2": Decimal(-300), ...}
            opening_cash: Cash at beginning of period (account 110 balance).

        Returns:
            List of computed ReportInstanceLine values.
        """
        # Map opening_cash to account_balances for ACCOUNT_AGGREGATE lines (CASH_BEGIN)
        account_balances: dict[str, dict[str, Decimal]] = {}
        if opening_cash != ZERO:
            account_balances["110"] = {"debit": opening_cash, "credit": ZERO}

        return self._engine.compute(template, account_balances, cash_flow_values=cash_flow_amounts)


# ─── Month-End Close Service (Sprint 7) ────────────────────────────────

# Account 911 — Xác định kết quả kinh doanh (Determining Business Results)
ACCOUNT_911 = "911"

# CIT provision accounts per TT99
CIT_EXPENSE_ACCOUNT = "8211"  # Thuế TNDN hiện hành
CIT_PAYABLE_ACCOUNT = "3334"  # Thuế TNDN phải nộp


def _is_revenue_account(code: str) -> bool:
    """Identify revenue accounts per TT99 Vietnamese accounting.

    Group 5 (5xx) = Doanh thu (Revenue) — credit-normal
    Account 711 = Doanh thu tài chính (Financial income)
    """
    if not code or not code[0].isdigit():
        return False
    first = int(code[0])
    # 5xx = Doanh thu (Revenue)
    if first == 5:
        return True
    # 711 = Doanh thu tài chính (Financial income)
    return code.startswith("711")


def _is_expense_account(code: str) -> bool:
    """Identify expense accounts per TT99 Vietnamese accounting.

    Group 6 (6xx) = Chi phí hoạt động kinh doanh (Cost of business)
    Group 7 (7xx except 711) = Chi phí tài chính (Financial expenses)
    Group 8 (8xx) = Thuế TNDN (CIT expense)
    Group 9 (9xx) = Kết quả kinh doanh (Settlement)
    """
    if not code or not code[0].isdigit():
        return False
    first = int(code[0])
    # 6xx = Chi phí hoạt động kinh doanh
    if first == 6:
        return True
    # 7xx except 711 = Chi phí tài chính
    if first == 7 and not code.startswith("711"):
        return True
    # 8xx = Thuế TNDN
    if first == 8:
        return True
    # 9xx = Kết quả kinh doanh
    return first == 9


class PeriodCloseService:
    """Execute month-end close procedure.

    Steps per TT99 §7.1:
    1. Transfer revenue to 911 (Dr. 911 / Cr. revenue accounts)
    2. Transfer expenses to 911 (Dr. expense accounts / Cr. 911)
    3. Calculate CIT provision (Dr. 8211 / Cr. 3334)

    Pure Python — no Flask/SQLAlchemy imports. Primitives in/out.
    """

    def __init__(self) -> None:
        pass

    def transfer_revenue(
        self,
        company_id: object,
        fiscal_year: int,
        period: int,
        trial_balance: list[dict[str, object]],
    ) -> ClosingEntry:
        """Step 3: Transfer revenue accounts to 911.

        Vietnamese accounting (TT99):
        - Group 5 (5xx) = Doanh thu (Revenue) — credit-normal
        - Group 7 account711 = Doanh thu tài chính (Financial income)
        For each revenue account with credit balance:
        Dr. 911 (amount) / Cr. revenue account (amount)

        Args:
            company_id: Company UUID (passed through, not used in calculation).
            fiscal_year: Fiscal year number.
            period: Period number (1-12).
            trial_balance: List of account balances from LedgerService.trial_balance().
                Each dict has: account_code (str), debit (Decimal), credit (Decimal).

        Returns:
            ClosingEntry with voucher lines for VoucherService.
        """
        revenue_entries: list[dict[str, str]] = []
        total_revenue = ZERO

        for row in trial_balance:
            code = str(row["account_code"])
            credit = Decimal(str(row.get("credit", 0)))
            debit = Decimal(str(row.get("debit", 0)))

            # Identify revenue accounts by first digit:
            # - 5xx = Doanh thu (Revenue) — TT99 group 5
            # - 711 = Doanh thu tài chính (Financial income)
            is_revenue = _is_revenue_account(code)
            if not is_revenue:
                continue

            # Revenue accounts have credit balance (credit > debit)
            net_credit = credit - debit
            if net_credit <= ZERO:
                continue

            # Dr. 911 / Cr. revenue account
            revenue_entries.append(
                {
                    "account_code": ACCOUNT_911,
                    "debit": str(net_credit),
                    "credit": "0",
                }
            )
            revenue_entries.append(
                {
                    "account_code": code,
                    "debit": "0",
                    "credit": str(net_credit),
                }
            )
            total_revenue += net_credit

        description = f"Kết quả kinh doanh tháng {period}/{fiscal_year} - Doanh thu"

        return ClosingEntry(
            entry_type=ClosingEntryType.REVENUE_TRANSFER,
            description=description,
            debit_account=ACCOUNT_911,
            credit_account="511/515/711",
            amount=total_revenue,
            lines=revenue_entries,
        )

    def transfer_expense(
        self,
        company_id: object,
        fiscal_year: int,
        period: int,
        trial_balance: list[dict[str, object]],
    ) -> ClosingEntry:
        """Step 4: Transfer expense accounts to 911.

        Vietnamese accounting (TT99):
        - Group 6 (6xx) = Chi phí hoạt động kinh doanh (Cost of business)
        - Group 7 (7xx except 711) = Chi phí tài chính (Financial expenses)
        - Group 8 (8xx) = Thuế TNDN (CIT expense)
        - Group 9 (9xx) = Kết quả kinh doanh (Settlement)
        For each expense account with debit balance:
        Dr. expense account (amount) / Cr. 911 (amount)

        Args:
            company_id: Company UUID (passed through, not used in calculation).
            fiscal_year: Fiscal year number.
            period: Period number (1-12).
            trial_balance: List of account balances from LedgerService.trial_balance().
                Each dict has: account_code (str), debit (Decimal), credit (Decimal).

        Returns:
            ClosingEntry with voucher lines for VoucherService.
        """
        expense_entries: list[dict[str, str]] = []
        total_expense = ZERO

        for row in trial_balance:
            code = str(row["account_code"])
            credit = Decimal(str(row.get("credit", 0)))
            debit = Decimal(str(row.get("debit", 0)))

            # Identify expense accounts by first digit
            is_expense = _is_expense_account(code)
            if not is_expense:
                continue

            # Expense accounts have debit balance (debit > credit)
            net_debit = debit - credit
            if net_debit <= ZERO:
                continue

            # Dr. expense account / Cr. 911
            expense_entries.append(
                {
                    "account_code": code,
                    "debit": str(net_debit),
                    "credit": "0",
                }
            )
            expense_entries.append(
                {
                    "account_code": ACCOUNT_911,
                    "debit": "0",
                    "credit": str(net_debit),
                }
            )
            total_expense += net_debit

        description = f"Kết quả kinh doanh tháng {period}/{fiscal_year} - Chi phí"

        return ClosingEntry(
            entry_type=ClosingEntryType.EXPENSE_TRANSFER,
            description=description,
            debit_account="632/635/641/642/811",
            credit_account=ACCOUNT_911,
            amount=total_expense,
            lines=expense_entries,
        )
