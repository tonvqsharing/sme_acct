"""Application service for Company aggregate — business orchestration.

Follows Clean Architecture: depends only on repository ports (from application.ports)
and domain entities/exceptions. No Flask or SQLAlchemy imports here.
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from src.application.ports import CompanyRepositoryPort
from src.domain.entities.company import Company, CompanyStatus
from src.domain.exceptions import (
    CompanyLockedError,
    CompanyNotFoundError,
    DuplicateMSTError,
)

logger = logging.getLogger(__name__)


class CompanyService:
    """Orchestrates Company aggregate lifecycle and business rules.

    Each method is a single business transaction:
    - validate via domain entity invariants
    - mutate and persist via repository
    - raise domain exceptions — Presentation layer handles HTTP translation
    """

    def __init__(
        self,
        company_repo: CompanyRepositoryPort,
    ) -> None:
        self._company_repo = company_repo

    # ── Creation ────────────────────────────────────────────────────────────

    def create_company(
        self,
        *,
        actor: UUID,
        **company_kwargs,
    ) -> Company:
        """Create a new company record.

        Domain entity validates all business invariants in __post_init__.
        Repository enforces MST uniqueness at DB level.

        Args:
            actor: User UUID of the operator performing this action.
            **company_kwargs: All Company field values (see Company dataclass).

        Returns:
            Persisted Company with auto-assigned id and timestamps.

        Raises:
            DuplicateMSTError: If MST already registered (propagated from repo).
            ValueError: If domain invariant violated (propagated from Company.__post_init__).
        """
        logger.info("Creating company", extra={"actor": str(actor)})

        company_kwargs["created_by"] = actor
        company_kwargs["updated_by"] = actor

        company = Company(**company_kwargs)
        saved = self._company_repo.create(company)

        logger.info(
            "Company created",
            extra={"company_id": str(saved.id), "mst": str(saved.mst)},
        )
        return saved

    # ── Read ─────────────────────────────────────────────────────────────────

    def get_company(self, company_id: UUID) -> Company:
        """Fetch company by id.

        Raises:
            CompanyNotFoundError: If no company with that id exists.
        """
        company = self._company_repo.get_by_id(company_id)
        if company is None:
            raise CompanyNotFoundError(
                f"Không tìm thấy đơn vị kế toán: {company_id}"
            )
        return company

    # ── Update ───────────────────────────────────────────────────────────────

    def update_company(
        self,
        company_id: UUID,
        actor: UUID,
        **changes,
    ) -> Company:
        """Apply partial update to a company record.

        Args:
            company_id: Target company.
            actor: User performing the change.
            **changes: Field names and new values to apply.

        Returns:
            Updated Company.

        Raises:
            CompanyNotFoundError: If company doesn't exist.
            CompanyLockedError: If company is SUSPENDED or DISSOLVED.
            ValueError: If resulting state violates domain invariant.
        """
        company = self._company_repo.get_by_id(company_id)
        if company is None:
            raise CompanyNotFoundError(
                f"Không tìm thấy đơn vị kế toán: {company_id}"
            )

        if company.status in (CompanyStatus.SUSPENDED, CompanyStatus.DISSOLVED):
            raise CompanyLockedError(
                f"Không thể chỉnh sửa đơn vị {company.legal_name} "
                f"(trạng thái: {company.status.value})"
            )

        for field, value in changes.items():
            if not hasattr(company, field):
                raise AttributeError(
                    f"Company has no field '{field}'"
                )
            object.__setattr__(company, field, value)

        # Re-validate domain invariants after mutation
        company.__post_init__()

        company.updated_by = actor
        updated = self._company_repo.update(company)

        logger.info(
            "Company updated",
            extra={"company_id": str(company_id), "actor": str(actor)},
        )
        return updated

    # ── Lifecycle: deactivate / dissolve ─────────────────────────────────────

    def deactivate_company(self, company_id: UUID, actor: UUID) -> Company:
        """Suspend a company (set SUSPENDED → no new transactions allowed).

        Raises:
            CompanyNotFoundError: If company doesn't exist.
            CompanyLockedError: If already dissolved.
        """
        company = self._company_repo.get_by_id(company_id)
        if company is None:
            raise CompanyNotFoundError(
                f"Không tìm thấy đơn vị kế toán: {company_id}"
            )

        company.deactivate()
        company.updated_by = actor
        updated = self._company_repo.update(company)

        logger.info(
            "Company deactivated",
            extra={"company_id": str(company_id), "actor": str(actor)},
        )
        return updated

    def dissolve_company(self, company_id: UUID, actor: UUID) -> Company:
        """Permanently dissolve a company (irreversible).

        Raises:
            CompanyNotFoundError: If company doesn't exist.
            CompanyLockedError: If already dissolved.
        """
        company = self._company_repo.get_by_id(company_id)
        if company is None:
            raise CompanyNotFoundError(
                f"Không tìm thấy đơn vị kế toán: {company_id}"
            )

        if company.status == CompanyStatus.DISSOLVED:
            raise CompanyLockedError("Đơn vị đã giải thể")

        company.dissolve()
        company.updated_by = actor
        updated = self._company_repo.update(company)

        logger.info(
            "Company dissolved",
            extra={"company_id": str(company_id), "actor": str(actor)},
        )
        return updated

    # ── Validation helpers (used by other services) ──────────────────────────

    def validate_active_for_transaction(self, company_id: UUID) -> None:
        """Block new transactions for SUSPENDED or DISSOLVED companies.

        Called by InvoiceService and VoucherService before accepting entries.

        Raises:
            CompanyNotFoundError: If company doesn't exist.
            CompanyLockedError: If company cannot accept new transactions.
        """
        company = self._company_repo.get_by_id(company_id)
        if company is None:
            raise CompanyNotFoundError(
                f"Không tìm thấy đơn vị kế toán: {company_id}"
            )
        company.validate_active_for_transaction()