"""Unit tests for Financial Statements storage (SQLAlchemy repos)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.bricks.financial_statements.domain import (
    LineType,
    ReportInstance,
    ReportTemplate,
    ReportTemplateLine,
    RetainedEarnings,
)
from src.bricks.financial_statements.storage import (
    Base,
    SQLAlchemyReportInstanceRepository,
    SQLAlchemyReportTemplateRepository,
    SQLAlchemyRetainedEarningsRepository,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture()
def tmpl_repo(session):
    return SQLAlchemyReportTemplateRepository(session)


@pytest.fixture()
def inst_repo(session):
    return SQLAlchemyReportInstanceRepository(session)


@pytest.fixture()
def re_repo(session):
    return SQLAlchemyRetainedEarningsRepository(session)


class TestReportTemplateRepository:
    def test_create_and_get(self, tmpl_repo):
        tmpl = ReportTemplate(code="B01-DN", name="Balance Sheet")
        tmpl_repo.create(tmpl)
        fetched = tmpl_repo.get_by_id(tmpl.id)
        assert fetched is not None
        assert fetched.code == "B01-DN"
        assert fetched.name == "Balance Sheet"

    def test_get_by_code(self, tmpl_repo):
        tmpl = ReportTemplate(code="B02-DN", name="Income Statement")
        tmpl_repo.create(tmpl)
        fetched = tmpl_repo.get_by_code("B02-DN")
        assert fetched is not None
        assert fetched.code == "B02-DN"

    def test_list_templates(self, tmpl_repo):
        tmpl_repo.create(ReportTemplate(code="B01-DN", name="Balance Sheet"))
        tmpl_repo.create(ReportTemplate(code="B02-DN", name="Income Statement"))
        result = tmpl_repo.list_templates()
        assert len(result) == 2

    def test_list_by_company(self, tmpl_repo):
        cid = uuid4()
        tmpl_repo.create(ReportTemplate(code="B01-DN", name="Balance Sheet", company_id=cid))
        tmpl_repo.create(ReportTemplate(code="GLOBAL", name="Global Report"))
        result = tmpl_repo.list_templates(company_id=cid)
        assert len(result) == 1
        assert result[0].code == "B01-DN"

    def test_update(self, tmpl_repo):
        tmpl = ReportTemplate(code="B01-DN", name="Balance Sheet")
        tmpl_repo.create(tmpl)
        tmpl.name = "Updated Balance Sheet"
        tmpl_repo.update(tmpl)
        fetched = tmpl_repo.get_by_id(tmpl.id)
        assert fetched.name == "Updated Balance Sheet"


class TestReportTemplateLineRepository:
    def test_create_line(self, tmpl_repo, session):
        tmpl = ReportTemplate(code="B01-DN", name="Balance Sheet")
        tmpl_repo.create(tmpl)
        line = ReportTemplateLine(
            template_id=tmpl.id,
            line_code="100",
            line_name="Assets",
            line_type=LineType.HEADER,
            account_codes=["111", "112"],
        )
        tmpl_repo.create_line(line)
        lines = tmpl_repo.get_lines(tmpl.id)
        assert len(lines) == 1
        assert lines[0].line_code == "100"
        assert lines[0].account_codes == ["111", "112"]

    def test_get_lines_ordered(self, tmpl_repo):
        tmpl = ReportTemplate(code="B01-DN", name="Balance Sheet")
        tmpl_repo.create(tmpl)
        tmpl_repo.create_line(
            ReportTemplateLine(
                template_id=tmpl.id,
                line_code="200",
                line_name="Liabilities",
                line_type=LineType.HEADER,
                sort_order=2,
            )
        )
        tmpl_repo.create_line(
            ReportTemplateLine(
                template_id=tmpl.id,
                line_code="100",
                line_name="Assets",
                line_type=LineType.HEADER,
                sort_order=1,
            )
        )
        lines = tmpl_repo.get_lines(tmpl.id)
        assert lines[0].line_code == "100"
        assert lines[1].line_code == "200"


class TestReportInstanceRepository:
    def test_create_and_get(self, inst_repo, tmpl_repo):
        tmpl = ReportTemplate(code="B01-DN", name="Balance Sheet")
        tmpl_repo.create(tmpl)
        inst = ReportInstance(
            template_id=tmpl.id,
            company_id=uuid4(),
            period_from=date(2026, 1, 1),
            period_to=date(2026, 12, 31),
        )
        inst_repo.create(inst)
        fetched = inst_repo.get_by_id(inst.id)
        assert fetched is not None
        assert fetched.status == "DRAFT"

    def test_list_by_template(self, inst_repo, tmpl_repo):
        tmpl = ReportTemplate(code="B01-DN", name="Balance Sheet")
        tmpl_repo.create(tmpl)
        cid = uuid4()
        inst_repo.create(
            ReportInstance(
                template_id=tmpl.id,
                company_id=cid,
                period_from=date(2026, 1, 1),
                period_to=date(2026, 12, 31),
            )
        )
        result = inst_repo.list_by_template(tmpl.id, cid)
        assert len(result) == 1

    def test_update_status(self, inst_repo, tmpl_repo):
        tmpl = ReportTemplate(code="B01-DN", name="Balance Sheet")
        tmpl_repo.create(tmpl)
        inst = ReportInstance(
            template_id=tmpl.id,
            company_id=uuid4(),
            period_from=date(2026, 1, 1),
            period_to=date(2026, 12, 31),
        )
        inst_repo.create(inst)
        inst.status = "FINAL"
        inst_repo.update(inst)
        fetched = inst_repo.get_by_id(inst.id)
        assert fetched.status == "FINAL"


class TestRetainedEarningsRepository:
    def test_create_and_get(self, re_repo):
        cid = uuid4()
        fyid = uuid4()
        re = RetainedEarnings(
            company_id=cid,
            fiscal_year_id=fyid,
            opening_balance=Decimal(1000),
            net_income=Decimal(500),
            dividends=Decimal(100),
        )
        re_repo.create(re)
        fetched = re_repo.get_by_fiscal_year(cid, fyid)
        assert fetched is not None
        assert fetched.opening_balance == Decimal(1000)
        assert fetched.net_income == Decimal(500)
        assert fetched.dividends == Decimal(100)

    def test_update(self, re_repo):
        cid = uuid4()
        fyid = uuid4()
        re = RetainedEarnings(company_id=cid, fiscal_year_id=fyid)
        re_repo.create(re)
        re.net_income = Decimal(200)
        re_repo.update(re)
        fetched = re_repo.get_by_fiscal_year(cid, fyid)
        assert fetched.net_income == Decimal(200)
