"""E-invoice GDT payload — pure functions. No Flask/SQLAlchemy/network.

Builds TT91/ND254-tagged XML (DLHDon/HDon/KHMSHDon/KMHHDON/SHDon/NLap/
NBan/NMua/HHDVu/THTTLTE/TTCKTM/TongCong) using the same tag vocabulary
`xml_ingest` parses, so every built payload round-trips through the
namespace-aware GDT parser. Signing/sending stay behind injected ports
in services.py — this module never touches the network or a CA.
"""

from __future__ import annotations

import hashlib
import xml.sax.saxutils as _esc
from decimal import Decimal
from typing import Any
from uuid import UUID


def _e(v: Any) -> str:
    return _esc.escape(str(v), {'"': "&quot;"})


def build_einvoice_xml(inv: Any, seller: dict[str, Any] | None = None) -> str:
    """Render invoice as GDT-compatible XML string (UTF-8, no declaration)."""
    seller = seller or {}
    lines = []
    for it in inv.items:
        rate = it.vat_rate if it.vat_rate is not None else inv.vat_rate
        eff = Decimal(0) if rate == Decimal(-1) else rate
        vat_amt = (it.amount * eff).quantize(Decimal(1))
        qty = it.quantity if it.quantity is not None else Decimal(1)
        price = it.unit_price if it.unit_price is not None else it.amount
        lines.append(
            "<HHDVuItem>"
            f"<Ten>{_e(it.description or it.account_code)}</Ten>"
            f"<SLuong>{_e(qty)}</SLuong>"
            f"<DGia>{_e(price)}</DGia>"
            f"<ThTien>{_e(it.amount)}</ThTien>"
            f"<TSuat>{_e(rate)}</TSuat>"
            f"<TSuatTien>{_e(vat_amt)}</TSuatTien>"
            "</HHDVuItem>"
        )
    return (
        "<HDon>"
        "<DLHDon>"
        "<HDon>"
        f"<KHMSHDon>{_e(inv.invoice_symbol or '')}</KHMSHDon>"
        f"<KMHHDON>{_e(inv.template_code or '')}</KMHHDON>"
        f"<SHDon>{_e(inv.number)}</SHDon>"
        f"<NLap>{_e(inv.issue_date.isoformat())}</NLap>"
        "<NBan>"
        f"<Ten>{_e(seller.get('name', ''))}</Ten>"
        f"<MST>{_e(seller.get('mst', ''))}</MST>"
        "</NBan>"
        "<NMua>"
        f"<Ten>{_e(inv.customer_name)}</Ten>"
        f"<MST>{_e(inv.customer_mst or '')}</MST>"
        "</NMua>"
        "<HHDVu>" + "".join(lines) + "</HHDVu>"
        f"<THTTLTE>{_e(inv.subtotal)}</THTTLTE>"
        f"<TTCKTM>{_e(inv.vat_amount)}</TTCKTM>"
        f"<TongCong>{_e(inv.grand_total)}</TongCong>"
        f"<DVTTe>{_e(getattr(inv, 'currency_code', 'VND') or 'VND')}</DVTTe>"
        "</HDon>"
        "</DLHDon>"
        "</HDon>"
    )


def validate_einvoice_ready(inv: Any) -> None:
    """Pre-issue guard. Raises NotPostedError / AlreadyIssuedError / ValueError."""
    from src.bricks.invoice.domain import EInvoiceStatus
    from src.bricks.invoice.services import AlreadyIssuedError, NotPostedError

    if inv.status.value != "POSTED":
        raise NotPostedError("Chỉ phát hành HĐĐT cho hóa đơn đã POSTED")
    if inv.einvoice_status != EInvoiceStatus.NOT_ISSUED:
        raise AlreadyIssuedError("HĐĐT already issued")
    if not inv.template_code or not inv.invoice_symbol:
        raise ValueError("template_code and invoice_symbol are required (ký hiệu NĐ254)")
    if not inv.items:
        raise ValueError("items must not be empty")


def mock_sign(xml_str: str, actor: UUID) -> str:
    """Deterministic mock signature (no CA). Real signer plugs in via port."""
    return hashlib.sha256(f"{xml_str}{actor}".encode()).hexdigest()


def xml_hash(xml_str: str) -> str:
    return hashlib.sha256(xml_str.encode()).hexdigest()
