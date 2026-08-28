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
            value = self._compute_line(line, lines_by_code, account_balances, computed)
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
    ) -> Decimal:
        """Compute a single line value."""
        if line.line_type == LineType.HEADER:
            return ZERO

        if line.line_type == LineType.ACCOUNT_AGGREGATE:
            return self._compute_account_aggregate(line, account_balances)

        if line.line_type == LineType.TOTAL:
            return self._compute_total(line, lines_by_code, account_balances, computed)

        if line.line_type == LineType.FORMULA:
            return self._compute_formula(line, lines_by_code, account_balances, computed)

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
    ) -> Decimal:
        """Sum of child lines (lines whose parent_code == this line's line_code)."""
        total = ZERO
        for child_code, child_line in lines_by_code.items():
            if child_line.parent_code == line.line_code:
                # Recursively compute child if not yet computed
                if child_code not in computed:
                    computed[child_code] = self._compute_line(
                        child_line, lines_by_code, account_balances, computed
                    )
                total += computed[child_code] * child_line.sign
        return total

    def _compute_formula(
        self,
        line: ReportTemplateLine,
        lines_by_code: dict[str, ReportTemplateLine],
        account_balances: dict[str, dict[str, Decimal]],
        computed: dict[str, Decimal],
    ) -> Decimal:
        """Evaluate arithmetic formula on other lines.

        Supported syntax: line_code references separated by + or -
        Example: "100+200-300" means line_100 + line_200 - line_300
        """
        if not line.formula:
            return ZERO

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
                    ref_line, lines_by_code, account_balances, computed
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
