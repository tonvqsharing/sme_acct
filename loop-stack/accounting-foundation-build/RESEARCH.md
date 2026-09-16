# Research Log

## Context & Prior Work

### Codebase Structure
```
SmeAccounting.sln (net10.0, C# 13, TreatWarningsAsErrors=true)
├── src/
│   ├── SmeAccounting.Domain/          (zero NuGet refs — pure domain)
│   ├── SmeAccounting.Application/     (MediatR 14.2, FluentValidation 12.1)
│   ├── SmeAccounting.Infrastructure/  (EF Core 10.0.4, Npgsql 10.0.3, PostgreSQL)
│   └── SmeAccounting.Api/             (ASP.NET MVC, Swagger)
└── tests/
    └── SmeAccounting.ArchitectureTests/  (xUnit, NetArchTest.Rules 1.3.2)
```

### Architecture Enforcement
- 22 NetArchTest tests verify Clean Architecture constraints
- Dependency direction: Api→Application→Domain←Infrastructure
- Domain must have zero NuGet package references
- Controllers must not reference Domain.Entities or Domain.Ports
- Application handlers must not reference Infrastructure

### Database
- PostgreSQL 16.14 on Windows host (172.21.208.1)
- Snake-case table/column naming (EFCore.NamingConventions)
- xmin concurrency tokens on all entities
- Connection: `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`
- 2 migrations: InitialCreate + FixAccountNameColumn

### Domain Layer

#### Entities (7 + BaseEntity)
| Entity | Fields | Methods | Notes |
|--------|--------|---------|-------|
| BaseEntity | Id (long), DomainEvents | AddDomainEvent, RemoveDomainEvent, ClearDomainEvents | Abstract base |
| Account | Code (AccountCode VO), Name, Level, ParentId, AccountType, IsActive, AccountGroupId, Children | Deprecate(), AddChild() | Self-referencing tree. Soft-delete only |
| AccountGroup | Code, Name, AccountType | — | Grouping for COA categories |
| FiscalYear | Year, Status (FiscalYearStatus), Periods | AddPeriod(month) | Has collection of FiscalPeriod |
| FiscalPeriod | YearId, Month, Status (PeriodStatus), OpenedAt, ClosedAt | Open(), Close() | Close raises PeriodClosed event |
| JournalEntry | EntryNumber, Date, PeriodId, Description, SourceType, SourceId, PostedBy, PostedAt, IsPosted, Lines | SetSource(), AddLine(), Post(), ValidateBalance() | Post validates balance then raises JournalEntryPosted |
| JournalEntryLine | EntryId, AccountId, Debit (Money), Credit (Money), Description | — | Owned Money value objects |
| PostingReference | JournalEntryId, SourceType, SourceId | — | Links journal entries to source documents |

#### Value Objects (6)
| VO | Type | Notes |
|----|------|-------|
| Money | record | decimal Amount + string Currency. Has +,- operators with currency-mismatch guards. Zero defaults to VND |
| AccountCode | record | String wrapper. Validates: non-empty, numeric, >= 4 digits |
| Currency | record | Code, Name, IsDefault — simple DTO-style VO |
| AccountType | enum | Asset, Liability, Equity, Revenue, Expense |
| PeriodStatus | enum | Open, Closing, Closed |
| FiscalYearStatus | enum | Open, Closed |

#### Domain Events (4)
| Event | Fields |
|-------|--------|
| DomainEvent (base) | OccurredOn (DateTimeOffset), EventId (Guid) |
| AccountCreated | AccountId (long) |
| AccountDeprecated | AccountId (long) |
| JournalEntryPosted | EntryId (long) |
| PeriodClosed | PeriodId (long) |

#### Domain Exceptions (4)
| Exception | Inherits | Message |
|-----------|----------|---------|
| DomainException | Exception | Base — takes message |
| AccountNotLeafException | DomainException | "Account {id} has child accounts and cannot accept postings." |
| InvalidPostingRuleException | DomainException | Takes message (used for balance validation) |
| PeriodClosedException | DomainException | "Period {id} is closed and cannot accept new postings." |

#### Port Interfaces (7)
| Port | Methods | Notes |
|------|---------|-------|
| IAccountRepository | GetByIdAsync, GetAllAsync, AddAsync, UpdateAsync | CRUD for Account |
| IJournalEntryRepository | GetByIdAsync, GetAllAsync, AddAsync | CRUD for JournalEntry |
| IUnitOfWork | SaveChangesAsync(ct) | Transaction boundary |
| IForeignExchangeRateProvider | ConvertAsync(amount, targetCurrency, date) → Money | FX conversion port |
| IAuditLogger | LogAsync(action, entity, entityId, details) | Audit trail |
| IPostingService | PostAsync(JournalEntry) | Posting orchestration |
| IClock | Now (DateTimeOffset) | Testable time |

### Infrastructure Layer
- **DbContext**: SmeAccountingDbContext (7 DbSets, implements IUnitOfWork, publishes domain events on SaveChanges — stub)
- **Configurations**: All 7 entities have IEntityTypeConfiguration with snake-case, xmin row version, owned Money types
- **Repositories**: EfAccountRepository (includes Children), EfJournalEntryRepository (includes Lines)
- **Adapters**: BankExchangeRateProvider (mock rates), DigitalSignatureAdapter (NOT_IMPLEMENTED), EInvoiceProviderAdapter (NOT_IMPLEMENTED)
- **Services**: AuditLogger (Console.WriteLine stub), SystemClock
- **DI**: AddInfrastructure extension — registers DbContext, repositories, clock, audit, FX provider

### Application Layer
- **CQRS Commands**: CreateAccount, DeprecateAccount, CreateJournalEntry, PostJournalEntry, CloseFiscalPeriod, OpenFiscalPeriod
- **CQRS Queries**: GetAccount, GetAccountsByGroup, GetBalanceSheet, GetIncomeStatement, GetFiscalPeriods, GetJournalEntry
- **DTOs**: AccountDto, BalanceSheetDto, IncomeStatementDto, MoneyDto, FiscalPeriodDto, FiscalYearDto, JournalEntryDto, JournalEntryLineDto, AccountGroupTotal
- **Validators**: CreateAccountCommand, CreateJournalEntryCommand, PostJournalEntryCommand (FluentValidation)
- **Services**: IAccountingReportService port (no implementation yet)
- **DI**: AddApplication extension — MediatR assembly scan + ValidationBehavior pipeline

### Api Layer (MVC)
- **Controllers**: ChartOfAccounts, JournalEntry, FiscalPeriod, Reporting, Settings, Home
- **ViewModels**: ChartOfAccountsViewModel, CreateAccountViewModel, FiscalPeriodViewModel, JournalEntryViewModel, CreateJournalEntryViewModel
- **Pattern**: Thin controllers — MediatR dispatch only, catch ValidationException for ModelState
- **Swagger**: Swashbuckle 10.2.3, dev mode only

### Tests (Architecture Only — 22 tests)
- DomainPurityTests: No NuGet refs, no forbidden packages, no EF Core dependency
- LayerCouplingTests: Controllers→Entities/Ports forbidden, Handlers→Infrastructure forbidden, Infrastructure→Api forbidden
- DependencyRulesTests: Domain→Application/Infrastructure/Api forbidden, Application→Infrastructure/Api forbidden, Controllers→Infrastructure forbidden
- NamingConventionsTests: Entities in Entities ns, Repository interfaces start with I, Commands end with Command, Queries end with Query, DTOs end withDto, Controllers end with Controller
- PostingRuleIsolationTests: IPostingService in Domain assembly, balance rule enforceable in domain

### Existing Entities vs Accounting Foundation Goal

| Target Entity | Exists? | Details |
|---------------|---------|---------|
| **Company** | **NO** | Not implemented anywhere |
| **FiscalYear** | **YES** | Domain entity with Year, Status, Periods collection |
| **FiscalPeriod** | **YES** | Domain entity with YearId, Month, Status, Open/Close |
| **Currency** | **PARTIAL** | Exists as Value Object only (record with Code, Name, IsDefault). NOT an entity with its own table |
| **ExchangeRate** | **NO** | Only IForeignExchangeRateProvider port exists (mock BankExchangeRateProvider). No ExchangeRate entity/table |
| **Account (COA)** | **YES** | Full entity with tree structure, AccountCode VO, AccountType, AccountGroup FK |
| **Department** | **NO** | Not implemented |
| **CostCenter** | **NO** | Not implemented |
| **Project** | **NO** | Not implemented |

### What Needs to Be Built for Accounting Foundation

**Domain Layer:**
- Company entity (single-company per AGENTS.md constraint, but still needed as entity)
- ExchangeRate entity (date-based rates, currency pairs)
- Promote Currency from VO to entity (or create CurrencyConfiguration for table)
- Department entity (accounting dimension)
- CostCenter entity (accounting dimension)
- Project entity (accounting dimension)
- New port interfaces: ICompanyRepository, IExchangeRateRepository, IDepartmentRepository, ICostCenterRepository, IProjectRepository
- Domain events: CompanyCreated, ExchangeRateRecorded, etc.
- New domain exceptions as needed

**Infrastructure Layer:**
- EF Core configurations for all new entities
- Repository implementations for new ports
- Add DbSets to SmeAccountingDbContext
- EF Core migrations for new tables

**Application Layer:**
- Commands/Queries for Company CRUD
- Commands/Queries for ExchangeRate management
- Commands/Queries for Department/CostCenter/Project CRUD
- DTOs for all new entities
- Validators for new commands

**Api Layer:**
- Controllers for Company, ExchangeRate, Department, CostCenter, Project
- ViewModels for new views

**Tests:**
- Architecture tests may need updating if new patterns emerge
- Unit tests for domain logic
- Integration tests for new repositories

### Key Constraints
- Single company (no multi-tenancy)
- VAS/Circular 99 compliance
- All domain events must use `long` IDs (consistent with BaseEntity.Id)
- Money arithmetic needs currency-mismatch guards
- Private parameterless constructors on all entities (EF Core)
- Snake-case PostgreSQL naming
- xmin concurrency tokens
- Domain has zero NuGet dependencies

## External Knowledge & Resources

### Circular 99/2025/TT-BTC — The Current Authoritative Source

| Attribute | Value |
|-----------|-------|
| **Official name** | Thông tư số 99/2025/TT-BTC hướng dẫn Chế độ kế toán doanh nghiệp |
| **Issuing body** | Bộ Tài chính (Ministry of Finance) |
| **Issued** | 27 October 2025 |
| **Effective** | 1 January 2026 |
| **Applies to** | Fiscal years beginning on or after 1 January 2026 |
| **Signer** | Nguyễn Đức Tâm (Minister of Finance) |
| **Replaces** | Circular 200/2014/TT-BTC, Circular 75/2015/TT-BTC, Circular 53/2016/TT-BTC, Circular 195/2012/TT-BTC |
| **Published on** | congbao.chinhphu.vn (Government Gazette) |

**Status: Circular 99/2025/TT-BTC IS the current authoritative source for enterprise accounting in Vietnam.** No newer circular has superseded it as of September 2026. The only newer related circular is **Circular 118/2026/TT-BTC** (effective 1 Jan 2027), which governs optional IFRS application for International Financial Center entities — it does NOT replace Circular 99 but operates alongside it.

**Official sources:**
- Government Gazette: https://congbao.chinhphu.vn/van-ban/thong-tu-so-99-2025-tt-btc-46529.htm
- English translation: https://english.luatvietnam.vn/circular-no-99-2025-tt-btc-dated-october-27-2025-of-the-ministry-of-finance-providing-guidance-on-the-enterprise-accounting-regime-417085-doc1.html
- KPMG summary: https://assets.kpmg.com/content/dam/kpmgsites/vn/pdf/2025/11/circular-99-en.pdf
- Grant Thornton guide: https://www.grantthornton.com.vn/contentassets/0b3af2858db348a0bbc26776b0152eaa/decree-99---eng-version.pdf
- Vietnam-Briefing compliance guide: https://www.vietnam-briefing.com/news/vietnam-circular-99-accounting-compliance-guide.html

---

### 1. Chart of Accounts Structure

**Regulated by:** Circular 99, Article 11, Appendix II

**Key changes from Circular 200:**
- Accounts 161, 441, 611, 631 **removed**
- New accounts added: 215 (Biological Assets), 332 (Dividends Payable), 82112 (GMT Top-Up Tax)
- Renamed: 112 → "Demand deposits" (was "Cash in banks"), "Finished goods" → "Products", "Prepaid expenses" → "Deferred expenses", "Share premium" → "Capital surplus"

**Structure (from Circular 99 Appendix II):**

| Category | Account Range | Examples |
|----------|--------------|----------|
| **1xx — Assets** | 111–244 | 111 Cash, 112 Bank deposits, 131 Trade receivables, 152 Materials, 211 Fixed assets |
| **3xx — Liabilities** | 331–357 | 331 Trade payables, 333 Taxes payable, 341 Borrowings, 352 Provisions |
| **4xx — Equity** | 411–421 | 411 Owner's equity, 412 Revaluation differences, 413 FX differences, 421 Retained earnings |
| **5xx — Revenue** | 511–521 | 511 Sales revenue, 515 Financial income, 521 Revenue deductions |
| **6xx — Expenses** | 611–641 | 611 Purchases, 632 Financial expenses, 641 Corporate income tax |
| **7xx — Production/Cost** | 711–719 | Cost of goods sold accounts |
| **8xx — Off-balance sheet** | 811–821 | Memorandum accounts |

**Account hierarchy:** Level 1 (2-digit) → Level 2 (4-digit) → Level 3 (optional, enterprise-defined)

**Enterprise flexibility (regulated):**
- Enterprises may supplement account names, codes, structures to suit operations
- Modifications must preserve economic substance and not affect financial statement line items
- Must issue internal Accounting Regulation (IGAP) documenting any changes
- Sub-accounts (Level 2/3) may be added without MoF approval for accounts not prescribed at those levels

**Application design choice:** The specific 4-digit Level 1 hierarchy and 9-category structure IS regulated. Enterprise-specific sub-accounts (Level 2/3) are application design choices. Our 4-digit AccountCode VO aligns with this requirement.

---

### 2. Fiscal Year and Period Requirements

**Regulated by:** Accounting Law No. 88/2015/QH13, Article 12; Circular 99, Articles 15, 21

**Requirements:**
- **Annual accounting period** = 12 months, by default calendar year (Jan 1 – Dec 31)
- **Alternative fiscal year** permitted: 12 full months starting first day of any quarter (Apr 1–Mar 31, Jul 1–Jun 30, Oct 1–Sep 30)
- Must notify local Tax Department if choosing non-calendar fiscal year
- **Monthly period** = 1 month; **Quarterly period** = 3 months

**First accounting period (new enterprises):**
- From date of Business Registration Certificate issuance to end of nearest annual/quarterly/monthly period
- First annual period can be < 90 days: may combine with next or prior annual period
- First annual period must be < 15 months

**Final accounting period (dissolution):**
- From start of current annual period to day before dissolution/merger effective date

**Financial statement deadlines:**
- Annual statements: within **90 days** after fiscal year end
- Interim statements: as per other laws or management requirements

**Our existing FiscalYear/FiscalPeriod entities align well:**
- FiscalYear: Year, Status (Open/Closed), Periods collection
- FiscalPeriod: YearId, Month, Status (Open/Closing/Closed), OpenedAt, ClosedAt
- PeriodClose raises PeriodClosed event — matches audit trail requirements

**Application design choice:** Whether to allow only calendar year or also alternative fiscal years is our design choice. Circular 99 permits both.

---

### 3. Currency and Exchange Rate Requirements

**Regulated by:** Circular 99, Articles 4–6

**Functional currency (Đơn vị tiền tệ trong kế toán):**
- Default: **Vietnamese Dong (VND)** — symbol "đ", international "VND"
- Foreign currency permitted if enterprise primarily transacts in foreign currency and meets 4 criteria:
  1. Currency influences selling prices and is used for settlements
  2. Currency influences labor/material costs and is used for settlements
  3. If (1) and (2) unclear: currency used for raising financial resources
  4. Currency regularly received from operations and retained as reserves
- **Once determined, functional currency cannot change** except at beginning of new fiscal year when significant operational change occurs
- Financial statements submitted to Vietnamese authorities must be in VND

**Exchange rate types (Circular 99, JPA guidance):**

| Rate Type | Use Case |
|-----------|----------|
| **Average transfer rate** | Remeasurement of monetary items at period-end; converting FS to VND |
| **Actual transaction rate** | Recording FX transactions that increase monetary/non-monetary items |
| **Book exchange rate** | Transactions that reduce FX monetary items; specific rate or weighted-average |
| **Contract rate** | Purchase/sale of FX per bank contract |

**Key rule:** Average transfer rate = arithmetic mean of transfer buying + transfer selling rates at the commercial bank with which the enterprise most frequently transacts.

**Approximation permitted:** May use approximate rate if deviation ≤ 1% from actual average bank transfer rate. Must specify whether determined weekly or monthly. Exceeding 1% = rate invalid.

**FX differences accounting:**
- Gains → Financial income (Account 515)
- Losses → Financial expenses (Account 635)
- Year-end revaluation of FX monetary items using average transfer rate

**Regulated vs design choice:**
- REGULATED: Default VND, FS must be in VND for authorities, exchange rate methodology, 1% approximation cap
- DESIGN CHOICE: Whether to support non-VND functional currency, which bank to use as primary, weekly vs monthly approximation

---

### 4. Accounting Dimensions (Department, Cost Center, Project)

**Regulated by:** Accounting Law No. 88/2015/QH13; Circular 99, Article 7

**What IS regulated:**
- Enterprises must organize accounting apparatus per Article 7 of Circular 99
- Dependent accounting units may be delegated authority to record allocated capital
- Enterprises decide organization of accounting work for affiliated units based on characteristics and management requirements
- Must not be contrary to law

**What is NOT specifically regulated:**
- Department/Cost Center/Project as formal accounting dimensions — these are NOT prescribed by Circular 99 as mandatory Chart of Accounts elements
- The Chart of Accounts in Appendix II does not include mandatory department/cost center/project codes
- Segment reporting (VAS 28) applies to large enterprises meeting specific thresholds (revenue ≥10% of total, assets ≥10% of total)

**VAS 28 — Segment Reporting:**
- Applies to enterprises meeting size thresholds
- Requires disclosure by business segment or geographical segment
- Not a mandatory dimension for all enterprises

**Our implementation approach (application design choice):**
- Department, CostCenter, Project as **optional accounting dimensions** is NOT mandated by regulation
- This is a management/accounting software design decision
- Many Vietnamese enterprise accounting systems (MISA, Fast, etc.) support department/project tracking as a software feature, not a regulatory requirement
- For SME accounting software, adding these as optional dimensions is good practice but not regulatory compliance

**Source:** Circular 99 Article 7 allows enterprises to determine organization of accounting work per management requirements; no specific accounting dimensions mandated beyond Chart of Accounts.

---

### 5. Business Rules: Mandated vs Design Choice

#### MANDATED by Regulation (Circular 99 / Accounting Law)

| Requirement | Source | Our Compliance |
|------------|--------|----------------|
| Chart of accounts must follow 9-category structure | Circular 99 Art. 11, Appendix II | ✅ Account entity with AccountType enum |
| Account codes numeric, Level 1 = 4-digit | Circular 99 Appendix II | ✅ AccountCode VO validates ≥ 4 digits |
| Financial statements = Position, P&L, Cash Flow, Notes | Circular 99 Art. 17 | ✅ DTOs exist for Position, P&L, Cash Flow |
| "Balance Sheet" renamed "Statement of Financial Position" | Circular 99 Art. 17 | ✅ BalanceSheetDto represents this |
| Annual FS due within 90 days | Circular 99 Art. 25 | Application-level enforcement |
| Books opened at fiscal year start / establishment date | Circular 99 Art. 12 | ✅ FiscalYear/FiscalPeriod entities |
| Single currency (VND) for statutory reporting | Circular 99 Art. 4, 6 | ✅ Money defaults to VND |
| FX revaluation at period-end | Circular 99 Art. 6 | Port interface exists (IForeignExchangeRateProvider) |
| Accounting Regulation (IGAP) for custom accounts | Circular 99 Art. 11 | Application-level — document storage |
| Internal controls for transaction lifecycle | Circular 99 Art. 2 | Architecture supports via audit logging |
| Postings must not be in closed periods | Circular 99 Art. 12 (book closing) | ✅ PeriodClosedException |
| Transaction balance (debits = credits) | Accounting Law, Circular 99 | ✅ ValidateBalance(), JournalEntryLine |

#### APPLICATION DESIGN CHOICES (Not Mandated)

| Design Choice | Our Approach | Rationale |
|--------------|-------------|-----------|
| Single company vs multi-tenant | Single company | Simplifies MVP; no regulatory requirement for multi-tenancy |
| Fiscal year = calendar year | Configurable | Circular 99 allows both calendar and quarter-start |
| Non-VND functional currency | Default VND, extensible | Most Vietnamese enterprises use VND |
| Department/Cost Center/Project dimensions | Optional entities | Management reporting, not regulatory mandate |
| Digital signature integration | Stub (NOT_IMPLEMENTED) | Legal requirement for e-invoicing but timing TBD |
| E-invoice provider | Stub (NOT_IMPLEMENTED) | TVAN providers (Viettel/MISA/BKAV) required for legal invoices |
| IFRS/VFRS dual reporting | IAccountingPolicy interface | Forward-looking for Circular 118/2026 (2027+) |
| Periodic repair/maintenance cost treatment | Circular 99 mandates amortization | Must update from major repair provisions |
| Biological asset accounting (Account 215) | New requirement in Circular 99 | Only if enterprise has biological assets |
| Global minimum tax (Account 82112) | New requirement in Circular 99 | Only applicable to large MNEs |

---

### 6. Key Regulatory References

| Document | Date | Status | Relevance |
|----------|------|--------|-----------|
| **Accounting Law No. 88/2015/QH13** | 20 Nov 2015 | In force (amended by Law 56/2024/QH15) | Base law governing accounting in Vietnam |
| **Circular 99/2025/TT-BTC** | 27 Oct 2025 | In force (effective 1 Jan 2026) | Primary enterprise accounting regime |
| **Circular 118/2026/TT-BTC** | 18 Aug 2026 | In force (effective 1 Jan 2027) | Optional IFRS for International Financial Center |
| **Decision 345/QĐ-BTC** | — | Referenced in MEMORY.md | IFRS transition roadmap |
| **VAS 28 — Segment Reporting** | — | In force | Segment reporting for large enterprises |
| **VAS 29 — Accounting Policy Changes** | — | In force | Transition provisions for Circular 99 adoption |
| **Law on Accounting (amended)** | 29 Nov 2024 | In force | 2024 amendments to base accounting law |
| **Decree 29/2025/ND-CP** | 24 Feb 2025 | In force | MoF organizational structure |

---

### 7. Compliance Verification Checklist

- [x] Circular 99/2025/TT-BTC is current authoritative source — confirmed
- [x] No superseding circular as of Sep 2026 — confirmed
- [x] Chart of accounts follows 9-category structure — confirmed
- [x] Account codes numeric, ≥ 4 digits — confirmed
- [x] Fiscal year/period structure aligns with Accounting Law Art. 12 — confirmed
- [x] VND as default currency — confirmed
- [x] FX rate methodology documented — confirmed
- [x] Financial statement titles correct (Statement of Financial Position, not Balance Sheet) — confirmed
- [x] 90-day annual statement deadline — confirmed
- [ ] Internal Accounting Regulation (IGAP) for custom accounts — needs implementation
- [ ] Accounting software compliance (Art. 29) — needs implementation
- [ ] FX revaluation logic — needs implementation
- [ ] Biological asset accounts (215) — optional, deferred
- [ ] GMT top-up tax (82112) — optional, deferred

## Requirements and Constraints

### 1. Domain Entity Specifications

#### Company (NEW)
| Attribute | Type | Constraints | Notes |
|-----------|------|-------------|-------|
| Id | long | BaseEntity PK | Consistent with all entities |
| Name | string | Required, max 200 | Legal entity name |
| TaxCode | string | Required, unique, pattern `\d{10}(\d{3})?` | Vietnamese tax ID (10 or 13 digits) |
| Address | string | Required | Registered address |
| Phone | string? | Optional | |
| Email | string? | Optional | |
| FiscalYearStartMonth | int | 1–12, default 1 | Which month fiscal year starts (1=calendar year) |
| FiscalYearStartDay | int | 1–28, default 1 | Day fiscal year starts (capped at 28 for Feb safety) |
| FunctionalCurrencyCode | string | Required, default "VND" | FK to Currency |
| IsActive | bool | Default true | Soft-delete pattern |

**Business rules:**
- Single company scope (per AGENTS.md constraint) — but entity still needed for FK relationships
- Functional currency set at company level; changing requires new fiscal year start + significant operational change (Circular 99 Art. 4–6)
- Fiscal year start date determines how periods are generated for that year

#### FiscalYear (EXTEND)
Current entity has `Year (int)` and `Status`. Needs:
| New Field | Type | Constraints | Notes |
|-----------|------|-------------|-------|
| CompanyId | long | FK → Company, required | Multi-company ready even if single-company MVP |
| StartDate | DateOnly | Required, computed from Company config | First day of fiscal year |
| EndDate | DateOnly | Required, computed | Last day of fiscal year |
| Description | string? | Optional | "FY2026 — Calendar Year" |

**Business rules:**
- No overlapping fiscal years per company: `StartDate..EndDate` must not intersect existing FY for same `CompanyId`
- Status transitions: Open → Closed (irreversible per Circular 99 Art. 15)
- Once closed, no period within can be reopened
- Year value must be unique per company (one FY per calendar year)
- Periods auto-generated from company's fiscal year start config

#### FiscalPeriod (REVIEW — minor changes)
Current entity has `YearId, Month, Status, OpenedAt, ClosedAt`. Needs:
| New/Changed Field | Type | Constraints | Notes |
|-------------------|------|-------------|-------|
| StartDate | DateOnly | Required | Explicit period start (not just month) |
| EndDate | DateOnly | Required | Explicit period end |
| PeriodType | enum | Monthly or Quarterly | For quarterly periods |

**Business rules:**
- Status transitions: Open → Closing → Closed (PeriodStatus enum already has these states)
- Cannot post to a closed period (already enforced via `PeriodClosedException`)
- Cannot close a period if unposted journal entries exist (integrity check)
- Period close raises `PeriodClosed` domain event (already implemented)
- Period open must be in sequential order (can't open period 3 before period 2)

#### Currency (PROMOTE to Entity)
Current VO: `record Currency(string Code, string Name, bool IsDefault)`. Needs promotion:

| Attribute | Type | Constraints | Notes |
|-----------|------|-------------|-------|
| Id | long | BaseEntity PK | |
| Code | string | Required, unique, ISO 4217 (3 chars) | "VND", "USD", "EUR" |
| Name | string | Required | "Vietnamese Dong", "US Dollar" |
| Symbol | string | Required | "đ", "$", "€" |
| DecimalPlaces | int | 0–8, default 0 for VND | Precision for display/storage |
| IsActive | bool | Default true | Can deactivate but never delete |

**Business rules:**
- VND is always active and cannot be deactivated (default functional currency)
- Currency with active ExchangeRate references cannot be deactivated
- Only one currency can be IsDefault per company (enforced at application level)
- DecimalPlaces=0 for VND (no sub-units), 2 for USD/EUR

#### ExchangeRate (NEW)
| Attribute | Type | Constraints | Notes |
|-----------|------|-------------|-------|
| Id | long | BaseEntity PK | |
| CompanyId | long | FK → Company | |
| FromCurrencyCode | string | FK → Currency.Code | Source currency |
| ToCurrencyCode | string | FK → Currency.Code | Target currency |
| Rate | decimal | Required, > 0, precision 10,6 | Exchange rate value |
| RateType | enum | Average/Actual/Book/Contract | Circular 99 Art. 6 rate types |
| EffectiveDate | DateOnly | Required | Date this rate applies |
| Source | string? | Optional | "SBV", "Bank name", etc. |

**Business rules:**
- `FromCurrencyCode != ToCurrencyCode` (no self-conversion)
- Only one rate per `(FromCurrencyCode, ToCurrencyCode, RateType, EffectiveDate)` per company
- Average transfer rate = mean of buying + selling (if RateType=Average, application validates)
- Rate must be > 0 (negative rates make no sense)
- Cannot record future-dated rates beyond 1 fiscal period

**Rate type enum:**
```
enum ExchangeRateType { Average, Actual, Book, Contract }
```

#### Chart of Accounts — Account (REVIEW)
Current entity is solid. Add:
| New/Changed Field | Type | Constraints | Notes |
|-------------------|------|-------------|-------|
| CompanyId | long | FK → Company | Multi-company ready |
| Description | string? | Optional | Account purpose description |
| NormalBalance | enum | Debit or Credit | Derived from AccountType but explicit for posting |

**Business rules (already exist, confirm):**
- AccountCode must be numeric, ≥ 4 digits (already in VO)
- Level 1 accounts (2-digit prefix) are system-defined per Circular 99 Appendix II
- Level 2+ accounts are enterprise-defined
- Account hierarchy: self-referencing tree via ParentId (already implemented)
- Deprecate() is soft-delete only (already implemented) — cannot deprecate accounts with active children
- AccountType determines normal balance: Asset/Expense → Debit, Liability/Equity/Revenue → Credit

#### AccountGroup (REVIEW)
Current entity: `Code, Name, AccountType`. Add:
| New Field | Type | Constraints | Notes |
|-----------|------|-------------|-------|
| CompanyId | long | FK → Company | |
| DisplayOrder | int | Required | For COA display ordering |

#### Accounting Dimensions (NEW — all three)
**Department:**
| Attribute | Type | Constraints |
|-----------|------|-------------|
| Id | long | BaseEntity PK |
| CompanyId | long | FK → Company |
| Code | string | Required, unique per company |
| Name | string | Required |
| IsActive | bool | Default true |

**CostCenter:**
| Attribute | Type | Constraints |
|-----------|------|-------------|
| Id | long | BaseEntity PK |
| CompanyId | long | FK → Company |
| Code | string | Required, unique per company |
| Name | string | Required |
| IsActive | bool | Default true |

**Project:**
| Attribute | Type | Constraints |
|-----------|------|-------------|
| Id | long | BaseEntity PK |
| CompanyId | long | FK → Company |
| Code | string | Required, unique per company |
| Name | string | Required |
| StartDate | DateOnly? | Optional |
| EndDate | DateOnly? | Optional |
| IsActive | bool | Default true |

**Business rules (all three dimensions):**
- Optional accounting dimensions — NOT mandated by Circular 99
- Code must be unique per company per dimension type
- Cannot deactivate a dimension with posted journal entries referencing it
- Soft-delete only (IsActive=false)
- Dimensions will attach to JournalEntryLine as optional FK references

---

### 2. Entity Relationships & Dependency Map

```
Company (1) ──── FiscalYear (1..*)
                    └──── FiscalPeriod (1..*)
Company (1) ──── Currency (*) ◄─── ExchangeRate
Company (1) ──── Account (1..*)
                    └─── AccountGroup (1..*)
                    └─── Account (self-referencing tree)
Company (1) ──── Department (0..*)
Company (1) ──── CostCenter (0..*)
Company (1) ──── Project (0..*)
```

**Dependency order (build sequence):**
```
Phase 1: Currency, Company (independent — no cross-dependencies)
Phase 2: FiscalYear → FiscalPeriod (FiscalYear depends on Company)
         ExchangeRate (depends on Currency + Company)
         AccountGroup, Account (depends on Company)
         Department, CostCenter, Project (depend on Company)
Phase 3: JournalEntryLine dimension FKs (depends on dimensions existing)
```

**Existing entity changes:**
| Entity | Action | Changes |
|--------|--------|---------|
| FiscalYear | EXTEND | Add CompanyId, StartDate, EndDate, Description |
| FiscalPeriod | EXTEND | Add StartDate, EndDate, PeriodType |
| Account | EXTEND | Add CompanyId, Description, NormalBalance |
| AccountGroup | EXTEND | Add CompanyId, DisplayOrder |
| Currency | PROMOTE | VO → Entity with Id, Symbol, DecimalPlaces, IsActive |
| Company | NEW | Full entity |
| ExchangeRate | NEW | Full entity |
| Department | NEW | Full entity |
| CostCenter | NEW | Full entity |
| Project | NEW | Full entity with dates |

---

### 3. Invariants & State Transitions

#### FiscalYear Invariants
1. No overlapping date ranges per company
2. Status: Open → Closed (irreversible)
3. All periods must be closed before FY can be closed
4. StartDate < EndDate
5. Duration must be 12 months (or 3/6 for sub-annual reporting)

#### FiscalPeriod Invariants
1. Periods are sequential within a fiscal year
2. Status: Open → Closing → Closed (forward only)
3. Cannot post to closed period (already enforced)
4. Cannot close period if journal entries have IsPosted=false in that period
5. OpenedAt set when first opened, ClosedAt set when closed

#### Currency Invariants
1. VND cannot be deactivated
2. Currency with active ExchangeRate cannot be deactivated
3. Code must be unique, non-empty, 3 characters (ISO 4217)
4. Only one IsDefault per company (application-level)

#### ExchangeRate Invariants
1. FromCurrency != ToCurrency
2. Rate > 0
3. Unique per (FromCurrency, ToCurrency, RateType, EffectiveDate) per company
4. Cannot record rate with unknown currency codes

#### Account Invariants
1. AccountCode numeric, ≥ 4 digits (existing VO validation)
2. Leaf accounts only can receive postings (existing via AccountNotLeafException)
3. Deprecated accounts cannot have children added
4. Parent must exist at Level - 1
5. AccountType consistent with parent (enforced by COA structure)

---

### 4. Constraints Summary

| Constraint | Source | Enforcement |
|------------|--------|-------------|
| Single company scope | AGENTS.md design | Application (no multi-tenant middleware) |
| Domain zero NuGet refs | Architecture tests | Build breaks on violation |
| All entities use `long` Id | BaseEntity pattern | Code convention |
| Private parameterless constructors | EF Core requirement | Code convention |
| Snake-case PostgreSQL naming | EFCore.NamingConventions | Infrastructure config |
| xmin concurrency tokens | Optimistic concurrency | All entity configs |
| VND default currency | Circular 99 Art. 4 | Money.Zero default, Currency.IsDefault |
| No self-conversion FX | Business rule | ExchangeRate domain validation |
| No posting to closed periods | Circular 99 Art. 12 | PeriodClosedException |
| Debits = Credits | Accounting equation | ValidateBalance() |
| Soft-delete only (no hard delete) | Audit trail requirement | Deprecate() pattern, IsActive flag |

## Environment and Integration

### Build Configuration

**Directory.Build.props** (`/Directory.Build.props`):
- `net10.0` target framework (shared across all projects)
- C# 13, nullable enabled, implicit usings
- `TreatWarningsAsErrors=true` — build fails on any warning

**.editorconfig** (`/.editorconfig`):
- 4-space indent, LF line endings, UTF-8
- 2-space for csproj/json/yaml
- Private fields: `_camelCase` prefix (suggestion severity)
- `var` preferred everywhere (suggestion)
- Brace on new line for all constructs
- Global using: `Xunit` (in test project only)

**Build status**: ✅ Compiles with 0 warnings, 0 errors.

### Database Schema

**PostgreSQL 16.14** on Windows host (`172.21.208.1`).
Connection: `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`

**Current tables** (7 — from InitialCreate + FixAccountNameColumn migrations):

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `accounts` | id, code (VO owned), name, level, parent_id (self-FK), account_type, is_active, account_group_id | Tree structure, xmin concurrency |
| `account_groups` | id, code, name, account_type | xmin concurrency |
| `fiscal_years` | id, year, status | xmin concurrency |
| `fiscal_periods` | id, year_id, month, status, opened_at, closed_at | FK to fiscal_years via shadow prop FiscalYearId |
| `journal_entries` | id, entry_number, date, period_id, description, source_type, source_id, posted_by, posted_at, is_posted | xmin concurrency |
| `journal_entry_lines` | id, entry_id, account_id, debit_amount, debit_currency, credit_amount, credit_currency, description | Owned Money VOs, xmin concurrency |
| `posting_references` | id, journal_entry_id, source_type, source_id | Composite index on (source_type, source_id) |

**Naming convention**: All snake_case. Applied via EFCore.NamingConventions.
**Concurrency**: `xmin` row version on every table.
**Value objects**: Money (owned — debit_amount/debit_currency, credit_amount/credit_currency), AccountCode (owned — `code` column).

**Known migration issues**: `FiscalPeriod` and `JournalEntryLine` have shadow property FK columns (`FiscalYearId`, `JournalEntryId`) that differ from configured column names (`year_id`, `entry_id`). These shadow props are unused — artifacts of EF Core auto-discovery. The correctly-named columns are the ones actually used.

### DbContext (`SmeAccountingDbContext`)

7 DbSets: Accounts, AccountGroups, JournalEntries, JournalEntryLines, FiscalYears, FiscalPeriods, PostingReferences.

- Implements `IUnitOfWork` (SaveChangesAsync)
- Ignores all 4 domain events in `OnModelCreating` (not stored in DB)
- Auto-discovers configurations via `ApplyConfigurationsFromAssembly`
- `SaveChangesAsync` collects domain events before save, then calls `PublishDomainEventAsync` (currently a no-op stub)
- New entities will need: (1) DbSet property, (2) `modelBuilder.Ignore<NewEvent>()` for any new domain events

### EF Core Configurations (7 files in `Infrastructure/Persistence/Configurations/`)

All follow consistent pattern:
- `internal sealed class XConfiguration : IEntityTypeConfiguration<X>`
- `builder.ToTable("snake_case_table_name")`
- Explicit `HasColumnName("snake_case")` for every property
- `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")` on all
- `ValueGeneratedOnAdd()` on Id
- Enums stored as strings via `.HasConversion<string>()`
- Owned types: `builder.OwnsOne(...)` for Money and AccountCode VOs

**Configuration pattern for new entities** (follow this exactly):
```csharp
internal sealed class NewEntityConfiguration : IEntityTypeConfiguration<NewEntity>
{
    public void Configure(EntityTypeBuilder<NewEntity> builder)
    {
        builder.ToTable("new_entities");
        builder.HasKey(e => e.Id);
        builder.Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd();
        // ... explicit HasColumnName for every property
        builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
    }
}
```

### Existing Migrations

2 migrations applied:
1. `20260916051341_InitialCreate` — creates all 7 tables
2. `20260916051520_FixAccountNameColumn` — renames `Name` → `name` on accounts (snake-case fix)

**Migration command**:
```bash
dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api
```

### Database Changes Needed for New Entities

| Entity | Action | New Table? | New Columns on Existing Tables |
|--------|--------|------------|-------------------------------|
| **Currency** | PROMOTE VO → Entity | `currencies` table | — |
| **Company** | NEW | `companies` table | — |
| **ExchangeRate** | NEW | `exchange_rates` table | — |
| **Department** | NEW | `departments` table | — |
| **CostCenter** | NEW | `cost_centers` table | — |
| **Project** | NEW | `projects` table | — |
| **FiscalYear** | EXTEND | — | `company_id` FK, `start_date`, `end_date`, `description` |
| **FiscalPeriod** | EXTEND | — | `start_date`, `end_date`, `period_type` |
| **Account** | EXTEND | — | `company_id` FK, `description`, `normal_balance` |
| **AccountGroup** | EXTEND | — | `company_id` FK, `display_order` |
| **JournalEntryLine** | EXTEND | — | Optional dimension FKs: `department_id`, `cost_center_id`, `project_id` |

**Migration strategy**: Single migration adding all new tables + alter statements for existing tables. Build order: Currency + Company first (no dependencies), then everything else.

### Test Infrastructure

**Framework**: xUnit 2.9.3 + NetArchTest.Rules 1.3.2
**Test project**: `tests/SmeAccounting.ArchitectureTests/` (single project, 22 tests)

**Test files** (5):
| File | Tests | What it checks |
|------|-------|----------------|
| `DomainPurityTests.cs` | 3 | No NuGet refs in Domain csproj, no Microsoft/Npgsql packages, no EFCore assembly dependency |
| `LayerCouplingTests.cs` | 4 | Controllers → Entities/Ports forbidden, Handlers → Infrastructure forbidden, Infrastructure → Api forbidden |
| `DependencyRulesTests.cs` | 7 | Domain → App/Infra/Api forbidden, App → Infra/Api forbidden, Controllers → Infra forbidden |
| `NamingConventionsTests.cs` | 6 | Entities in Entities ns, I-prefix on repositories, Command/Query/Dto/Controller suffix conventions |
| `PostingRuleIsolationTests.cs` | 2 | IPostingService in Domain assembly, balance rule enforceable in domain |

**All 22 tests pass** ✅

**Test packages**:
- xunit 2.9.3
- xunit.runner.visualstudio 3.1.4
- Microsoft.NET.Test.Sdk 17.14.1
- coverlet.collector 6.0.4
- NetArchTest.Rules 1.3.2

**What's missing** (no tests exist for):
- Unit tests for domain logic (entity methods, value objects, invariants)
- Integration tests for repositories / EF Core
- Application layer command/query handler tests
- API controller tests

### DependencyInjection Registration Pattern

**Application DI** (`AddApplication()`):
- MediatR assembly scan for commands/queries
- `ValidationBehavior<,>` open pipeline behavior
- FluentValidation validators from assembly

**Infrastructure DI** (`AddInfrastructure(IConfiguration)`):
- `SmeAccountingDbContext` via `UseNpgsql`
- `IUnitOfWork` → DbContext (scoped)
- `IAccountRepository` → `EfAccountRepository` (scoped)
- `IJournalEntryRepository` → `EfJournalEntryRepository` (scoped)
- `IClock` → `SystemClock` (singleton)
- `IAuditLogger` → `AuditLogger` (scoped)
- `IForeignExchangeRateProvider` → `BankExchangeRateProvider` (scoped)

**Pattern for new repositories**: Add `services.AddScoped<INewRepository, EfNewRepository>();` in `AddInfrastructure`. New port interfaces go in Domain/Ports, implementations in Infrastructure/Repositories.

### CI/CD & Tooling

- **No CI/CD pipeline exists** — no `.github/workflows/`, no Dockerfile, no docker-compose
- **No dotnet tools** installed globally
- **No pre-commit hooks**
- **No code coverage** configured beyond coverlet.collector reference
- **Build verification**: `dotnet build SmeAccounting.sln` (primary gate)
- **Test verification**: `dotnet test tests/SmeAccounting.ArchitectureTests/`

### Key Integration Points for Implementation

1. **DbContext changes**: Add 6 new DbSets, ignore new domain events, update `SaveChangesAsync` for new event types
2. **6 new Configuration classes** in `Infrastructure/Persistence/Configurations/` following the exact pattern of existing 7
3. **5 existing Configuration classes** need updates for new columns (FiscalYear, FiscalPeriod, Account, AccountGroup, JournalEntryLine)
4. **6 new Repository classes** + 6 new port interfaces
5. **DI registration** in `Infrastructure/DependencyInjection.cs`
6. **Single EF Core migration** for all schema changes
7. **Architecture tests**: 22 existing tests will still pass — new entities follow same conventions (BaseEntity, Entities namespace, I-prefix ports). No test changes needed unless new patterns emerge.
8. **No test infrastructure exists for unit/integration tests** — new xUnit test projects needed if we want domain logic or repository tests.

## Task-Specific Research — T1 Company + Currency

### BaseEntity Pattern (`src/SmeAccounting.Domain/Entities/BaseEntity.cs`)
```csharp
public abstract class BaseEntity
{
    public long Id { get; set; }
    private readonly List<DomainEvent> _domainEvents = [];
    public IReadOnlyCollection<DomainEvent> DomainEvents => _domainEvents.AsReadOnly();
    protected BaseEntity() { }
    protected BaseEntity(long id) => Id = id;
    public void AddDomainEvent(DomainEvent domainEvent) => _domainEvents.Add(domainEvent);
    public void RemoveDomainEvent(DomainEvent domainEvent) => _domainEvents.Remove(domainEvent);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
```
**Key:** `Id` is `long`. Two constructors: parameterless (for EF Core) + one taking `id`. Domain events managed internally.

### Account Entity Pattern (`src/SmeAccounting.Domain/Entities/Account.cs`)
- Inherits `BaseEntity`
- Properties: `public get; private set` — immutable from outside
- Private parameterless constructor: `private Account() { }`
- Public constructor with required params + null checks on reference types
- Business methods mutate state + raise domain events: `Deprecate()` sets `IsActive=false` and raises `AccountDeprecated(Id, DateTimeOffset.UtcNow)`
- Domain events raised via `AddDomainEvent(new SomeEvent(Id, DateTimeOffset.UtcNow))`
- Child collections: `private readonly List<T> _children = []; IReadOnlyCollection<T> Children => _children.AsReadOnly();`

### Currency Value Object (current — `src/SmeAccounting.Domain/ValueObjects/Currency.cs`)
```csharp
namespace SmeAccounting.Domain.ValueObjects;
public record Currency(string Code, string Name, bool IsDefault);
```
**Minimal record VO.** No validation, no Id, no Symbol, no DecimalPlaces. Referenced nowhere as an entity — just a DTO-style value object.

**Impact of promotion:** Currency must move from `ValueObjects/` to `Entities/`, change from `record` to `class : BaseEntity`, and gain Id/Symbol/DecimalPlaces/IsActive. The old VO namespace import `SmeAccounting.Domain.ValueObjects` must change to `SmeAccounting.Domain.Entities` wherever Currency is used. Money VO still references `string Currency` — no change needed there.

### Money Value Object (`src/SmeAccounting.Domain/ValueObjects/Money.cs`)
```csharp
public record Money
{
    public decimal Amount { get; }
    public string Currency { get; }
    public static Money Zero => new(0m, "VND");
    // + and - operators with currency-mismatch guards
}
```
**No change needed.** Uses `string Currency` — not a Currency VO/entity reference. Company FunctionalCurrencyCode will be a `string` for the same reason.

### EF Configuration Pattern (e.g. `AccountConfiguration.cs`)
```csharp
internal sealed class AccountConfiguration : IEntityTypeConfiguration<Account>
{
    public void Configure(EntityTypeBuilder<Account> builder)
    {
        builder.ToTable("accounts");
        builder.HasKey(e => e.Id);
        builder.Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd();
        // Explicit HasColumnName for EVERY property
        builder.Property(e => e.AccountType).HasColumnName("account_type").HasConversion<string>();
        builder.OwnsOne(e => e.Code, codeBuilder => { ... });
        builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
    }
}
```
**Conventions:** `internal sealed class`, snake_case table names, explicit `HasColumnName` on every property, enums via `HasConversion<string>()`, xmin row version on all, `ValueGeneratedOnAdd` on Id.

### Repository Pattern (e.g. `EfAccountRepository.cs`)
```csharp
public class EfAccountRepository : IAccountRepository
{
    private readonly SmeAccountingDbContext _context;
    public EfAccountRepository(SmeAccountingDbContext context) => _context = context;
    // GetByIdAsync, GetAllAsync, AddAsync, UpdateAsync
}
```
**Convention:** Constructor-injected DbContext. `GetAllAsync` uses `AsNoTracking()`. `AddAsync` just calls `AddAsync` on DbSet — UoW handles save.

### Port Interface Pattern (e.g. `IAccountRepository.cs`)
```csharp
namespace SmeAccounting.Domain.Ports;
public interface IAccountRepository
{
    Task<Account?> GetByIdAsync(long id);
    Task<IReadOnlyList<Account>> GetAllAsync();
    Task AddAsync(Account account);
    Task UpdateAsync(Account account);
}
```
**Convention:** `I{Name}Repository` in `Domain.Ports` namespace. Returns `Task<T>`. Nullable for single-get, `IReadOnlyList<T>` for list.

### Domain Event Pattern (e.g. `AccountCreated.cs`)
```csharp
public class AccountCreated : DomainEvent
{
    public long AccountId { get; }
    public AccountCreated(long accountId, DateTimeOffset occurredOn) : base(occurredOn)
    {
        AccountId = accountId;
    }
}
```
**Convention:** Extends `DomainEvent`. Stores entity ID as `long`. Constructor takes `(long entityId, DateTimeOffset occurredOn)`. Callers pass `DateTimeOffset.UtcNow`.

### DbContext Pattern (`SmeAccountingDbContext.cs`)
- DbSet properties: `public DbSet<T> Ts => Set<T>();`
- `OnModelCreating`: ignores ALL domain event types individually via `modelBuilder.Ignore<SpecificEvent>()`
- `SaveChangesAsync`: collects domain events from ChangeTracker before save, then calls `PublishDomainEventAsync` (no-op stub)
- **New entities need:** (1) DbSet property, (2) `modelBuilder.Ignore<NewEvent>()` for each new event

### DI Registration Pattern (`DependencyInjection.cs`)
```csharp
services.AddScoped<IRepository, EfRepository>();
```
**Convention:** Repositories scoped. Clock singleton. Audit/FX scoped. UnitOfWork resolves from DbContext.

### Company Entity — Required Fields per Circular 99
| Field | Type | Default | Notes |
|-------|------|---------|-------|
| Id | long | — | BaseEntity PK |
| Name | string | — | Legal name, required |
| TaxCode | string | — | Vietnamese tax ID, required, unique |
| Address | string | — | Registered address |
| Phone | string? | null | Optional |
| Email | string? | null | Optional |
| FiscalYearStartMonth | int | 1 | 1–12, default Jan |
| FiscalYearStartDay | int | 1 | 1–28, default 1 (capped at 28 for Feb) |
| FunctionalCurrencyCode | string | "VND" | Default per Circular 99 Art. 4 |
| IsActive | bool | true | Soft-delete |

**TaxCode validation:** `\d{10}(\d{3})?` — 10-digit or 13-digit numeric. Vietnamese enterprise tax ID (MST: Mã số thuế). Apply via FluentValidation on create command, not in entity constructor (entity stores validated value).

### Currency Promotion — From VO to Entity
**Old VO:** `record Currency(string Code, string Name, bool IsDefault)` in `ValueObjects/`
**New entity:** `class Currency : BaseEntity` in `Entities/`

New fields added:
| Field | Type | Notes |
|-------|------|-------|
| Id | long | BaseEntity PK |
| Symbol | string | "đ", "$", "€" |
| DecimalPlaces | int | 0 for VND, 2 for USD/EUR |
| IsActive | bool | Soft-delete |

Preserved fields: Code, Name, IsDefault (become entity properties with `public get; private set`).

**Files affected by namespace change:** Any file importing `SmeAccounting.Domain.ValueObjects` that references `Currency` must change to `SmeAccounting.Domain.Entities`. Check: Money.cs (no — uses `string Currency`), any existing Currency usages in Application/Infrastructure.

### Build Verification
```bash
dotnet build SmeAccounting.sln              # 0 warnings, 0 errors
dotnet test tests/SmeAccounting.ArchitectureTests/  # 22/22 pass
```
Architecture tests check: Entities in Entities namespace, ports have I-prefix, Domain has zero NuGet refs, no forbidden cross-layer deps. Company/Currency in Entities namespace + ICompanyRepository/ICurrencyRepository in Ports — all pass existing conventions.

## Task-Specific Research
(Preserved from prior research — see top of document for existing domain model constraints)
