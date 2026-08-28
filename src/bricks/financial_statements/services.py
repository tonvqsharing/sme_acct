"""Financial Statements services — ReportEngine computation. Pure Python."""

from __future__ import annotations

from decimal import Decimal

from src.bricks.financial_statements.domain import (
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
    ) -> list[ReportInstanceLine]:
        """Compute all lines for a report instance.

        Args:
            template: Report template with lines.
            account_balances: {account_code: {"debit": Decimal, "credit": Decimal}}

        Returns:
            List of computed ReportInstanceLine values.
        """
        lines_by_code = {line.line_code: line for line in template.lines}
        computed: dict[str, Decimal] = {}
        result_lines: list[ReportInstanceLine] = []

        for line in template.lines:
            value = self._compute_line(line, lines_by_code, account_balances, computed, trail=set())
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
        computed: dict[str, Decimal],
        trail: set[str],
    ) -> Decimal:
        """Compute a single line value."""
        if line.line_type == LineType.HEADER:
            return ZERO

        if line.line_type == LineType.ACCOUNT_AGGREGATE:
            return self._compute_account_aggregate(line, account_balances)

        if line.line_type == LineType.TOTAL:
            return self._compute_total(line, lines_by_code, account_balances, computed, trail)

        if line.line_type == LineType.FORMULA:
            return self._compute_formula(line, lines_by_code, account_balances, computed, trail)

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
                        child_line, lines_by_code, account_balances, computed, trail
                    )
                total += computed[child_code]
        return total

    def _compute_formula(
        self,
        line: ReportTemplateLine,
        lines_by_code: dict[str, ReportTemplateLine],
        account_balances: dict[str, dict[str, Decimal]],
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
                    ref_line, lines_by_code, account_balances, computed, trail
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

    Uses cash_flow_class tags on voucher lines, not account codes.
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
        lines_by_code = {line.line_code: line for line in template.lines}
        computed: dict[str, Decimal] = {}

        result_lines: list[ReportInstanceLine] = []
        for line in template.lines:
            if line.line_type == LineType.CASH_FLOW_ITEM:
                # Direct mapping from cash_flow_amounts by line_code
                value = cash_flow_amounts.get(line.line_code, ZERO)
                computed[line.line_code] = value
            elif line.line_type == LineType.HEADER:
                value = ZERO
                computed[line.line_code] = value
            elif line.line_type == LineType.TOTAL:
                value = self._engine._compute_total(line, lines_by_code, {}, computed, trail=set())
                computed[line.line_code] = value
            elif line.line_type == LineType.FORMULA:
                if line.line_code == "CASH_END":
                    value = computed.get("NET_CF", ZERO) + opening_cash
                else:
                    value = self._engine._compute_formula(
                        line, lines_by_code, {}, computed, trail=set()
                    )
                computed[line.line_code] = value
            elif line.line_type == LineType.ACCOUNT_AGGREGATE:
                if line.line_code == "CASH_BEGIN":
                    value = opening_cash
                else:
                    value = ZERO
                computed[line.line_code] = value
            else:
                value = ZERO
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
