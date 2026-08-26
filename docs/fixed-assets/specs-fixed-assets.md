# Specs — Fixed Assets Module (Tài sản cố định)

_Version 1.0.0 · 2026-08-25 · Legal base: TT99/2025 Phụ lục 2 (TSCĐ accounts), TT45/2013 (sửa TT147/2016) depreciation framework, Luật Kế toán 2015 Art. 11_
_Brick: `src/bricks/fixed_assets/`_

---

## 1. Brick layout

```
src/bricks/fixed_assets/
├── contract.py      # FixedAssetRepositoryPort, DepreciationRunRepositoryPort
├── domain.py        # FixedAsset, DepreciationMethod, FAStatus, FixedAssetDepreciation
├── services.py      # FixedAssetService
├── storage.py       # fixed_assets + depreciation_runs tables
└── web_adapter.py   # fixed_assets_bp
```

---

## 2. Data model — `fixed_assets`

| Field | Type | Rules |
|---|---|---|
| id | UUID PK | |
| company_id | UUID INDEX | tenant isolation |
| asset_code | VARCHAR(30) UNIQUE(company_id) | auto-generated `TSCĐ/{seq:04d}` |
| name | VARCHAR(200) NOT NULL | |
| category | ENUM(huu_hinh/tai_chinh/vu_hinh) | maps to TK 211/212/213 |
| original_cost | NUMERIC(18,2) >0 | nguyên giá |
| acquisition_date | DATE | trích khấu hao từ ngày này |
| useful_life_months | INT ≥1 | thời gian khấu hao (tháng) |
| depreciation_method | ENUM(STRAIGHT_LINE) | v1: straight-line only |
| depreciation_account | VARCHAR(10) | TK chi phí (627/641/642) per TT99 allocation |
| is_active | BOOL default TRUE | soft-deactivate only (R-6 retention) |
| accumulated_depreciation | NUMERIC(18,2) default 0 | giá trị hao mòn lũy kế — updated by monthly run |
| checksum | CHAR(64) | SHA-256 chain |

**Unique:** `(company_id, asset_code)` · `(company_id, asset_code)` on asset_code

## 3. Domain entities

### 3.1 FixedAsset

```python
class DepreciationMethod(Enum):
    STRAIGHT_LINE = "STRAIGHT_LINE"

class FAStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"     # ngừng sử dụng ≤9 months
    CLOSED = "closed"           # đã thanh lý/nhượng bán

@dataclass
class FixedAsset:
    company_id: UUID
    asset_code: str
    name: str
    category: str               # huu_hinh / tai_chinh / vu_hinh
    original_cost: Decimal
    acquisition_date: date
    useful_life_months: int     # >= 1
    depreciation_method: str    # STRAIGHT_LINE v1
    depreciation_account: str   # e.g. "6421"
    is_active: bool = True
    accumulated_depreciation: Decimal = field(default_factory=lambda: Decimal(0))
    id: UUID = field(default_factory=uuid4)
    status: str = "active"
    checksum: str = ""

    @property
    def monthly_depreciation(self) -> Decimal:
        """Straight-line: NG / useful_life_months."""
        return (self.original_cost / self.useful_life_months).quantize(Decimal("1"))

    @property
    def remaining_months(self) -> int:
        if self.monthly_depreciation <= 0:
            return 0
        return max(0, int(self.original_cost / self.monthly_depreciation)
                   - int(self.accumulated_depreciation / self.monthly_depreciation))

    @property
    def book_value(self) -> Decimal:
        return self.original_cost - self.accumulated_depreciation

    def apply_monthly_depreciation(self, amount: Decimal) -> None:
        self.accumulated_depreciation += amount

    def compute_checksum(self, prev: str, actor: UUID, action: str, reason: str) -> str:
        payload = f"{prev}{self.id}{actor}{self.status}{action}{reason}"
        return hashlib.sha256(payload.encode()).hexdigest()
```

### 3.2 Validation rules

| Rule | Enforced at |
|---|---|
| R-FA1: original_cost > 0 | Entity __post_init__ |
| R-FA2: useful_life_months ≥ 1 | Entity __post_init__ |
| R-FA3: unique (company, asset_code) | Service → repo.exists_duplicate() |
| R-FA4: depreciation only when status=ACTIVE and accumulated < cost | Service.compute_depreciation |
| R-FA5: monthly amount capped at remaining (NG − accumulated) | Service.compute_depreciation |
| R-FA6: soft-close only; CLOSED blocks depreciation | Service.close_asset |
| R-FA7: every mutation stamps SHA-256 checksum chain | _stamp pattern |

## 4. Contract — `FixedAssetRepositoryPort`

```python
create(asset) -> asset
get_by_id(id) -> asset | None
get_by_company(cid) -> list[asset]
update(asset) -> asset
exists_duplicate(cid, code) -> bool
find_active_with_remaining(cid) -> list[asset]  # for monthly run
```

## 5. Services — `FixedAssetService` + `DepreciationService`

### FixedAssetService

| Method | Roles | Description |
|---|---|---|
| create_asset(...) | WRITE_ROLES | R-FA1..R-FA3 gates; genesis checksum |
| get_asset(id) | READ_ROLES | |
| list_by_company(cid, status?) | READ_ROLES | |
| deactivate(id, actor, reason) | CHIEF+ | soft-close; blocks future depreciation |
| validate_before_entry(cid, id) | — | status must be ACTIVE |

### DepreciationService (monthly batch)

| Method | Description |
|--------|-------------|
| compute_and_post(cid, year, month, actor, reason) | For each ACTIVE asset with remaining depreciation: compute straight-line amount (capped at remaining); create voucher via injected voucher_svc; update accumulated_depreciation |

**Journal generated:** `Dr {depreciation_account} / Cr 214` per asset or grouped.

**Guards:** period open via FY gate; COA posting gate for expense account.

## 6. API endpoints (`fixed_assets_bp`)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/api/v1/fixed-assets?company_id&status` | READ_ROLES | List FA |
| GET | `/api/v1/fixed-assets/<id>` | READ_ROLES | Detail incl. computed fields |
| POST | `/api/v1/fixed-assets` | WRITE_ROLES | Create new asset |
| POST | `/api/v1/depreciation-runs/compute` | WRITE_ROLES | Monthly batch compute+post |
| GET | `/api/v1/fixed-assets/<id>/depreciation-schedule` | READ_ROLES | Full schedule table |

Error codes: `EX-FA01 MISSING_ACTOR(400)` · `FA02 DUPLICATE_ASSET_CODE(409)` · `FA03 PERIOD_CLOSED(409)` · `FA04 INVALID_ACCOUNT(422)` · `FA05 ASSET_CLOSED(409)` · `FA06 NO_REMAINING_DEPRECIATION(409)` · `AUDITOR_READ_ONLY(403)`

## 7. Out of scope v1

Declining balance method · production output method · useful-life change workflow · transfer between departments · revaluation · physical count · XML import from TCT portal.
