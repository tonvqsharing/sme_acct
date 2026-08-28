"""Unit tests for Financial Statements domain and storage."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from src.bricks.financial_statements.domain import (
    ClosingEntry,
    ClosingEntryType,
    LineType,
    PeriodCloseResult,
    ReportInstance,
    ReportInstanceLine,
    ReportTemplate,
    ReportTemplateLine,
    ReportTemplateType,
    RetainedEarnings,
)


class TestReportTemplateType:
    def test_trial_balance_value(self):
        assert ReportTemplateType.TRIAL_BALANCE.value == "S06-DN"

    def test_balance_sheet_value(self):
        assert ReportTemplateType.BALANCE_SHEET.value == "B01-DN"

    def test_income_statement_value(self):
        assert ReportTemplateType.INCOME_STATEMENT.value == "B02-DN"

    def test_cash_flow_value(self):
        assert ReportTemplateType.CASH_FLOW.value == "B03-DN"


class TestLineType:
    def test_header_value(self):
        assert LineType.HEADER.value == "header"

    def test_account_aggregate_value(self):
        assert LineType.ACCOUNT_AGGREGATE.value == "account_aggregate"

    def test_formula_value(self):
        assert LineType.FORMULA.value == "formula"

    def test_total_value(self):
        assert LineType.TOTAL.value == "total"


class TestReportTemplate:
    def test_create_template(self):
        tmpl = ReportTemplate(
            code="B01-DN",
            name="Balance Sheet",
            description="Bảng cân đối kế toán",
        )
        assert tmpl.code == "B01-DN"
        assert tmpl.is_active is True
        assert tmpl.lines == []

    def test_template_with_company(self):
        cid = uuid4()
        tmpl = ReportTemplate(
            code="CUSTOM",
            name="Custom Report",
            company_id=cid,
        )
        assert tmpl.company_id == cid

    def test_template_with_lines(self):
        tmpl = ReportTemplate(code="B01-DN", name="Balance Sheet")
        line = ReportTemplateLine(
            template_id=tmpl.id,
            line_code="100",
            line_name="Assets",
            line_type=LineType.HEADER,
            level=0,
        )
        tmpl.lines.append(line)
        assert len(tmpl.lines) == 1
        assert tmpl.lines[0].line_code == "100"


class TestReportTemplateLine:
    def test_line_defaults(self):
        line = ReportTemplateLine(
            template_id=uuid4(),
            line_code="111",
            line_name="Cash",
            line_type=LineType.ACCOUNT_AGGREGATE,
        )
        assert line.account_codes == []
        assert line.formula is None
        assert line.parent_code is None
        assert line.level == 0
        assert line.sort_order == 0
        assert line.sign == 1

    def test_line_with_accounts(self):
        line = ReportTemplateLine(
            template_id=uuid4(),
            line_code="111",
            line_name="Cash",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["1111", "1112", "1113"],
            sign=1,
        )
        assert len(line.account_codes) == 3

    def test_line_with_formula(self):
        line = ReportTemplateLine(
            template_id=uuid4(),
            line_code="A",
            line_name="Total",
            line_type=LineType.FORMULA,
            formula="100+200",
        )
        assert line.formula == "100+200"


class TestRetainedEarnings:
    def test_closing_balance(self):
        re = RetainedEarnings(
            company_id=uuid4(),
            fiscal_year_id=uuid4(),
            opening_balance=Decimal(1000),
            net_income=Decimal(500),
            dividends=Decimal(100),
        )
        assert re.closing_balance == Decimal(1400)

    def test_negative_net_income(self):
        re = RetainedEarnings(
            company_id=uuid4(),
            fiscal_year_id=uuid4(),
            opening_balance=Decimal(1000),
            net_income=Decimal(-200),
            dividends=Decimal(0),
        )
        assert re.closing_balance == Decimal(800)


class TestReportInstance:
    def test_instance_defaults(self):
        inst = ReportInstance(
            template_id=uuid4(),
            company_id=uuid4(),
            period_from=date(2026, 1, 1),
            period_to=date(2026, 12, 31),
        )
        assert inst.status == "DRAFT"
        assert inst.lines == []


class TestReportInstanceLine:
    def test_instance_line_defaults(self):
        line = ReportInstanceLine(
            instance_id=uuid4(),
            line_code="100",
            line_name="Assets",
        )
        assert line.value_current == Decimal(0)
        assert line.value_prior is None


# ─── Month-End Close domain tests ──────────────────────────────────────


class TestClosingEntryType:
    def test_revenue_transfer_value(self):
        assert ClosingEntryType.REVENUE_TRANSFER.value == "revenue_transfer"

    def test_expense_transfer_value(self):
        assert ClosingEntryType.EXPENSE_TRANSFER.value == "expense_transfer"

    def test_cit_provision_value(self):
        assert ClosingEntryType.CIT_PROVISION.value == "cit_provision"


class TestClosingEntry:
    def test_revenue_transfer_entry(self):
        entry = ClosingEntry(
            entry_type=ClosingEntryType.REVENUE_TRANSFER,
            description="Transfer revenue to 911",
            debit_account="911",
            credit_account="5111",
            amount=Decimal(5000000),
        )
        assert entry.entry_type == ClosingEntryType.REVENUE_TRANSFER
        assert entry.debit_account == "911"
        assert entry.credit_account == "5111"
        assert entry.amount == Decimal(5000000)
        assert entry.lines == []

    def test_expense_transfer_entry(self):
        entry = ClosingEntry(
            entry_type=ClosingEntryType.EXPENSE_TRANSFER,
            description="Transfer expenses to 911",
            debit_account="6321",
            credit_account="911",
            amount=Decimal(3000000),
        )
        assert entry.entry_type == ClosingEntryType.EXPENSE_TRANSFER
        assert entry.debit_account == "6321"
        assert entry.credit_account == "911"

    def test_cit_provision_entry(self):
        entry = ClosingEntry(
            entry_type=ClosingEntryType.CIT_PROVISION,
            description="CIT provision",
            debit_account="8211",
            credit_account="3334",
            amount=Decimal(400000),
        )
        assert entry.entry_type == ClosingEntryType.CIT_PROVISION
        assert entry.debit_account == "8211"
        assert entry.credit_account == "3334"

    def test_entry_with_voucher_lines(self):
        lines = [
            {"account_code": "911", "debit": "5000000", "credit": "0"},
            {"account_code": "5111", "debit": "0", "credit": "5000000"},
        ]
        entry = ClosingEntry(
            entry_type=ClosingEntryType.REVENUE_TRANSFER,
            description="Transfer revenue to 911",
            debit_account="911",
            credit_account="5111",
            amount=Decimal(5000000),
            lines=lines,
        )
        assert len(entry.lines) == 2
        assert entry.lines[0]["account_code"] == "911"


class TestPeriodCloseResult:
    def test_success_result(self):
        entries = [
            ClosingEntry(
                entry_type=ClosingEntryType.REVENUE_TRANSFER,
                description="Transfer revenue",
                debit_account="911",
                credit_account="5111",
                amount=Decimal(5000000),
            ),
            ClosingEntry(
                entry_type=ClosingEntryType.EXPENSE_TRANSFER,
                description="Transfer expenses",
                debit_account="6321",
                credit_account="911",
                amount=Decimal(3000000),
            ),
        ]
        result = PeriodCloseResult(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            closing_entries=entries,
            net_income=Decimal(2000000),
            success=True,
        )
        assert result.success is True
        assert result.net_income == Decimal(2000000)
        assert len(result.closing_entries) == 2
        assert result.error_message is None

    def test_failure_result(self):
        result = PeriodCloseResult(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            success=False,
            error_message="Period already closed",
        )
        assert result.success is False
        assert result.error_message == "Period already closed"
        assert result.closing_entries == []

    def test_default_values(self):
        result = PeriodCloseResult(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
        )
        assert result.success is False
        assert result.net_income == Decimal(0)
        assert result.closing_entries == []
