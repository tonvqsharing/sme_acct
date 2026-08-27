"""XML ingest web adapter — REST endpoints for uploading e-invoice XML."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

xml_ingest_bp = Blueprint("xml_ingest", __name__)

_xml_ingest_service: Any = None


def init_xml_ingest_service(svc: Any) -> None:
    global _xml_ingest_service
    _xml_ingest_service = svc


def _svc() -> Any:
    s = _xml_ingest_service
    if s is None:
        abort(500, description="XMLIngestService not initialized")
    return s


# ─── POST /api/v1/xml-ingest/single ────────────────────────────────────


@xml_ingest_bp.post("/api/v1/xml-ingest/single")
@login_required  # type: ignore[untyped-decorator]
def ingest_single() -> tuple[Any, int]:
    """Upload a single XML invoice file.

    Expects multipart/form-data with:
      - file: XML file
      - company_id: UUID string
      - default_expense_account: COA code (optional)
      - entry_date: ISO date string (optional, defaults to today)
      - reason: audit reason (optional)
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded", "code": "NO_FILE"}), 422

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected", "code": "NO_FILE"}), 422

    company_id = request.form.get("company_id", "")
    if not company_id:
        return jsonify({"error": "company_id required", "code": "MISSING_COMPANY_ID"}), 422

    result = _svc().ingest_single(
        company_id=company_id,
        xml_bytes=file.read(),
        default_expense_account=request.form.get("default_expense_account", ""),
        entry_date=request.form.get("entry_date", ""),
        actor_id=str(current_user.id),
        reason=request.form.get("reason", "XML invoice ingest"),
    )

    status = 200 if result.success else 422
    return (
        jsonify(
            {
                "success": result.success,
                "data": {
                    "invoice_number": result.invoice_number,
                    "supplier_name": result.supplier_name,
                    "supplier_mst": result.supplier_mst,
                    "total_after_vat": result.total_after_vat,
                    "purchase_invoice_id": result.purchase_invoice_id,
                },
                "error": result.error or None,
                "warnings": result.warnings,
            }
        ),
        status,
    )


# ─── POST /api/v1/xml-ingest/batch ─────────────────────────────────────


@xml_ingest_bp.post("/api/v1/xml-ingest/batch")
@login_required  # type: ignore[untyped-decorator]
def ingest_batch() -> tuple[Any, int]:
    """Upload multiple XML invoice files.

    Expects multipart/form-data with:
      - files: multiple XML files
      - company_id: UUID string
      - default_expense_account: COA code (optional)
      - entry_date: ISO date string (optional)
      - reason: audit reason (optional)
    """
    files = request.files.getlist("files")
    if not files or all(not f.filename for f in files):
        return jsonify({"error": "No files uploaded", "code": "NO_FILES"}), 422

    company_id = request.form.get("company_id", "")
    if not company_id:
        return jsonify({"error": "company_id required", "code": "MISSING_COMPANY_ID"}), 422

    file_dicts = []
    for f in files:
        if f.filename:
            file_dicts.append({"filename": f.filename, "content": f.read()})

    result = _svc().ingest_batch(
        company_id=company_id,
        files=file_dicts,
        default_expense_account=request.form.get("default_expense_account", ""),
        entry_date=request.form.get("entry_date", ""),
        actor_id=str(current_user.id),
        reason=request.form.get("reason", "XML batch ingest"),
    )

    return (
        jsonify(
            {
                "total_files": result.total_files,
                "success_count": result.success_count,
                "error_count": result.error_count,
                "results": [
                    {
                        "success": r.success,
                        "invoice_number": r.invoice_number,
                        "supplier_name": r.supplier_name,
                        "supplier_mst": r.supplier_mst,
                        "total_after_vat": r.total_after_vat,
                        "purchase_invoice_id": r.purchase_invoice_id,
                        "error": r.error or None,
                        "warnings": r.warnings,
                    }
                    for r in result.results
                ],
            }
        ),
        200,
    )
