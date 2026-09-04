"""8% exclusion categories as data — panel-managed, seeded from statute.

Mirrors `TaxRateCatalogService.ensure_seeded`: the NĐ174 Art.1 exclusion
set ships as seed rows per company; CHIEF/ADMIN edits win afterwards.
`is_eligible` keeps static semantics: unknown/empty → eligible.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.bricks.system_settings.rate_windows import EXCLUDED_FROM_8PCT


class CategoryExclusionService:
    def __init__(self, repo: Any, audit: Any | None = None) -> None:
        self._repo = repo
        self._audit = audit

    def _ensured(self, company_id: UUID) -> set[str]:
        rows = set(self._repo.list_categories(company_id))
        if not rows:
            for cat in sorted(EXCLUDED_FROM_8PCT):
                self._repo.add(company_id, cat)
            rows = set(self._repo.list_categories(company_id))
        return {c.lower() for c in rows}

    def is_eligible(self, company_id: UUID, category: str | None) -> bool:
        if category is None or category == "":
            return True
        return category.lower() not in self._ensured(company_id)

    def list_categories(self, company_id: UUID) -> list[str]:
        return sorted(self._ensured(company_id))

    def add_category(self, company_id: UUID, category: str, *, actor: UUID, reason: str) -> str:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        if not category or not category.strip():
            raise ValueError("category required")
        self._ensured(company_id)
        saved = self._repo.add(company_id, category.strip().lower())
        if self._audit:
            self._audit.append(
                entity_type="excluded_8pct_category",
                entity_id=company_id,
                action="ADD",
                actor_id=actor,
                reason=reason,
                after_value={"category": saved},
            )
        return saved  # type: ignore[no-any-return]

    def remove_category(self, company_id: UUID, category: str, *, actor: UUID, reason: str) -> None:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        self._ensured(company_id)
        self._repo.remove(company_id, category.strip().lower())
        if self._audit:
            self._audit.append(
                entity_type="excluded_8pct_category",
                entity_id=company_id,
                action="REMOVE",
                actor_id=actor,
                reason=reason,
                after_value={"category": category.strip().lower()},
            )
