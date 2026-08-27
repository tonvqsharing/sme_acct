"""Public port — xml_ingest brick."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IngestResult:
    """Result of a single XML invoice ingest attempt."""

    success: bool
    invoice_number: str = ""
    supplier_name: str = ""
    supplier_mst: str = ""
    total_after_vat: str = "0"
    purchase_invoice_id: str = ""
    error: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class BatchIngestResult:
    """Result of a batch XML ingest."""

    total_files: int = 0
    success_count: int = 0
    error_count: int = 0
    results: list[IngestResult] = field(default_factory=list)


class XMLIngestPort(ABC):
    """Port for ingesting XML invoices into the purchase ledger."""

    @abstractmethod
    def ingest_single(
        self,
        *,
        company_id: str,
        xml_bytes: bytes,
        default_expense_account: str = "",
        entry_date: str = "",
        actor_id: str = "",
        reason: str = "",
    ) -> IngestResult:
        """Parse XML and create a purchase invoice.

        Args:
            company_id: Target company UUID string
            xml_bytes: Raw XML content
            default_expense_account: Fallback COA code for lines without account
            entry_date: Override entry date (ISO); defaults to today
            actor_id: Actor UUID string (required)
            reason: Audit reason (required)

        Returns:
            IngestResult with success/error status
        """
        ...

    @abstractmethod
    def ingest_batch(
        self,
        *,
        company_id: str,
        files: list[dict[str, Any]],
        default_expense_account: str = "",
        entry_date: str = "",
        actor_id: str = "",
        reason: str = "",
    ) -> BatchIngestResult:
        """Ingest multiple XML files.

        Args:
            files: list of {"filename": str, "content": bytes}

        Returns:
            BatchIngestResult with per-file results
        """
        ...
