# Specs — Currencies & Exchange Rates Module

| | |
|---|---|
| Version | 0.1 |
| Date | 2026-08-18 |
| Status | DRAFT |
| Related | brd-currencies.md, rules-currencies.md, ADR-003 |

## 1. Architecture placement

Follows existing Lego Brick architecture (see AGENTS.md, company-module pattern):

```
src/bricks/
  currencies/                  ← 🧱 EXISTING brick
    contract.py                ← 🔌 Public interface (CurrencyCode, RateType, primitive IDs only)
    domain.py                  ← 🎯 Currency, ExchangeRate, FXDifference, RevaluationRun (pure Python)
    services.py                ← ⚙️ CurrencyService, ExchangeRateService, RevaluationService
    storage.py                 ← 💾 SQLAlchemy models + repository adapters
    web_adapter.py             ← 🌐 Flask blueprint + REST endpoints (currencies_bp)
```

**Brick boundaries:**
- `domain.py` — pure Python; NO Flask, NO SQLAlchemy, NO flask_login imports
- `contract.py` — public interface; accepts/returns only `str`, `int`, `float`, `dict`, `Decimal`, `UUID`
- `storage.py` — SQLAlchemy models + repo adapters (the ONLY file with SQLAlchemy imports)
- `services.py` — orchestration with injected port; no Flask/SQLAlchemy imports
- `web_adapter.py` — Flask blueprint; `@login_required` + `current_user.role` checks (no Casbin)
    database/
      models.py          # CurrencyModel, ExchangeRateModel, RevaluationRunModel,
                         # RevaluationEntryModel, FXDifferenceModel
    repositories/
      currency_repo.py   # SQLAlchemy adapters
    fx/
      nhnn_source.py     # NHNN rate fetcher (v1.5), CSV importer (v1)
  presentation/
    api/
      currencies_bp.py   # REST endpoints + @login_required + current_user.role
    serializers/
      currency_serializer.py
```

## 2. Domain model

### 2.1 Currency (entity)

```python
@dataclass(frozen=True)
class Currency:
    code: str            # ISO 4217, uppercase, 3 chars
    name: str
    symbol: str
    decimal_places: int  # 2 for most, 0 for JPY/VND
    is_base: bool = False
    is_active: bool = True
    display_format: str = "{symbol} {amount:,.2f}"
```

Rules:
- code matches `^[A-Z]{3}$` (ISO 4217).
- VND = base, decimal_places=0, immutable once transactions exist.
- Base currency per company, stored in CompanyConfig (`base_currency`, default VND).

### 2.2 ExchangeRate (entity)

```python
@dataclass(frozen=True)
class ExchangeRate:
    currency_code: str
    rate_date: date
    rate_type: RateType      # BUY, SELL, TRANSFER, CENTRAL, BOOKING
    rate: Decimal            # VND per 1 unit foreign currency (default orientation)
    source: str              # MANUAL | CSV_IMPORT | NHNN | BANK
    actor: UUID
    created_at: datetime
    note: str | None = None
```

Rules:
- Rate valid from `rate_date` until superseded by later rate of same (currency, type)
  (Tryton pattern: rate = value valid from date; last available rate used for gaps).
- rate > 0. Rate locked when a posted transaction references it (RateLockedError).
- Rate change requires reason + actor; audit-logged.

### 2.3 FXSourceConfig (in CompanyConfig flags)

| Flag | Type | Values | Default |
|---|---|---|---|
| `base_currency` | LAW (immutable after first use) | ISO code | VND |
| `fx_rate_source` | CONFIG | MANUAL, CSV_IMPORT, NHNN, BANK | MANUAL |
| `fx_revaluation_account` | CONFIG | 413 or DIRECT | DIRECT |
| `fx_gain_account` | LAW | account code | 515 |
| `fx_loss_account` | LAW | account code | 635 |
| `fx_revaluation_approval_required` | CONFIG | bool | True |
| `fx_booking_rate_debit` | LAW | ACTUAL or WEIGHTED_AVG | ACTUAL |
| `fx_booking_rate_credit` | LAW | WEIGHTED_AVG or ACTUAL | WEIGHTED_AVG |
| `fx_nhnn_auto_sync` | CONFIG | bool | False (v1.5) |

LAW-type flags immutable without migration (FlagLockedError), per system-settings pattern.

### 2.4 Monetary item marking (invoice/voucher/bank)

Amount fields carry original currency context:

- `currency_code` (nullable; None = base currency VND)
- `amount_original` (Decimal, in original currency)
- `amount_vnd` (Decimal, converted at booking rate)
- `fx_rate` (Decimal, the rate used; immutable after post)
- `fx_rate_type` (BUY/SELL/TRANSFER/CENTRAL/BOOKING)

### 2.5 RevaluationRun (entity)

```python
@dataclass
class RevaluationRun:
    id: UUID
    company_id: UUID
    period_start: date
    period_end: date
    rate_date: date
    status: RevaluationStatus  # DRAFT, PENDING_APPROVAL, APPROVED, POSTED, REVERSED
    entries: list[RevaluationEntry]
    actor: UUID
    approver: UUID | None
    created_at: datetime
    posted_at: datetime | None
```

`RevaluationEntry`: account_code, currency_code, balance_original, rate_applied,
old_vnd_balance, new_vnd_balance, difference (gain/loss), posting_side.

## 3. Booking rate resolution (service)

`ExchangeRateService.resolve_booking_rate(entry_side, currency, rate_date, rate_type=None)`

- Debit (Nợ) side: actual transaction rate (giao dịch thực tế) — from invoice/voucher/contract.
- Credit (Có) side: weighted average (bình quân gia quyền) of the account's FX balance
  or actual rate; per CompanyConfig `fx_booking_rate_credit`.
- Weighted average: `avg = Σ(amount_original * rate) / Σ(amount_original)` over open
  FX balance of that account, computed at booking time.
- If no rate found for date, fall back to last available rate ≤ date (Tryton semantics).

## 4. Revaluation algorithm

1. Guard: period unlocked (period_locks) else PeriodLockedError.
2. Collect monetary items with currency != base at period_end:
   - FX cash, FX bank balances (revalue at bank of account for demand deposits).
   - FX receivables, FX payables.
3. Closing rate = tỷ giá mua bán chuyển khoản trung bình of NHTM nơi DN thường xuyên
   giao dịch (TT 99/2025) — per rate_date; transfer rate type.
4. For each item: `new_vnd = balance_original * closing_rate`; `diff = new_vnd - old_vnd`.
5. Build balanced journal: gain → 515 (Có), loss → 635 (Nợ) [direct];
   or TK 413 path per config.
6. Status flow: DRAFT → PENDING_APPROVAL → (approver) APPROVED → POSTED;
   REVERSED on re-run (reverse prior postings, re-apply).
7. Idempotent: re-run same period reverses prior run first.
8. Postings must balance (debit == credit, tol 0.01 — reuse Voucher.post() rule).

## 5. Data model (SQLAlchemy) — proposed

```python
class CurrencyModel(Base):
    __tablename__ = "currencies"
    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str]
    symbol: Mapped[str]
    decimal_places: Mapped[int]
    is_base: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)

class ExchangeRateModel(Base):
    __tablename__ = "exchange_rates"
    id: Mapped[UUID]
    currency_code: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    rate_date: Mapped[date]
    rate_type: Mapped[str]  # enum: BUY/SELL/TRANSFER/CENTRAL/BOOKING
    rate: Mapped[Numeric(18, 6)]
    source: Mapped[str]
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]
    note: Mapped[str | None]
    __table_args__ = UniqueConstraint("currency_code", "rate_date", "rate_type")

class RevaluationRunModel(Base):
    __tablename__ = "revaluation_runs"
    id, company_id (FK companies.id), period_start, period_end, rate_date,
    status, actor_id, approver_id, created_at, posted_at

class RevaluationEntryModel(Base):
    __tablename__ = "revaluation_entries"
    id, run_id (FK revaluation_runs.id), account_code, currency_code,
    balance_original, rate_applied, old_vnd, new_vnd, difference,
    posting_side (DEBIT/CREDIT)

class FXDifferenceModel(Base):
    __tablename__ = "fx_differences"
    id, company_id, account_code, currency_code, period_start, period_end,
    opening_original, opening_vnd, movements_original, movements_vnd,
    closing_original, closing_vnd, revaluation_adjustment, cumulative_difference
```

## 6. API endpoints (draft)

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | /api/currencies | ADMIN, ACCOUNTANT, CHIEF_ACCOUNTANT, AUDITOR | list |
| POST | /api/currencies | ADMIN | create |
| PATCH | /api/currencies/{code} | ADMIN | update/deactivate |
| GET | /api/exchange-rates?currency=&from=&to=&type= | all above | list/history |
| POST | /api/exchange-rates | ACCOUNTANT, CHIEF_ACCOUNTANT | create rate (actor required) |
| POST | /api/exchange-rates/import | ACCOUNTANT, CHIEF_ACCOUNTANT | CSV batch import |
| POST | /api/exchange-rates/sync | CHIEF_ACCOUNTANT, ADMIN | NHNN sync (v1.5) |
| POST | /api/revaluations | ACCOUNTANT, CHIEF_ACCOUNTANT | create DRAFT run |
| POST | /api/revaluations/{id}/approve | CHIEF_ACCOUNTANT | 2nd approval |
| POST | /api/revaluations/{id}/post | CHIEF_ACCOUNTANT | post journal |
| POST | /api/revaluations/{id}/reverse | CHIEF_ACCOUNTANT | reverse + re-run |
| GET | /api/revaluations/{id} | all above | detail |
| GET | /api/fx-differences?period=&currency=&account= | all above | report |
| GET | /api/config | all above | FX config (existing bp) |

All routes decorated `@login_required + current_user.role`; AUDITOR read-only; actor UUID required
for all mutations.

## 7. CSV import format

```csv
rate_date,currency,rate_type,rate,source,note
2026-08-01,USD,BUY,24700,CSV_IMPORT,import aug
2026-08-01,USD,SELL,24900,CSV_IMPORT,import aug
2026-08-01,USD,TRANSFER,24800,CSV_IMPORT,import aug
```

- Validation per row: code ISO, date parseable, rate > 0, type enum; errors collected
  as `{row: n, error: msg}`; valid rows applied only if all rows valid (atomic)
  or partial-apply with report (configurable, default atomic).

## 8. Non-functional

- Decimal(18,6) rates, Decimal(18,2) VND amounts.
- Rate history immutable; updates = new row (no in-place edit) → audit-friendly.
- Revaluation in one DB transaction; rollback on any failure.
- No SQLAlchemy/Flask imports in domain entities (lint-enforced).
- Timezone: all timestamps UTC; rate_date business date (Asia/Ho_Chi_Minh).

## 9. Version history

| Ver | Date | Change |
|---|---|---|
| 0.1 | 2026-08-18 | Initial spec draft |