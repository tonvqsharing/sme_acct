"""Costing engine — pure functions. No Flask/SQLAlchemy/repo access.

Each cost method (VAS 02 §13 + TT99 Standard) is one testable function.
`InventoryService` resolves inputs (stock qty/value, move history) and
delegates here — service keeps orchestration, math lives here.
"""

from __future__ import annotations

from collections import deque
from decimal import Decimal
from typing import Any


def moving_average_unit(qty: Decimal, value: Decimal, fallback: Decimal) -> Decimal:
    """Moving weighted average unit cost. Falls back when no stock."""
    if qty <= 0:
        return fallback
    avg = (value / qty).quantize(Decimal(1))
    return avg if avg > 0 else fallback


def specific_out_unit(move_cost: Decimal, standard_cost: Decimal | None) -> Decimal:
    """Specific identification: the lot's own cost, else standard, else 0."""
    if move_cost > 0:
        return move_cost
    return standard_cost or Decimal(0)


def fifo_out_unit(
    in_lots: list[tuple[Decimal, Decimal]],
    out_qty_consumed: list[Decimal],
) -> Decimal:
    """Oldest-lot unit cost after replaying consumed out quantities.

    `in_lots`: chronological (qty, unit_cost) receipts.
    `out_qty_consumed`: chronological out quantities already posted.
    Returns front-lot cost, or 0 when no lots remain.
    """
    queue: deque[tuple[Decimal, Decimal]] = deque(in_lots)
    for need_in in out_qty_consumed:
        need = need_in
        while need > 0 and queue:
            q, c = queue[0]
            if q <= need:
                need -= q
                queue.popleft()
            else:
                queue[0] = (q - need, c)
                need = Decimal(0)
    if queue:
        return queue[0][1]
    return Decimal(0)


def split_standard(
    actual_unit: Decimal, standard: Decimal, qty: Decimal
) -> tuple[Decimal, Decimal]:
    """Split a Standard-method issue into (cogs_total, variance_total).

    COGS posts at standard; variance = (actual − standard) × qty, which may
    be negative (favourable). Quantized to whole VND.
    """
    cogs = (standard * qty).quantize(Decimal(1))
    variance = ((actual_unit - standard) * qty).quantize(Decimal(1))
    return cogs, variance


def fifo_lots_from_moves(moves: list[Any]) -> tuple[list[tuple[Decimal, Decimal]], list[Decimal]]:
    """Adapt domain StockMove history to `fifo_out_unit` inputs. Pure data mapping."""
    ins: list[tuple[Decimal, Decimal]] = []
    outs: list[Decimal] = []
    for m in moves:
        if m.from_loc is None and m.to_loc is not None:
            ins.append((m.qty, m.unit_cost))
        elif m.to_loc is None and m.from_loc is not None:
            outs.append(m.qty)
    return ins, outs
