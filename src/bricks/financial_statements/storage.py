"""Financial Statements storage — SQLAlchemy adapter."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import JSON

from src.bricks.financial_statements.contract import (
    ReportInstanceRepositoryPort,
    ReportTemplateRepositoryPort,
    RetainedEarningsRepositoryPort,
)
from src.bricks.financial_statements.domain import (
    LineType,
    ReportInstance,
    ReportInstanceLine,
    ReportTemplate,
    ReportTemplateLine,
    RetainedEarnings,
)


class Base(DeclarativeBase):
    pass


class ReportTemplateModel(Base):
    __tablename__ = "report_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(10), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500), default="")
    company_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)


class ReportTemplateLineModel(Base):
    __tablename__ = "report_template_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    template_id: Mapped[str] = mapped_column(String(36), ForeignKey("report_templates.id"))
    line_code: Mapped[str] = mapped_column(String(20))
    line_name: Mapped[str] = mapped_column(String(200))
    line_type: Mapped[str] = mapped_column(String(20))
    account_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    formula: Mapped[str | None] = mapped_column(String(500), nullable=True)
    parent_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    level: Mapped[int] = mapped_column(default=0)
    sort_order: Mapped[int] = mapped_column(default=0)
    sign: Mapped[int] = mapped_column(default=1)


class ReportInstanceModel(Base):
    __tablename__ = "report_instances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    template_id: Mapped[str] = mapped_column(String(36), ForeignKey("report_templates.id"))
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    period_from: Mapped[date] = mapped_column(Date)
    period_to: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10), default="DRAFT")


class ReportInstanceLineModel(Base):
    __tablename__ = "report_instance_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    instance_id: Mapped[str] = mapped_column(String(36), ForeignKey("report_instances.id"))
    line_code: Mapped[str] = mapped_column(String(20))
    line_name: Mapped[str] = mapped_column(String(200))
    value_current: Mapped[Decimal] = mapped_column(default=Decimal(0))
    value_prior: Mapped[Decimal | None] = mapped_column(nullable=True)


class RetainedEarningsModel(Base):
    __tablename__ = "retained_earnings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    fiscal_year_id: Mapped[str] = mapped_column(String(36))
    opening_balance: Mapped[Decimal] = mapped_column(default=Decimal(0))
    net_income: Mapped[Decimal] = mapped_column(default=Decimal(0))
    dividends: Mapped[Decimal] = mapped_column(default=Decimal(0))
    checksum: Mapped[str] = mapped_column(String(64), default="")

    __table_args__ = (UniqueConstraint("company_id", "fiscal_year_id"),)


def _template_to_domain(m: ReportTemplateModel) -> ReportTemplate:
    return ReportTemplate(
        id=UUID(m.id),
        code=m.code,
        name=m.name,
        description=m.description,
        company_id=UUID(m.company_id) if m.company_id else None,
        is_active=m.is_active,
    )


def _line_to_domain(m: ReportTemplateLineModel) -> ReportTemplateLine:
    return ReportTemplateLine(
        id=UUID(m.id),
        template_id=UUID(m.template_id),
        line_code=m.line_code,
        line_name=m.line_name,
        line_type=LineType(m.line_type),
        account_codes=m.account_codes or [],
        formula=m.formula,
        parent_code=m.parent_code,
        level=m.level,
        sort_order=m.sort_order,
        sign=m.sign,
    )


def _instance_to_domain(m: ReportInstanceModel) -> ReportInstance:
    return ReportInstance(
        id=UUID(m.id),
        template_id=UUID(m.template_id),
        company_id=UUID(m.company_id),
        period_from=m.period_from,
        period_to=m.period_to,
        status=m.status,
    )


def _instance_line_to_domain(m: ReportInstanceLineModel) -> ReportInstanceLine:
    return ReportInstanceLine(
        id=UUID(m.id),
        instance_id=UUID(m.instance_id),
        line_code=m.line_code,
        line_name=m.line_name,
        value_current=m.value_current,
        value_prior=m.value_prior,
    )


def _re_to_domain(m: RetainedEarningsModel) -> RetainedEarnings:
    return RetainedEarnings(
        id=UUID(m.id),
        company_id=UUID(m.company_id),
        fiscal_year_id=UUID(m.fiscal_year_id),
        opening_balance=m.opening_balance,
        net_income=m.net_income,
        dividends=m.dividends,
        checksum=m.checksum,
    )


class SQLAlchemyReportTemplateRepository(ReportTemplateRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, template: ReportTemplate) -> ReportTemplate:
        self._session.add(
            ReportTemplateModel(
                id=str(template.id),
                code=template.code,
                name=template.name,
                description=template.description,
                company_id=str(template.company_id) if template.company_id else None,
                is_active=template.is_active,
            )
        )
        self._session.commit()
        return template

    def get_by_id(self, template_id: UUID) -> ReportTemplate | None:
        m = self._session.get(ReportTemplateModel, str(template_id))
        return _template_to_domain(m) if m else None

    def get_by_code(self, code: str, company_id: UUID | None = None) -> ReportTemplate | None:
        query = self._session.query(ReportTemplateModel).filter(ReportTemplateModel.code == code)
        if company_id is not None:
            query = query.filter(ReportTemplateModel.company_id == str(company_id))
        m = query.first()
        return _template_to_domain(m) if m else None

    def list_templates(self, company_id: UUID | None = None) -> list[ReportTemplate]:
        query = self._session.query(ReportTemplateModel)
        if company_id is not None:
            query = query.filter(ReportTemplateModel.company_id == str(company_id))
        return [_template_to_domain(m) for m in query.all()]

    def update(self, template: ReportTemplate) -> ReportTemplate:
        m = self._session.get(ReportTemplateModel, str(template.id))
        if m is None:
            raise ValueError(f"Template {template.code} not found")
        m.name = template.name
        m.description = template.description
        m.is_active = template.is_active
        self._session.commit()
        return template

    def create_line(self, line: ReportTemplateLine) -> ReportTemplateLine:
        self._session.add(
            ReportTemplateLineModel(
                id=str(line.id),
                template_id=str(line.template_id),
                line_code=line.line_code,
                line_name=line.line_name,
                line_type=line.line_type.value,
                account_codes=line.account_codes,
                formula=line.formula,
                parent_code=line.parent_code,
                level=line.level,
                sort_order=line.sort_order,
                sign=line.sign,
            )
        )
        self._session.commit()
        return line

    def get_lines(self, template_id: UUID) -> list[ReportTemplateLine]:
        rows = (
            self._session.query(ReportTemplateLineModel)
            .filter(ReportTemplateLineModel.template_id == str(template_id))
            .order_by(ReportTemplateLineModel.sort_order.asc())
            .all()
        )
        return [_line_to_domain(r) for r in rows]


class SQLAlchemyReportInstanceRepository(ReportInstanceRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, instance: ReportInstance) -> ReportInstance:
        self._session.add(
            ReportInstanceModel(
                id=str(instance.id),
                template_id=str(instance.template_id),
                company_id=str(instance.company_id),
                period_from=instance.period_from,
                period_to=instance.period_to,
                status=instance.status,
            )
        )
        self._session.commit()
        return instance

    def get_by_id(self, instance_id: UUID) -> ReportInstance | None:
        m = self._session.get(ReportInstanceModel, str(instance_id))
        return _instance_to_domain(m) if m else None

    def list_by_template(self, template_id: UUID, company_id: UUID) -> list[ReportInstance]:
        rows = (
            self._session.query(ReportInstanceModel)
            .filter(
                ReportInstanceModel.template_id == str(template_id),
                ReportInstanceModel.company_id == str(company_id),
            )
            .all()
        )
        return [_instance_to_domain(r) for r in rows]

    def update(self, instance: ReportInstance) -> ReportInstance:
        m = self._session.get(ReportInstanceModel, str(instance.id))
        if m is None:
            raise ValueError(f"Instance {instance.id} not found")
        m.status = instance.status
        self._session.commit()
        return instance

    def create_line(self, line: ReportInstanceLine) -> ReportInstanceLine:
        self._session.add(
            ReportInstanceLineModel(
                id=str(line.id),
                instance_id=str(line.instance_id),
                line_code=line.line_code,
                line_name=line.line_name,
                value_current=line.value_current,
                value_prior=line.value_prior,
            )
        )
        self._session.commit()
        return line

    def get_lines(self, instance_id: UUID) -> list[ReportInstanceLine]:
        rows = (
            self._session.query(ReportInstanceLineModel)
            .filter(ReportInstanceLineModel.instance_id == str(instance_id))
            .all()
        )
        return [_instance_line_to_domain(r) for r in rows]

    def save_instance(
        self, instance: ReportInstance, lines: list[ReportInstanceLine]
    ) -> ReportInstance:
        """Atomically create/update instance + replace all lines."""
        existing = self._session.get(ReportInstanceModel, str(instance.id))
        if existing is None:
            self._session.add(
                ReportInstanceModel(
                    id=str(instance.id),
                    template_id=str(instance.template_id),
                    company_id=str(instance.company_id),
                    period_from=instance.period_from,
                    period_to=instance.period_to,
                    status=instance.status,
                )
            )
        else:
            existing.status = instance.status

        # Delete old lines for idempotent recompute
        self._session.query(ReportInstanceLineModel).filter(
            ReportInstanceLineModel.instance_id == str(instance.id)
        ).delete()

        # Insert new lines
        for line in lines:
            self._session.add(
                ReportInstanceLineModel(
                    id=str(line.id),
                    instance_id=str(instance.id),
                    line_code=line.line_code,
                    line_name=line.line_name,
                    value_current=line.value_current,
                    value_prior=line.value_prior,
                )
            )

        self._session.commit()
        return instance


class SQLAlchemyRetainedEarningsRepository(RetainedEarningsRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, re: RetainedEarnings) -> RetainedEarnings:
        self._session.add(
            RetainedEarningsModel(
                id=str(re.id),
                company_id=str(re.company_id),
                fiscal_year_id=str(re.fiscal_year_id),
                opening_balance=re.opening_balance,
                net_income=re.net_income,
                dividends=re.dividends,
                checksum=re.checksum,
            )
        )
        self._session.commit()
        return re

    def get_by_fiscal_year(self, company_id: UUID, fiscal_year_id: UUID) -> RetainedEarnings | None:
        m = (
            self._session.query(RetainedEarningsModel)
            .filter(
                RetainedEarningsModel.company_id == str(company_id),
                RetainedEarningsModel.fiscal_year_id == str(fiscal_year_id),
            )
            .first()
        )
        return _re_to_domain(m) if m else None

    def update(self, re: RetainedEarnings) -> RetainedEarnings:
        m = self._session.get(RetainedEarningsModel, str(re.id))
        if m is None:
            raise ValueError(f"RetainedEarnings {re.id} not found")
        m.opening_balance = re.opening_balance
        m.net_income = re.net_income
        m.dividends = re.dividends
        m.checksum = re.checksum
        self._session.commit()
        return re
