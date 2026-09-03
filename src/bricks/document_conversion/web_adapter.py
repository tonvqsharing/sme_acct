"""Flask blueprint — MarkItDown conversion. ONLY file with Flask/werkzeug imports."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, abort, jsonify, request
from flask_login import login_required

from src.bricks.document_conversion.domain import validate_file_name
from src.bricks.document_conversion.services import DocumentConversionService

bp = Blueprint("document_conversion", __name__)

_svc: DocumentConversionService | None = None


def init_document_conversion(svc: DocumentConversionService) -> None:
    global _svc
    _svc = svc


def _get_svc() -> DocumentConversionService:
    if _svc is None:
        abort(500, description="DocumentConversionService not initialized")
    return _svc


@bp.post("/api/v1/documents/convert")
@login_required  # type: ignore[untyped-decorator]
def convert_document() -> tuple[Any, int]:
    """Single file → Markdown. Form: file=<upload>, optional file_name override."""
    svc = _get_svc()
    f = request.files.get("file")
    if f is None:
        # also accept raw bytes + ?file_name=
        data = request.get_data()
        fname = request.args.get("file_name", "upload.txt")
        if not data:
            abort(422, description="file required (multipart 'file' or raw body)")
        try:
            validate_file_name(fname, len(data))
        except ValueError as exc:
            return jsonify({"error": str(exc), "code": "INVALID_FILE"}), 422
        res = svc.convert_bytes(data=data, file_name=fname)
    else:
        fname = f.filename or "upload"
        data = f.read()
        try:
            validate_file_name(fname, len(data))
        except ValueError as exc:
            return jsonify({"error": str(exc), "code": "INVALID_FILE"}), 422
        res = svc.convert_bytes(data=data, file_name=fname)
    if not res.success:
        return jsonify({"error": res.error, "code": "CONVERSION_FAILED"}), 422
    payload: dict[str, Any] = {
        "file_name": res.file_name,
        "file_type": res.file_type,
        "title": res.title,
        "markdown": res.markdown,
    }
    if res.warnings:
        payload["warnings"] = res.warnings
    return jsonify({"data": payload}), 200


@bp.post("/api/v1/documents/convert-batch")
@login_required  # type: ignore[untyped-decorator]
def convert_batch() -> tuple[Any, int]:
    """Multiple files → list of Markdown. Form: files=<multi>."""
    svc = _get_svc()
    files = request.files.getlist("files")
    if not files:
        files = request.files.getlist("file")
    if not files:
        abort(422, description="files required (multipart 'files')")
    if len(files) > 10:
        abort(422, description="Tối đa 10 files/lần")
    results: list[dict[str, Any]] = []
    for f in files:
        fname = f.filename or "upload"
        data = f.read()
        try:
            validate_file_name(fname, len(data))
        except ValueError as exc:
            results.append({"file_name": fname, "success": False, "error": str(exc)})
            continue
        res = svc.convert_bytes(data=data, file_name=fname)
        results.append(
            {
                "file_name": res.file_name,
                "file_type": res.file_type,
                "success": res.success,
                "markdown": res.markdown if res.success else "",
                "error": res.error if not res.success else "",
                "warnings": res.warnings,
            }
        )
    return jsonify({"data": results}), 200


@bp.get("/api/v1/documents/supported-types")
@login_required  # type: ignore[untyped-decorator]
def supported_types() -> tuple[Any, int]:
    from src.bricks.document_conversion.domain import ALLOWED_EXTENSIONS, MAX_BYTES

    return (
        jsonify({"data": {"extensions": sorted(ALLOWED_EXTENSIONS), "max_bytes": MAX_BYTES}}),
        200,
    )
