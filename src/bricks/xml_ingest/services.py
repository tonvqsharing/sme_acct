"""XML invoice ingest service — bridges XML parser to PurchaseService."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from src.bricks.xml_ingest.contract import BatchIngestResult, IngestResult, XMLIngestPort
from src.bricks.xml_ingest.domain import parse_xml_invoice

logger = logging.getLogger(__name__)


class XMLIngestService(XMLIngestPort):
    """Ingests e-invoice XML files into the purchase ledger.

    Depends on PurchaseService (via thin port) — never imports purchases.storage.
    """

    def __init__(self, *, purchase_service: Any) -> None:
        self._purchase = purchase_service

    # ── single ingest ───────────────────────────────────────────────────
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
        if not actor_id or not actor_id.strip():
            return IngestResult(success=False, error="actor_id is required")
        if not reason or not reason.strip():
            return IngestResult(success=False, error="reason is required")

        # Parse XML
        try:
            parsed = parse_xml_invoice(xml_bytes)
        except ValueError as exc:
            return IngestResult(success=False, error=f"XML parse error: {exc}")
        except ET.ParseError as exc:
            return IngestResult(success=False, error=f"XML malformed: {exc}")

        # Determine entry date
        try:
            entry_dt = date.fromisoformat(entry_date) if entry_date else datetime.now(tz=UTC).date()
        except ValueError:
            return IngestResult(success=False, error=f"Invalid entry_date: {entry_date}")

        # Build lines for PurchaseService
        lines: list[dict[str, str]] = []
        warnings: list[str] = []
        for i, line in enumerate(parsed.lines):
            account = default_expense_account
            if not account:
                warnings.append(f"Line {i + 1}: no expense_account, using empty")
                account = ""
            lines.append(
                {
                    "expense_account": account,
                    "description": line.name,
                    "amount_pre_vat": str(line.amount),
                    "vat_rate": str(line.vat_rate),
                    "deductible": "True",
                }
            )

        if not lines:
            return IngestResult(
                success=False,
                invoice_number=parsed.invoice_number,
                supplier_name=parsed.seller_name,
                supplier_mst=parsed.seller_mst,
                error="No line items in XML",
            )

        # Invoice date from XML; fallback to entry_date
        inv_date = parsed.invoice_date or entry_dt

        # Call PurchaseService
        try:
            inv = self._purchase.create_invoice(
                company_id=UUID(company_id),
                supplier_name=parsed.seller_name,
                supplier_mst=parsed.seller_mst,
                invoice_number=parsed.invoice_number,
                invoice_symbol=parsed.invoice_symbol,
                invoice_date=inv_date,
                entry_date=entry_dt,
                lines=lines,
                actor=UUID(actor_id),
                reason=reason,
            )
            return IngestResult(
                success=True,
                invoice_number=parsed.invoice_number,
                supplier_name=parsed.seller_name,
                supplier_mst=parsed.seller_mst,
                total_after_vat=str(inv.total_payment),
                purchase_invoice_id=str(inv.id),
                warnings=warnings,
            )
        except (
            ValueError,
            KeyError,
        ) as exc:
            return IngestResult(
                success=False,
                invoice_number=parsed.invoice_number,
                supplier_name=parsed.seller_name,
                supplier_mst=parsed.seller_mst,
                error=str(exc),
                warnings=warnings,
            )

    # ── batch ingest ────────────────────────────────────────────────────
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
        result = BatchIngestResult(total_files=len(files))
        for f in files:
            single = self.ingest_single(
                company_id=company_id,
                xml_bytes=f["content"],
                default_expense_account=default_expense_account,
                entry_date=entry_date,
                actor_id=actor_id,
                reason=reason,
            )
            result.results.append(single)
            if single.success:
                result.success_count += 1
            else:
                result.error_count += 1
        return result
