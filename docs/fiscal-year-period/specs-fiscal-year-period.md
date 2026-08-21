# Fiscal Years & Accounting Periods Module — Technical Spec

## 1. Overview

Extend Lego Brick architecture with a real fiscal-year/period domain. Replace the
stub `PeriodLockService`, rebuild `period_locks` table, add `FiscalYear` /
`AccountingPeriod` entities, enforcement hooks on posting services, and a REST
API following the currencies-blueprint pattern (test-engine hooks,
`@login_required + current_user.role`, `_req_session`).

## 2. Brick Position

```
src/bricks/
  fiscal_year_period/          ← 🧱 NEW brick
    contract.py                ← 🔌 Public interface (FiscalYearCode, PeriodCode, primitive IDs only)
    domain.py                  ← 🎯 FiscalYear, AccountingPeriod, PeriodLock entities (pure Python)
    services.py                ← ⚙️ FiscalYearService, PeriodLockService
    storage.py                 ← 💾 SQLAlchemy models + repository adapters
    web_adapter.py             ← 🌐 Flask blueprint + REST endpoints (fiscal_year_bp)
```

**Brick boundaries:**
- `domain.py` — pure Python; NO Flask, NO SQLAlchemy, NO flask_login imports
- `contract.py` — public interface; accepts/returns only `str`, `int`, `float`, `dict`, `Decimal`, `UUID`
- `storage.py` — SQLAlchemy models + repo adapters (the ONLY file with SQLAlchemy imports)
- `services.py` — orchestration with injected port; no Flask/SQLAlchemy imports
- `web_adapter.py` — Flask blueprint; `@login_required` + `current_user.role` checks (no Casbin)

## 3. Domain layer (`src/bricks/fiscal_year_period/domain.py`)

### 3.1 Enums (extend `src/bricks/fiscal_year_period/domain.py`)

Replace the current `AccountingPeriodType` (has illegal `FISCAL_15`):

```python
class AccountingPeriodType(Enum):
    CALENDAR = "CALENDAR"          # 01/01 – 31/12
    FISCAL_APR = "FISCAL_APR"      # 01/04 – 31/03
    FISCAL_JUL = "FISCAL_JUL"      # 01/07 – 30/06
    FISCAL_OCT = "FISCAL_OCT"      # 01/10 – 30/09
    # NOTE: FISCAL_15 (15-month, mid-quarter start) is ILLEGAL per
    # Luật 88/2015 Điều 12 — removed. Migration handles legacy data.
```

New enums:

```python
class PeriodStatus(Enum):
    OPEN = "OPEN"            # accepting entries
    LOCKED = "LOCKED"        # closed, entries blocked
    YEAR_CLOSED = "YEAR_CLOSED"  # fiscal year fully closed

class PeriodLockAction(Enum):
    CLOSE = "CLOSE"
    REOPEN = "REOPEN"
    YEAR_END = "YEAR_END"

class LockScope(Enum):
    PERIOD = "PERIOD"        # whole period (default)
    JOURNAL = "JOURNAL"      # per-journal lock (enhancement, Tryton parity)
```

Mirror all three in `src/bricks/fiscal_year_period/storage.py` (duplication rule).

### 3.2 Entities

`FiscalYear` (aggregate root):
- `id: UUID`, `company_id: UUID`, `year_code: str` (e.g. `"2026"`, `"FY2026"`),
  `period_type: AccountingPeriodType`, `start_date: date`, `end_date: date`,
  `is_first_period: bool` (≤ 15 months), `status: PeriodStatus`,
  `opening_balance_posted: bool`, `closed_by/at`, `created_at/updated_at`.
- Methods: `periods()`, `period_for_date(d)`, `is_locked(d)`, `close()`,
  `reopen(reason, actor)`, `build_opening_balances()`.

`AccountingPeriod`:
- `id: UUID`, `fiscal_year_id: FK`, `period_number: int` (1..12 or 1 for
  merged/first), `label: str` (e.g. "Tháng 01/2026"), `start_date`, `end_date`,
  `status: PeriodStatus`, `locked_by/at`, `unlocked_by/at`, `lock_reason`.
- Invariant: periods of a fiscal year are contiguous and non-overlapping;
  concatenation = fiscal year span; no period < 90 days.

`PeriodLockEvent` (append-only history):
- `id`, `period_id`, `action: PeriodLockAction`, `requested_by`,
  `approved_by`, `requested_at`, `approved_at`, `reason`, `approval_ref`,
  `checksum` (SHA-256 chain, audit-log parity).

### 3.3 Exceptions (in `src/bricks/fiscal_year_period/domain.py`)
- `PeriodLockedError(period_id, date)` — posting into locked period.
- `InvalidFiscalYearError` — non-quarter-aligned start, wrong length.
- `PeriodNotClosableError` — open entries / prerequisites missing.
- `YearEndPreconditionsError` — periods not all locked.
- `SelfApprovalError` — SOD violation.
- `PeriodTransitionError` — illegal state transition.
- `FiscalYearExistsError` — duplicate year_code.

## 4. Services layer (`src/bricks/fiscal_year_period/services.py`)

### 4.1 FiscalYearService

```python
class FiscalYearRepositoryPort(Protocol):
    def get_by_id(self, fiscal_year_id: UUID) -> FiscalYear | None: ...
    def get_active(self, company_id: UUID, entry_date: date) -> FiscalYear | None: ...
    def period_for_date(self, company_id: UUID, entry_date: date) -> AccountingPeriod | None: ...
    def save(self, fy: FiscalYear) -> None: ...
    def list_by_company(self, company_id: UUID) -> list[FiscalYear]: ...

class PeriodLockRepositoryPort(Protocol):
    def is_locked(self, company_id: UUID, period_start: date, period_end: date) -> bool: ...
    def lock(self, period_id: UUID, actor: UUID, reason: str) -> PeriodLockEvent: ...
    def reopen(self, period_id: UUID, actor: UUID, reason: str) -> PeriodLockEvent: ...
    def history(self, period_id: UUID) -> list[PeriodLockEvent]: ...
```

### 4.2 PeriodLockService (full rewrite)

- `is_locked(company_id, entry_date) -> bool`
- `validate_before_entry(company_id, entry_date, actor)` — raises
  `PeriodLockedError`; **called by every posting service**:
  `VoucherService.post`, `InvoiceService.*`, `RevaluationService.create_run`,
  `ExchangeRateService` CSV import.
- `close_period(period_id, actor, reason) -> PeriodLockEvent` — SOD: if
  approver == requester → `SelfApprovalError`.
- `reopen_period(period_id, actor, reason) -> PeriodLockEvent` — requires
  `period.reopen` permission + non-empty reason.
- `close_fiscal_year(fiscal_year_id, actor) -> OpeningBalancesResult` —
  preconditions R-08, runs kết chuyển 911/421 (calls a
  `YearEndClosingService`), posts opening balances to new year.
- `create_fiscal_year(company_id, period_type, start_date, actor) -> FiscalYear`
  — validates quarter alignment + 12-month length (R-01/R-02).
- `change_fiscal_year(company_id, new_period_type, actor) -> ChangeResult` —
  per A2/A4: close old year → transition BCTC snapshot → new fiscal year with
  "Số đầu năm" opening balances.
- Remove the `SystemSettingsService.lock_period/unlock_period` duplicate —
  route through this service (or keep as thin delegators).

### 4.3 Enforcement integration

| Caller | Hook |
|---|---|
| `VoucherService.post` | `validate_before_entry(company, voucher.date, actor)` |
| `InvoiceService` (create/update) | same |
| `RevaluationService.create_run` | existing `PeriodLockedError` path kept, now backed by real repo |
| `ExchangeRateService` CSV import | validate each row date before bulk insert |
| `CompanyService` (dissolve) | require current period state consistent with dissolution (A1) |

## 5. Storage layer (`src/bricks/fiscal_year_period/storage.py`)

### 5.1 Models — rebuild `period_locks` (currently `PeriodLockModel`)

```python
class FiscalYearModel(Base):
    __tablename__ = "fiscal_years"
    id: Mapped[uuid] = mapped_column(primary_key=True)
    company_id: Mapped[uuid] = mapped_column(ForeignKey("companies.id"), index=True)
    year_code: Mapped[str] = mapped_column(String(20))
    period_type: Mapped[str] = mapped_column(String(20))
    start_date: Mapped[date]
    end_date: Mapped[date]
    is_first_period: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    opening_balance_posted: Mapped[bool] = mapped_column(default=False)
    closed_at: Mapped[datetime | None]
    closed_by: Mapped[uuid | None]
    __table_args__ = (UniqueConstraint("company_id", "year_code"),)

class AccountingPeriodModel(Base):
    __tablename__ = "accounting_periods"
    id: Mapped[uuid] = mapped_column(primary_key=True)
    fiscal_year_id: Mapped[uuid] = mapped_column(ForeignKey("fiscal_years.id"), index=True)
    period_number: Mapped[int]
    label: Mapped[str]
    start_date: Mapped[date]
    end_date: Mapped[date]
    status: Mapped[str] = mapped_column(default="OPEN")
    locked_by: Mapped[uuid | None]
    locked_at: Mapped[datetime | None]
    lock_reason: Mapped[str | None]
    __table_args__ = (
        UniqueConstraint("fiscal_year_id", "period_number"),
        CheckConstraint("end_date >= start_date", name="ck_period_span"),
    )

class PeriodLockEventModel(Base):
    __tablename__ = "period_lock_events"
    id: Mapped[uuid] = mapped_column(primary_key=True)
    period_id: Mapped[uuid] = mapped_column(ForeignKey("accounting_periods.id"), index=True)
    action: Mapped[str]          # CLOSE | REOPEN | YEAR_END
    requested_by: Mapped[uuid]
    approved_by: Mapped[uuid]
    requested_at: Mapped[datetime]
    approved_at: Mapped[datetime]
    reason: Mapped[str]
    prev_checksum: Mapped[str]
    checksum: Mapped[str]        # SHA-256 of prev + row (audit parity)
```

Drop/replace the old `period_locks` table via migration (`flask db migrate`).

### 5.2 Repository adapter
- New file `src/bricks/fiscal_year_period/storage.py` with `SQLAlchemyFiscalYearRepository`
  + `SQLAlchemyPeriodLockRepository`.
- `is_locked`: single overlap query against `accounting_periods`
  (`status != 'OPEN'`), same shape as `currency_repo.period_is_locked()`.

### 5.3 Migration
- New migration: create `fiscal_years`, `accounting_periods`,
  `period_lock_events`; migrate legacy `period_locks` rows (map to
  `accounting_periods.status`); seed default fiscal year per existing company
  (CALENDAR 2026) + 12 periods; data-fix any `FISCAL_15` config → require
  admin confirmation.

## 6. REST API (`src/bricks/fiscal_year_period/web_adapter.py`)

Register in `app.py`; `@login_required + current_user.role` on all; AUDITOR read-only.
Copy test-engine hook pattern from `currencies_bp.py` (init_test_engine /
`_req_session` / teardown session restore).

| Method | Path | Permission | Body/Query | Returns |
|---|---|---|---|---|
| GET | `/api/fiscal-years` | any auth | `?company_id=` | list |
| POST | `/api/fiscal-years` | fiscal_year.configure | period_type, start_date | 201 |
| GET | `/api/fiscal-years/<id>` | any auth | — | detail + periods |
| GET | `/api/fiscal-years/<id>/periods` | any auth | — | period list |
| POST | `/api/periods/<id>/close` | period.close.request | reason | 202 (approval flow) |
| POST | `/api/periods/<id>/reopen` | period.reopen | reason (required) | 200 |
| POST | `/api/periods/<id>/lock-events` | period.close.approve | approval_ref | 200 |
| POST | `/api/fiscal-years/<id>/close` | year_end.run | — | 200 + opening balances |
| POST | `/api/fiscal-years/change` | fiscal_year.configure | new_period_type | 200 + transition report |
| GET | `/api/fiscal-years/<id>/history` | any auth | — | lock events |
| GET | `/api/periods/locked?date=&company_id=` | any auth | — | lock status (for UI banner) |

Error contract: `{"error": "<code>", "message": "...", "period_id": ...}`;
`409` for lock conflicts, `422` for legal-shape violations, `403` SOD/RBAC.

## 6. Serializers (`src/presentation/serializers/fiscal_year.py`)
- `fiscal_year_to_dict`, `period_to_dict`, `lock_event_to_dict` — snake_case
  JSON, `date` as ISO-8601, Decimal untouched.

## 7. Concurrency & integrity
- Lock + validate inside one DB transaction; `SELECT ... FOR UPDATE` on the
  period row before status flip; unique constraints as backstop (R-04/NFR-2).
- `is_locked` hot path: 60s in-memory cache per (company, date), invalidated on
  lock events.

## 8. Migration of existing System Settings routes
- `system_settings_bp.py` `/api/invoices/<id>/approve` + `/threshold-info`
  unaffected. `lock_period`/`unlock_period` delegates to the new
  `PeriodLockService` (keeps old routes working) — do NOT remove until
  fiscal-year API is live.

## 9. Test plan (summary; see templates/test-plan-fiscal-year.md)
- Unit: period math (quarter alignment, ≤15-month first, <90-day merge,
  leap years), state machine, SOD, exceptions. ≥ 30 cases.
- Integration: repo adapters (SQLite), API routes incl. RBAC, lock enforcement
  on Voucher/Invoice/Revaluation via real service calls.
- No UI/E2E for pure logic (TESTING_STRATEGY mục 6.4).
