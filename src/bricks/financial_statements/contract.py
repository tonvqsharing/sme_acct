"""Financial Statements port — public interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.financial_statements.domain import (
    ReportInstance,
    ReportTemplate,
    ReportTemplateLine,
    RetainedEarnings,
)


class ReportTemplateRepositoryPort(ABC):
    @abstractmethod
    def create(self, template: ReportTemplate) -> ReportTemplate: ...

    @abstractmethod
    def get_by_id(self, template_id: UUID) -> ReportTemplate | None: ...

    @abstractmethod
    def get_by_code(self, code: str, company_id: UUID | None = None) -> ReportTemplate | None: ...

    @abstractmethod
    def list_templates(self, company_id: UUID | None = None) -> list[ReportTemplate]: ...

    @abstractmethod
    def update(self, template: ReportTemplate) -> ReportTemplate: ...

    @abstractmethod
    def create_line(self, line: ReportTemplateLine) -> ReportTemplateLine: ...

    @abstractmethod
    def get_lines(self, template_id: UUID) -> list[ReportTemplateLine]: ...


class ReportInstanceRepositoryPort(ABC):
    @abstractmethod
    def create(self, instance: ReportInstance) -> ReportInstance: ...

    @abstractmethod
    def get_by_id(self, instance_id: UUID) -> ReportInstance | None: ...

    @abstractmethod
    def list_by_template(self, template_id: UUID, company_id: UUID) -> list[ReportInstance]: ...

    @abstractmethod
    def update(self, instance: ReportInstance) -> ReportInstance: ...


class RetainedEarningsRepositoryPort(ABC):
    @abstractmethod
    def create(self, re: RetainedEarnings) -> RetainedEarnings: ...

    @abstractmethod
    def get_by_fiscal_year(
        self, company_id: UUID, fiscal_year_id: UUID
    ) -> RetainedEarnings | None: ...

    @abstractmethod
    def update(self, re: RetainedEarnings) -> RetainedEarnings: ...
