# Specs — Tax Engine Config / Tax Rates Module

| | |
|---|---|
| Version | 0.2 |
| Date | 2026-09-03 |
| Status | ✅ DONE — P0+P1 shipped, 951 tests, gate green |

## 1. Architecture placement

Lego Brick Architecture (see `AGENTS.md`):

```
src/bricks/system_settings/          ← 🧱 Tax Engine lives here (not separate tax_engine brick)
  contract.py                ← TaxRate port, SystemSettingsRepositoryPort, ALLOWED_VAT_FRACTIONS
  domain.py                  ← TaxRate {0,5,8,10,-1}, CompanyConfig, EInvoiceSeries, CONFIG_FLAGS
  rate_windows.py            ← TaxRateWindow, SEED_TAX_RATE_WINDOWS, VAT_REDUCTION_END, is_8pct_eligible, make_rate_gate
  services.py                ← SystemSettingsService, TaxRateCatalogService, VatDeclarationService (+ carry + GDT XML)
  storage.py                 ← SystemSettingsModel, TaxRateWindowModel, VatCarryModel, PeriodLockModel
  web_adapter.py             ← Flask blueprint `/api/v1/system-settings/*` + `/reports/vat-declaration` + `/tax-rate-windows`
src/bricks/invoice/          ← gates: FY period → COA → catalog → rate window + 8% category (all lines)
src/bricks/purchases/        ← gates: FY → COA → duplicate → totals + rate window + 8% category + submit_proof
src/bricks/voucher/ledger/   ← FY+COA gates, LedgerSourcePort for declaration
```

**Brick boundaries:**
- `domain.py` pure Python; no Flask/SQLAlchemy/flask_login
- `contract.py` primitives only `str/int/Decimal/UUID/dict`
- `storage.py` only file with SQLAlchemy; `services.py` via port; `web_adapter.py` only Flask

## 2. Domain model

### 2.1 TaxRate

```python
class TaxRate(Enum):
    VAT_0 = 0
    VAT_5 = 5
    VAT_8 = 8  # temporary 01/07/2025→31/12/2026 per NQ204/ND174
    VAT_10 = 10
    NOT_TAXED = -1  # Điều 5 exempt, item-level only

    def to_fraction(self) -> Decimal:
        return Decimal(0) if self is NOT_TAXED else Decimal(self.value)/Decimal(100)
```

Rules: `VAT_8` prints "8%" on invoice, deducts at reduced figure; after 31/12/2026 gate rejects → revert to 10%.

### 2.2 CompanyConfig

```python
@dataclass
class CompanyConfig:
    vat_rates: frozenset[int] = {0,5,10}  # LAW-type immutable
    vat_settlement_cycle: str = "monthly"|"quarterly"  # CONFIG-type, enforce in VatDeclarationService
    # + fiscal_year_start_month/day, decimal_places, default_currency, cost_center_required
```

### 2.3 TaxRateWindow + 8% gate

```python
@dataclass(frozen=True)
class TaxRateWindow:
    rate_pct: int; fraction: str; valid_from: date|None; valid_to: date|None; decree_ref: str
    def covers(self, on: date) -> bool: ...

VAT_REDUCTION_END = date(2026,12,31)
EXCLUDED_FROM_8PCT = frozenset({"telecom","finance",...,"mining","sst"})
def is_8pct_eligible(category: str|None) -> bool: ...
def _frac(pct:int) -> str: return str(TaxRate(pct).to_fraction())
SEED_TAX_RATE_WINDOWS = (TaxRateWindow(0,_frac(0),...), TaxRateWindow(8,_frac(8),2025-07-01,VAT_REDUCTION_END,...))
def make_rate_gate(windows): return gate(fraction,on_date) raises ValueError with decree citation
```

## 3. Service layer

### 3.1 SystemSettingsService

`validate_vat_rate(rate)` — rejects ∉ {0,5,8,10}; `add_e_invoice_series` max15 SOD actor≠approver; `update_config_flag` with `CONFIG_FLAGS` allowlist + optimistic `config_version`.

### 3.2 VatDeclarationService

```python
class VatDeclarationService:
    def __init__(self, *, output_source, input_source, carry_repo=None, config_repo=None): ...
    def _compute(company_id,year,month|quarter) -> dict: # pure calc
    def declare(...) -> dict: # _compute + save_carry + cycle enforce
    def export_gdt_xml(...) -> str: # _compute + saxutils.escape → 01/GTGT XML
```

- Monthly `month` XOR quarterly `quarter`; `InvalidPeriodError` otherwise
- `config_repo.get_config().vat_settlement_cycle` enforces monthly≠quarter cross →422
- `carry_repo.get_previous_carry` adds `prev_carry` to `in_ded`; `save_carry` persists `carry_forward = max(0,in_ded-out_vat)`
- `export_gdt_xml` uses `_compute` (no double persist), `saxutils.escape` safe

### 3.3 PurchaseService proof

`submit_proof(iid,actor,reason)` — only `PENDING_PROOF` → `payment_proof=True`, `CASH→BANK` flip if needed, checksum `PROOF`, audit append `reason [was:cash]` + `after_value`.

## 4. Data model (actual)

```sql
system_settings (id, company_id, vat_rates JSON, e_invoice_series JSON, config_version, updated_by/at, fiscal_year_start_month/day, vat_settlement_cycle, decimal_places, default_currency, cost_center_required, legal_reviewed_at/by)
tax_rate_windows (id, rate_pct, fraction, valid_from, valid_to, decree_ref)
vat_carry_forwards (id, company_id, year, month, quarter, carry_amount Numeric(18,2), UNIQUE company_id+year+month+quarter)
period_locks (id, company_id, fiscal_year, accounting_period, lock_type, locked_at/by, notes)
```

Alembic `9c1a2b3d4e5f_add_vat_carry_forwards.py` `upgrade head` creates `vat_carry_forwards`.

## 5. API endpoints

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/v1/system-settings/tax-rates` | any auth | list TaxRate enum {0,5,8,10,-1} + fractions |
| GET/POST | `/api/v1/tax-rate-windows[?on=YYYY-MM-DD]` | GET any, POST ADMIN | list windows, add window SOD |
| GET | `/api/v1/system-settings/config/{cid}` | any auth | get CompanyConfig |
| PATCH | `/api/v1/system-settings/config/{cid}` | ADMIN,CHIEF | update CONFIG flag with version |
| POST | `/api/v1/system-settings/e-invoice-series` | ADMIN,CHIEF SOD | add series max15 |
| POST | `/api/v1/invoices` | ACCOUNTANT+ | create invoice — gates FY→COA→catalog→window→8% category (all lines) |
| POST | `/api/v1/purchase-invoices` | ACCOUNTANT+ | create purchase — same gates + duplicate guard |
| POST | `/api/v1/purchase-invoices/<iid>/proof` | ACCOUNTANT+ | submit proof PENDING→DEDUCTIBLE |
| GET/POST | `/api/v1/reports/vat-declaration?company_id&year&month|quarter[&format=gdt_xml]` | any auth | 01/GTGT JSON or GDT XML, cycle enforce, carry persist |

All `@login_required + role`, AUDITOR 403 on writes, actor UUID required.

## 6. Invoice VAT calculation

`Invoice.vat_amount = (subtotal * vat_rate).quantize(Decimal(1))` VND; `grand_total = subtotal+vat_amount`.

## 7. Non-functional

- Decimal tol 0.01, UTC timestamps, Asia/Ho_Chi_Minh business date
- `vat_carry_forwards` persists per period; `export_gdt_xml` pure, no double persist via `_compute`
- 951 tests, `ruff+black+mypy strict+pytest` green on 3.11+3.12

## 8. Version history

| Ver | Date | Change |
|---|---|---|
| 0.1 | 2026-08-19 | Initial draft; tax_engine NEW brick proposal, repo MISSING |
| 0.2 | 2026-09-03 | DONE: moved to system_settings brick, added VAT_8 windows+gate, VatCarryModel, cycle enforce, GDT XML, proof workflow, 951 tests, law re-checked 137 sources |
