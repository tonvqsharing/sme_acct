"""Port — system settings."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.system_settings.domain import CompanyConfig


class SystemSettingsRepositoryPort(ABC):
    @abstractmethod
    def get_config(self, company_id: UUID) -> CompanyConfig: ...
    @abstractmethod
    def update_config(self, cfg: CompanyConfig) -> CompanyConfig: ...
