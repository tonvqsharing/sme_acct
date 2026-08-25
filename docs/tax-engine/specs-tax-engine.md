# Specs — Tax Engine Config / Tax Rates Module

| | |
|---|---|
| Version | 0.1 |
| Date | 2026-08-19 |
| Status | DRAFT — awaiting implementation + repository adapter |

## 1. Architecture placement

Follows existing Lego Brick Architecture (see AGENTS.md, system-settings module pattern):

```
src/bricks/
  tax_engine/                  ← 🧱 NEW brick
    contract.py                ← 🔌 Public interface (TaxRate, VATMethod, FlagType, etc.)
    domain.py                  ← 🎯 TaxRate enum, VATMethod, FlagType, FlagScope, FlagCategory (pure Python)
    services.py                ← ⚙️ SystemSettingsService with VAT validation, e-invoice series, config updates
    storage.py                 ← 💾 SQLAlchemy models + repository adapters
    web_adapter.py             ← 🌐 Flask blueprint + REST endpoints
```

**Brick boundaries:**
- `domain.py` — pure Python; NO Flask, NO SQLAlchemy, NO flask_login imports
- `contract.py` — public interface; accepts/returns only `str`, `int`, `float`, `dict`, `Decimal`, `UUID`
- `storage.py` — SQLAlchemy models + repo adapters (the ONLY file with SQLAlchemy imports)
- `services.py` — orchestration with injected port; no Flask/SQLAlchemy imports
- `web_adapter.py` — Flask blueprint; `@login_required` + `current_user.role` checks (no Casbin)
      models.py        # SystemSettingsModel, CompanyConfigModel + vat_rates column
    repositories/
      system_settings_repo.py  # SQLAlchemySystemSettingsRepository (MISSING — causes 500)
  presentation/
    api/
      system_settings_bp.py   # REST endpoints — BROKEN: 500 due to missing repo
    serializers/
      tax_serializer.py
```

## 2. Domain model

### 2.1 TaxRate (entity)

```python
class TaxRate(Enum):
    """Thuế suất theo quy định Việt Nam."""
    VAT_0 = 0
    VAT_5 = 5
    VAT_10 = 10
    NOT_TAXED = -1
```

Rules:
- `VAT_0` = 0% — xuất khẩu, dịch vụ quốc tế, không chịu thuế GTGT.
- `VAT_5` = 5% — hàng hóa và dịch vụ bắt buộc (nước dùng: nước sạch, thuốc y học, sách giáo khoa, phân bón, pesticide).
- `VAT_10` = 10% — chuẩn mực — hàng hóa và dịch vụ thường (dịch vụ thương mại, bất động sản, nội địa vận chuyển, v.v.).
- `NOT_TAXED` = -1 — miễn thuế GTGT (các mặt hàng không chịu thuế theo Điều 5 Luật GTGT).

Constraints:
- Code matches enum values {0, 5, 10, -1}.
- Domain layer: no sqlalchemy/Flask imports (lint-enforced, per AGENTS.md).

### 2.2 CompanyConfig — vat_rates

```python
@dataclass
class CompanyConfig:
    vat_rates: frozenset[int] = frozenset({0, 5, 10})  # LAW-type, immutable without migration
    # ... other fields
```

Rules:
- `vat_rates` is a **LAW-type flag** — immutable without migration (FlagLockedError).
- Default `{0, 5, 10}` per Vietnamese VAT Law effective 01/07/2025.
- Change requires migration patch + documented reason + 2nd approval (CHIEF_ACCOUNTANT).
- Validation: `validate_vat_rate(rate)` → raises `InvalidRegimeError` if rate ∉ {0, 5, 10}.

## 3. Service layer

### 3.1 SystemSettingsService — VAT-related methods

```python
def validate_vat_rate(self, rate: int) -> None:
    """Validate VAT rate is in the allowed set."""
    if rate not in {0, 5, 10}:
        raise InvalidRegimeError(
            f"Thuế GTGT {rate} không hợp lệ. Các mức được phép: {{0, 5, 10}}"
        )

def add_e_invoice_series(
    self,
    company_id: UUID,
    actor: UUID,
    prefix: str,
    ca_signer: str | None,
) -> EInvoiceSeries:
    """Add a new e-invoice series.

    Max 15 active series per company.
    Requires CA signer information.
    CONFIG-type flag; 2nd approval pattern (ADMIN → CHIEF_ACCOUNTANT).
    """
    config = self._settings_repo.get_config(company_id)
    current_series = len(config.e_invoice_series)
    if current_series >= 15:
        raise SystemSettingsError(
            "Đã đạt giới hạn 15 series số hóa đơn điện tử.active"
        )
    new_series = EInvoiceSeries(
        prefix=prefix,
        next_sequence=1,
        active=True,
        ca_signer=ca_signer,
    )
    config.e_invoice_series = frozenset(
        list(config.e_invoice_series) + [new_series]
    )
    config.updated_by = actor
    config.config_version += 1
    updated = self._settings_repo.update_config(config)
    return new_series
```

### 3.2 Invoice VAT calculation (domain entity, no service needed)

```python
class InvoiceItem:
    def __init__(self, ..., vat_rate: TaxRate = TaxRate.VAT_10, ...):
        self.vat_rate = vat_rate
        line_total = self.quantity * self.unit_price - self.discount
        self.vat_amount = round(line_total * self.vat_rate.value / 100, 2)
        self.total_amount = round(line_total + self.vat_amount, 2)
```

## 4. Data model (SQLAlchemy) — proposed

```python
class SystemSettingsModel(Base):
    __tablename__ = "system_settings"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    vat_rates: Mapped[frozenset[int]] = mapped_column(FrozenJSON, nullable=False, default=frozenset({0, 5, 10}))
    e_invoice_series: Mapped[frozenset[EInvoiceSeries]] = mapped_column(FrozenJSON, nullable=True, default=frozenset())
    config_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    # ... other LAW/CONFIG-type flags

class EInvoiceSeriesModel(Base):
    __tablename__ = "e_invoice_series"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    next_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ca_signer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
```

## 5. API endpoints (draft)

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | /api/v1/system_settings/config | ADMIN, CHIEF_ACCOUNTANT, AUDITOR | list config (first company as example) |
| GET | /api/v1/system_settings/config/{company_id} | all above | get config by company ID |
| PATCH | /api/v1/system_settings/config/{company_id} | ADMIN, CHIEF_ACCOUNTANT | update config (LAW-type immutable without migration) |
| POST | /api/v1/system_settings/e-invoice-series | ADMIN, CHIEF_ACCOUNTANT | add e-invoice series (2nd approval) |
| GET | /api/v1/system_settings/tax-rates | all above | list TaxRate enum values {0, 5, 10, -1} |

All routes decorated `@login_required + current_user.role`; AUDITOR read-only backend-enforced; actor UUID required
for all mutations.

## 6. CSV / import format (for e-invoice series or config changes, if needed)

Not primary; manual API entry preferred. If CSV import needed later, pattern follows
`exchange_rate_service.py.import_csv()`: atomic all-or-nothing, per-row validation,
error report `{row: n, error: msg}`.

## 7. Non-functional

- Decimal rounding tol: implied 0.01 (VAT amount in VND).
- Rate history append-only: new row supersedes old; no in-place edit → audit-friendly.
- All mutations in single DB transaction; rollback on any failure.
- No SQLAlchemy/Flask imports in domain entities (lint-enforced).
- Timezone: all timestamps UTC; business date Asia/Ho_Chi_Minh.

## 8. Version history

| Ver | Date | Change |
|---|---|---|
| 0.1 | 2026-08-19 | Initial spec draft; module broken (missing repo); domain OK |
---

## Addendum 2026-08 — Reduced 8% VAT rate (TEMPORARY)

**Source:** gdt.gov.vn (Bộ Tài chính reform page) · thuvienphapluat.vn · verified 2026-08-24.

- **NQ 204/2025/QH15** + **NĐ 174/2025/NĐ-CP**: reduce 10% → **8%** for deduction-method businesses, **eff 01/07/2025 → 31/12/2026**. Invoice prints "8%"; input-VAT deducts at the reduced figure.
- **Exclusions while active:** viễn thông; tài chính/ngân hàng/chứng khoán/bảo hiểm; kinh doanh BĐS; kim loại & sản phẩm kim loại đúc sẵn; khai khoáng (trừ than); hàng hóa/dịch vụ chịu TTĐB (**trừ xăng — xăng được giảm**).
- After 31/12/2026 rates revert to Luật GTGT 2024 — enum must be revisited.

**Implementation delta:** `TaxRate.VAT_8 = 8` added; `LAWFUL_RATES = {0,5,8,10}` for `validate_vat_rate`; `CompanyConfig.vat_rates` default remains `{0,5,10}` per base law — configure 8 explicitly when trading reduced goods.
