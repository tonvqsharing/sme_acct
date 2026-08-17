"""UI blueprint stubs (templates + routes)."""

from __future__ import annotations

from flask import Blueprint

ui_bp = Blueprint("ui", __name__)


@ui_bp.get("/")
def index():
    return "<h1>Kế toán doanh nghiệp SME</h1><p>stub</p>"


@ui_bp.get("/partners")
def partners():
    return "<h1>Danh mục đối tượng</h1><p>stub</p>"


@ui_bp.get("/invoices")
def invoices():
    return "<h1>Hóa đơn</h1><p>stub</p>"


@ui_bp.get("/vouchers")
def vouchers():
    return "<h1>Chứng từ</h1><p>stub</p>"
