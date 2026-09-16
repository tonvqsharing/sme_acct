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

## Task-Specific Research — T2 FiscalYear + FiscalPeriod

### Current FiscalYear Entity (`src/SmeAccounting.Domain/Entities/FiscalYear.cs`)
```csharp
public class FiscalYear : BaseEntity
{
    public int Year { get; private set; }
    public FiscalYearStatus Status { get; private set; } = FiscalYearStatus.Open;
    private readonly List<FiscalPeriod> _periods = [];
    public IReadOnlyCollection<FiscalPeriod> Periods => _periods.AsReadOnly();
    private FiscalYear() { }
    public FiscalYear(int year) { Year = year; }
    public FiscalPeriod AddPeriod(int month) { ... }
}
```
**Current fields:** Year (int), Status (FiscalYearStatus = Open/Closed), Periods collection.
**Missing:** CompanyId, StartDate, EndDate, Description. Constructor only takes `year`.

### Current FiscalPeriod Entity (`src/SmeAccounting.Domain/Entities/FiscalPeriod.cs`)
```csharp
public class FiscalPeriod : BaseEntity
{
    public long YearId { get; private set; }
    public int Month { get; private set; }
    public PeriodStatus Status { get; private set; } = PeriodStatus.Open;
    public DateTimeOffset? OpenedAt { get; private set; }
    public DateTimeOffset? ClosedAt { get; private set; }
    private FiscalPeriod() { }
    public FiscalPeriod(long yearId, int month) { ... }
    public void Open(DateTimeOffset openedAt) { ... }
    public void Close(DateTimeOffset closedAt) { ... AddDomainEvent(new PeriodClosed(Id, closedAt)); }
}
```
**Current fields:** YearId (long FK), Month (int), Status, OpenedAt, ClosedAt.
**Missing:** StartDate, EndDate, PeriodType. Constructor only takes `(yearId, month)`.

### Existing Enums
- **FiscalYearStatus** (`ValueObjects/FiscalYearStatus.cs`): `Open`, `Closed` — in `SmeAccounting.Domain.ValueObjects` namespace
- **PeriodStatus** (`ValueObjects/PeriodStatus.cs`): `Open`, `Closing`, `Closed` — in `SmeAccounting.Domain.ValueObjects` namespace
- **No PeriodType enum exists** — needs creation. Plan specifies: `Monthly`, `Quarterly`
- **No `Enums/` directory** — all existing enums in `ValueObjects/`. New PeriodType should follow same convention (put in `ValueObjects/` for consistency, or create `Enums/` — pick one)

### EF Core Configurations
- **FiscalYearConfiguration** (`Infrastructure/Persistence/Configurations/FiscalYearConfiguration.cs`): `fiscal_years` table, explicit HasColumnName for Year and Status, xmin row version. No FK to Company.
- **FiscalPeriodConfiguration** (`Infrastructure/Persistence/Configurations/FiscalPeriodConfiguration.cs`): `fiscal_periods` table, explicit HasColumnName for YearId, Month, Status, OpenedAt, ClosedAt, xmin row version, index on YearId. No FK to FiscalYear explicitly configured (shadow prop from navigation).

### Application Layer (Commands/Queries/DTOs)
- **Commands:** `OpenFiscalPeriodCommand(long YearId, int Month)`, `CloseFiscalPeriodCommand(long PeriodId)` — record definitions only, NO handlers exist
- **Queries:** `GetFiscalPeriodsQuery(long? YearId)` — record definition only, NO handler exists
- **DTOs:** `FiscalYearDto(long Id, int Year, string Status)`, `FiscalPeriodDto(long Id, long YearId, int Month, string Status, DateTimeOffset? OpenedAt, DateTimeOffset? ClosedAt)` — need new fields
- **Controller:** `FiscalPeriodController` — thin MediatR dispatch, takes `(yearId, month)` for Open, `(id)` for Close
- **ViewModel:** `FiscalPeriodViewModel(IReadOnlyList<FiscalPeriodDto> Periods)` — needs no structural changes but DTO changes propagate

### DbContext State
- `SmeAccountingDbContext` already has: `DbSet<FiscalYear> FiscalYears`, `DbSet<FiscalPeriod> FiscalPeriods`
- Already ignores: `PeriodClosed` event in `OnModelCreating`
- New `FiscalYearCreated` event needs `Ignore<>` added

### What Needs to Change — FiscalYear
| Change | Type | Details |
|--------|------|---------|
| CompanyId | long, required FK → Company | New property. EF will create FK constraint |
| StartDate | DateOnly, required | First day of fiscal year |
| EndDate | DateOnly, required | Last day of fiscal year |
| Description | string?, optional | "FY2026 — Calendar Year" |
| Constructor | Update | Take `(long companyId, int year, DateOnly startDate, DateOnly endDate, string? description = null)` |
| Validation | In constructor | `startDate < endDate`,CompanyId > 0 |
| Domain event | New | `FiscalYearCreated(long CompanyId, int Year, DateOnly StartDate, DateOnly EndDate)` |
| Configuration | Add columns | `company_id`, `start_date`, `end_date`, `description` with snake_case naming |
| AddPeriod method | Keep | Existing `AddPeriod(int month)` stays for backwards compat. Consider overload with start/end dates |

### What Needs to Change — FiscalPeriod
| Change | Type | Details |
|--------|------|---------|
| StartDate | DateOnly, required | Explicit period start (not just month) |
| EndDate | DateOnly, required | Explicit period end |
| PeriodType | new enum: Monthly, Quarterly | New property |
| Constructor | Update | Take `(long yearId, int month, DateOnly startDate, DateOnly endDate, PeriodType periodType)` |
| Configuration | Add columns | `start_date`, `end_date`, `period_type` with snake_case, enum as string |

### Domain Invariants to Enforce
1. **FiscalYear:** `StartDate < EndDate` — validate in constructor
2. **FiscalYear:** No overlapping FY per company — validate in repository or application layer (not pure domain, needs DB query)
3. **FiscalYear:** Status transitions: Open → Closed (irreversible) — already exists
4. **FiscalPeriod:** PeriodType determines duration — Monthly = 1 month, Quarterly = 3 months (validate in constructor or application)
5. **FiscalPeriod:** StartDate/EndDate should be within parent FiscalYear's range (application-level)

### Breaking Changes Assessment
- **No breaking changes to existing method signatures.** Commands/queries are record definitions — adding new fields to DTOs is additive.
- **Constructor changes** on FiscalYear/FiscalPeriod are breaking to existing callers, but NO callers exist outside of tests/handlers (no handlers exist). Safe to change.
- **AddPeriod(int month)** on FiscalYear still works — existing FK from FiscalPeriod.YearId unchanged.
- **FiscalPeriodDto/FiscalYearDto** records — adding new parameters changes constructor signature. Since no handlers map these yet, safe to change.

### Domain Event Pattern for FiscalYearCreated
```csharp
public class FiscalYearCreated : DomainEvent
{
    public long CompanyId { get; }
    public int Year { get; }
    public DateOnly StartDate { get; }
    public DateOnly EndDate { get; }
    public FiscalYearCreated(long companyId, int year, DateOnly startDate, DateOnly endDate, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        CompanyId = companyId; Year = year; StartDate = startDate; EndDate = endDate;
    }
}
```

### Files to Create/Modify
**Create:**
- `src/SmeAccounting.Domain/ValueObjects/PeriodType.cs` (new enum: Monthly, Quarterly)
- `src/SmeAccounting.Domain/Events/FiscalYearCreated.cs` (new domain event)

**Modify:**
- `src/SmeAccounting.Domain/Entities/FiscalYear.cs` (add CompanyId, StartDate, EndDate, Description; update constructor; add validation; add event)
- `src/SmeAccounting.Domain/Entities/FiscalPeriod.cs` (add StartDate, EndDate, PeriodType; update constructor)
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/FiscalYearConfiguration.cs` (add new column mappings)
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/FiscalPeriodConfiguration.cs` (add new column mappings, PeriodType as string conversion)
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` (Ignore FiscalYearCreated event)
- `src/SmeAccounting.Application/DTOs/FiscalYearDto.cs` (add CompanyId, StartDate, EndDate, Description)
- `src/SmeAccounting.Application/DTOs/FiscalPeriodDto.cs` (add StartDate, EndDate, PeriodType)

**No changes needed:**
- Commands (OpenFiscalPeriodCommand, CloseFiscalPeriodCommand) — signatures stay same
- Queries (GetFiscalPeriodsQuery) — signature stays same
- Controller (FiscalPeriodController) — dispatches via MediatR, no direct entity access
- ViewModel (FiscalPeriodViewModel) — wraps DTOs, structural change is DTO-propagated

### FK Relationship
- FiscalYear gets `CompanyId` as a required FK → Company (configured via `builder.HasOne<Company>()...HasForeignKey("CompanyId")` in config or via convention if navigation added)
- FiscalPeriod already has `YearId` FK → FiscalYear (via shadow property + index)
- No direct FK from FiscalPeriod to Company (goes through FiscalYear)

## Task-Specific Research — T3 ExchangeRate

### Existing IForeignExchangeRateProvider Port (`src/SmeAccounting.Domain/Ports/IForeignExchangeRateProvider.cs`)
```csharp
public interface IForeignExchangeRateProvider
{
    Task<Money> ConvertAsync(Money amount, string targetCurrency, DateTimeOffset date);
}
```
**Key insight:** This is an *adapter port* for converting money — NOT the same as an exchange rate *repository*. It takes Money + target + date and returns converted Money. ExchangeRate entity/repository is a separate concern: it stores rates, while this provider uses them. Both can coexist. The ExchangeRate entity could eventually back this provider (replace mock BankExchangeRateProvider).

### BankExchangeRateProvider Adapter (`src/SmeAccounting.Infrastructure/Adapters/BankExchangeRateProvider.cs`)
```csharp
public class BankExchangeRateProvider : IForeignExchangeRateProvider
{
    public Task<Money> ConvertAsync(Money amount, string targetCurrency, DateTimeOffset date)
    {
        if (amount.Currency == targetCurrency)
            return Task.FromResult(amount);
        decimal mockRate = amount.Currency switch { ... };
        return Task.FromResult(new Money(converted, targetCurrency));
    }
}
```
**Current state:** Hardcoded mock rates (VND↔USD=25000, VND↔EUR=27000). No date awareness. Registered as scoped in DI. T3 ExchangeRate entity is the *data store* for real rates — BankExchangeRateProvider is the *consumer* (adapter that looks up rates). No changes to this adapter needed for T3 — future task can wire it to ExchangeRate entity.

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
**Key:** Uses `string Currency` — NOT a FK to Currency entity. ExchangeRate stores `FromCurrencyCode` and `ToCurrencyCode` as `string` matching this pattern. No coupling between Money and ExchangeRate entity.

### Currency Entity (`src/SmeAccounting.Domain/Entities/Currency.cs`)
```csharp
public class Currency : BaseEntity
{
    public string Code { get; private set; }    // ISO 4217 3-char, validated
    public string Name { get; private set; }
    public string Symbol { get; private set; }
    public int DecimalPlaces { get; private set; }  // default 2
    public bool IsDefault { get; private set; }
    public bool IsActive { get; private set; } = true;
}
```
**Relevance for T3:** ExchangeRate references currencies by `string Code` (not FK). No FK constraint at DB level. Application layer should validate currency codes exist. Domain invariant: `FromCurrencyCode != ToCurrencyCode` enforced in entity constructor.

### No Existing ExchangeRate Files
- No `ExchangeRate` entity, no `IExchangeRateRepository` port, no `ExchangeRateRecorded` event, no `ExchangeRateType` enum
- Grep confirmed: only `IForeignExchangeRateProvider` mentions "ExchangeRate" in codebase

### ExchangeRateType Enum — Where to Put It
- No `Enums/` directory exists — all enums live in `ValueObjects/`: AccountType, PeriodStatus, FiscalYearStatus, PeriodType
- **Decision:** Put `ExchangeRateType` in `ValueObjects/` for consistency with existing pattern
- Values per PLAN: `Average`, `Actual`, `Book`, `Contract`
- Circular 99 Art. 6 mapping:
  - Average = remeasurement of monetary items at period-end; converting FS to VND
  - Actual = recording FX transactions that increase monetary/non-monetary items
  - Book = transactions that reduce FX monetary items; specific rate or weighted-average
  - Contract = purchase/sale of FX per bank contract

### ExchangeRate Entity — Field Specification (from PLAN)
| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| Id | long | BaseEntity PK | |
| CompanyId | long | FK → Company, required | Multi-company ready |
| FromCurrencyCode | string | Required, references Currency.Code | Source currency code |
| ToCurrencyCode | string | Required, references Currency.Code | Target currency code |
| Rate | decimal(10,6) | Required, > 0 | Exchange rate value |
| RateType | ExchangeRateType enum | Required | Average/Actual/Book/Contract |
| EffectiveDate | DateOnly | Required | Date this rate applies |
| Source | string? | Optional | "SBV", "Bank name", etc. |

### Domain Invariants to Enforce
1. **FromCurrencyCode != ToCurrencyCode** — no self-conversion. Throw `DomainException` (new subclass or inline)
2. **Rate > 0** — negative/zero rates make no sense. Throw `DomainException`
3. **Unique per (CompanyId, FromCurrencyCode, ToCurrencyCode, RateType, EffectiveDate)** — enforced at application/repository level (composite unique index in config)

### Domain Event Pattern for ExchangeRateRecorded
```csharp
public class ExchangeRateRecorded : DomainEvent
{
    public long ExchangeRateId { get; }
    public long CompanyId { get; }
    public string FromCurrencyCode { get; }
    public string ToCurrencyCode { get; }
    public decimal Rate { get; }
    public ExchangeRateRecorded(long exchangeRateId, long companyId, string fromCurrencyCode,
        string toCurrencyCode, decimal rate, DateTimeOffset occurredOn) : base(occurredOn)
    {
        ExchangeRateId = exchangeRateId; CompanyId = companyId;
        FromCurrencyCode = fromCurrencyCode; ToCurrencyCode = toCurrencyCode; Rate = rate;
    }
}
```
**Convention:** Follows CompanyCreated/FiscalYearCreated pattern — entity ID + key fields + occurredOn from base.

### IExchangeRateRepository — Port Interface Design
```csharp
public interface IExchangeRateRepository
{
    Task<ExchangeRate?> GetByIdAsync(long id);
    Task<ExchangeRate?> GetByCurrencyPairAsync(string fromCurrencyCode, string toCurrencyCode,
        ExchangeRateType rateType, DateOnly effectiveDate, long companyId);
    Task<IReadOnlyList<ExchangeRate>> GetAllAsync();
    Task AddAsync(ExchangeRate exchangeRate);
}
```
**Key method:** `GetByCurrencyPairAsync` — looks up the specific rate for a currency pair + rate type + date + company. This is the primary lookup for the IForeignExchangeRateProvider adapter to consume. Nullable return (rate might not exist yet).

### EF Core Configuration Pattern
```csharp
internal sealed class ExchangeRateConfiguration : IEntityTypeConfiguration<ExchangeRate>
{
    public void Configure(EntityTypeBuilder<ExchangeRate> builder)
    {
        builder.ToTable("exchange_rates");
        builder.HasKey(e => e.Id);
        builder.Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd();
        builder.Property(e => e.CompanyId).HasColumnName("company_id");
        builder.Property(e => e.FromCurrencyCode).HasColumnName("from_currency_code").HasMaxLength(3);
        builder.Property(e => e.ToCurrencyCode).HasColumnName("to_currency_code").HasMaxLength(3);
        builder.Property(e => e.Rate).HasColumnName("rate").HasColumnType("decimal(10,6)");
        builder.Property(e => e.RateType).HasColumnName("rate_type").HasConversion<string>();
        builder.Property(e => e.EffectiveDate).HasColumnName("effective_date");
        builder.Property(e => e.Source).HasColumnName("source").HasMaxLength(200);
        // Composite unique index for rate lookup
        builder.HasIndex(e => new { e.CompanyId, e.FromCurrencyCode, e.ToCurrencyCode, e.RateType, e.EffectiveDate })
            .IsUnique();
        // FK to Company
        builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);
        builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
    }
}
```
**Key decisions:**
- `HasConversion<string>()` on RateType (same as PeriodStatus, FiscalYearStatus, PeriodType)
- `HasColumnType("decimal(10,6)")` for Rate precision
- Composite unique index prevents duplicate rates per (company, pair, type, date)
- FK to Company with `Restrict` delete (same pattern as FiscalYear)
- `HasMaxLength(3)` on currency code columns (ISO 4217)

### Repository Pattern (from EfCompanyRepository)
- Constructor-injected `SmeAccountingDbContext`
- `GetAllAsync()` uses `AsNoTracking()`
- `AddAsync` just calls `_context.Set.AddAsync` — UoW handles save
- `GetByCurrencyPairAsync` will need composite key lookup with `FirstOrDefaultAsync`

### DbContext Changes Needed
- Add `DbSet<ExchangeRate> ExchangeRates => Set<ExchangeRate>();`
- Add `modelBuilder.Ignore<ExchangeRateRecorded>();` in `OnModelCreating`

### DI Registration
- `services.AddScoped<IExchangeRateRepository, EfExchangeRateRepository>();`

### Domain Exception Decision
- PLAN says: "No self-conversion (same currency codes) throws DomainException"
- Can use existing `DomainException` base class directly (no need for a subclass — `DomainException("FromCurrencyCode and ToCurrencyCode must be different.")` is sufficient)
- Alternative: `SelfConversionException` subclass for more specific catching — but over-engineering for this case
- **Decision:** Use `DomainException` directly with descriptive message (consistent with `InvalidPostingRuleException` pattern but no custom subclass needed)

### Breaking Changes Assessment
- **No existing ExchangeRate entity, repo, or event** — everything is new, no breaking changes
- `IForeignExchangeRateProvider` port stays unchanged — it's a separate adapter concern
- `BankExchangeRateProvider` stays unchanged — mock adapter, future task can wire to ExchangeRate entity
- Money VO stays unchanged — uses `string Currency` throughout

### Files to Create
1. `src/SmeAccounting.Domain/ValueObjects/ExchangeRateType.cs` (new enum)
2. `src/SmeAccounting.Domain/Entities/ExchangeRate.cs` (new entity)
3. `src/SmeAccounting.Domain/Events/ExchangeRateRecorded.cs` (new domain event)
4. `src/SmeAccounting.Domain/Ports/IExchangeRateRepository.cs` (new port interface)
5. `src/SmeAccounting.Infrastructure/Persistence/Configurations/ExchangeRateConfiguration.cs` (new config)
6. `src/SmeAccounting.Infrastructure/Repositories/EfExchangeRateRepository.cs` (new repository)

### Files to Modify
1. `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` (Add DbSet + Ignore event)
2. `src/SmeAccounting.Infrastructure/DependencyInjection.cs` (Register repository)

### Unique Constraint Approach
- Composite unique index: `(CompanyId, FromCurrencyCode, ToCurrencyCode, RateType, EffectiveDate)`
- Prevents duplicate rates for same pair+type+date per company
- DB-level enforcement (EF Core config), not just application-level
- One rate per (pair, type, date, company) — users override by creating new record if needed

### FK Relationship
- ExchangeRate.CompanyId → Company (required FK, Restrict delete)
- FromCurrencyCode/ToCurrencyCode are NOT FKs to Currency entity — they reference Currency.Code by value (string match)
- This matches the pattern used by MoneyVO (string Currency, not FK) and FunctionalCurrencyCode on Company

## Task-Specific Research — T4 COA

### Current Account Entity (`src/SmeAccounting.Domain/Entities/Account.cs`)
```csharp
public class Account : BaseEntity
{
    public AccountCode Code { get; private set; } = null!;
    public string Name { get; private set; } = string.Empty;
    public int Level { get; private set; }
    public long? ParentId { get; private set; }
    public AccountType AccountType { get; private set; }
    public bool IsActive { get; private set; } = true;
    public long? AccountGroupId { get; private set; }
    private readonly List<Account> _children = [];
    public IReadOnlyCollection<Account> Children => _children.AsReadOnly();
    private Account() { }
    public Account(AccountCode code, string name, AccountType accountType, int level = 1, long? parentId = null, long? accountGroupId = null) { ... }
    public void Deprecate() { ... }
    public Account AddChild(AccountCode code, string name, AccountType accountType, long? accountGroupId = null) { ... }
}
```
**Current fields:** Code (AccountCode VO owned), Name, Level, ParentId (self-FK), AccountType (enum), IsActive, AccountGroupId (FK).
**Missing:** CompanyId (long FK → Company), Description (string?), NormalBalance (enum).
**Constructor takes:** (code, name, accountType, level, parentId, accountGroupId). CompanyId must be added as required param.

### Current AccountGroup Entity (`src/SmeAccounting.Domain/Entities/AccountGroup.cs`)
```csharp
public class AccountGroup : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public AccountType AccountType { get; private set; }
    private AccountGroup() { }
    public AccountGroup(string code, string name, AccountType accountType) { ... }
}
```
**Current fields:** Code (string), Name (string), AccountType (enum).
**Missing:** CompanyId (long FK → Company), DisplayOrder (int).
**Constructor takes:** (code, name, accountType). CompanyId must be added as required param.

### AccountType Enum (`src/SmeAccounting.Domain/ValueObjects/AccountType.cs`)
```csharp
namespace SmeAccounting.Domain.ValueObjects;
public enum AccountType { Asset, Liability, Equity, Revenue, Expense }
```
**Location:** `ValueObjects/` — NOT a separate `Enums/` directory. All existing enums live in ValueObjects: AccountType, PeriodStatus, FiscalYearStatus, PeriodType, ExchangeRateType. New NormalBalance must follow same convention.

### NormalBalance Enum — Does NOT Exist
No NormalBalance enum anywhere in codebase. Needs creation in `ValueObjects/NormalBalance.cs`.
- Values: `Debit`, `Credit`
- Derivation rule: Asset/Expense → Debit, Liability/Equity/Revenue → Credit
- PLAN says "stored explicitly for posting clarity" — so it's a DB column, not just derived logic

### Existing AccountConfiguration (`Infrastructure/Persistence/Configurations/AccountConfiguration.cs`)
- Table: `accounts`
- snake_case columns: `id`, `level`, `name`, `parent_id`, `account_type`, `is_active`, `account_group_id`
- `AccountCode` owned VO → `code` column (HasMaxLength(20))
- AccountType: `HasConversion<string>()`
- Self-referencing FK: `HasOne<Account>().WithMany(a => a.Children).HasForeignKey(e => e.ParentId).OnDelete(DeleteBehavior.Restrict)`
- Index on `parent_id`
- xmin concurrency token
- **Needs additions:** `company_id` (long FK), `description` (string?), `normal_balance` (string via HasConversion)

### Existing AccountGroupConfiguration (`Infrastructure/Persistence/Configurations/AccountGroupConfiguration.cs`)
- Table: `account_groups`
- snake_case columns: `id`, `code`, `name`, `account_type`
- AccountType: `HasConversion<string>()`
- Code: HasMaxLength(20), Name: HasMaxLength(200)
- xmin concurrency token
- **Needs additions:** `company_id` (long FK), `display_order` (int)

### FK Pattern to Company (from T2 FiscalYear + T3 ExchangeRate)
```csharp
builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);
```
- Required FK (not nullable)
- Restrict delete (prevent cascade)
- No navigation property on Account/AccountGroup to Company (just FK column)
- Pattern consistent across FiscalYear, ExchangeRate

### Application Layer — Commands/Queries/DTOs

**CreateAccountCommand** — currently `(Code, Name, AccountType, ParentId, AccountGroupId)`. Needs:
- Add `CompanyId` (long, required) — accounts belong to a company
- Add `Description` (string?, optional)
- Add `NormalBalance` (NormalBalance enum, required)

**DeprecateAccountCommand** — `(AccountId)`. **No changes needed.** Deprecation is by ID only.

**GetAccountQuery** — `(AccountId)`. **No changes needed.** Returns AccountDto.

**GetAccountsByGroupQuery** — `(AccountGroupId)`. **No changes needed.** Returns IReadOnlyList<AccountDto>.

**AccountDto** — currently `(Id, Code, Name, Level, ParentId, AccountType, IsActive, AccountGroupId)`. Needs:
- Add `CompanyId` (long)
- Add `Description` (string?)
- Add `NormalBalance` (string — DTO uses string not enum, per convention from FiscalPeriodDto)

### Domain Events — AccountCreated/AccountDeprecated
- `AccountCreated(long AccountId, DateTimeOffset occurredOn)` — **No changes needed.** T4 is about extending fields, not changing event contract.
- `AccountDeprecated(long AccountId, DateTimeOffset occurredOn)` — **No changes needed.**

### DbContext Changes Needed
- Already has: `DbSet<Account>`, `DbSet<AccountGroup>`, ignores `AccountCreated`, `AccountDeprecated`
- **No new DbSets needed** — Account/AccountGroup already registered
- **No new domain events to ignore** — AccountCreated/AccountDeprecated already ignored
- **No DI changes needed** — `IAccountRepository` + `EfAccountRepository` already registered

### Invariants to Enforce
1. **CompanyId > 0** — validate in entity constructor (required param)
2. **NormalBalance consistent with AccountType** — Asset/Expense → Debit, Liability/Equity/Revenue → Credit. Could validate in constructor but PLAN says "stored explicitly for posting clarity" — allow override? Or validate invariant? **Decision: validate invariant in constructor** (NormalBalance must match AccountType). Prevents data corruption.
3. **DisplayOrder >= 0** — validate in AccountGroup constructor
4. **No existing unique constraint on (CompanyId, Code) for AccountGroup** — but should be unique per company? PLAN says "DisplayOrder (int)" only. No unique constraint specified. **Skip for now** — application-level enforcement.

### Constructor Changes

**Account constructor** — new signature:
```csharp
public Account(AccountCode code, string name, AccountType accountType, long companyId,
    NormalBalance normalBalance, int level = 1, long? parentId = null, long? accountGroupId = null,
    string? description = null)
```
- `companyId` required (CompanyId > 0 validation)
- `normalBalance` required (validate matches AccountType)
- `description` optional
- `level`, `parentId`, `accountGroupId` remain optional with defaults

**AddChild method** — needs companyId and normalBalance passed through:
```csharp
public Account AddChild(AccountCode code, string name, AccountType accountType, long companyId,
    NormalBalance normalBalance, long? accountGroupId = null, string? description = null)
```

**AccountGroup constructor** — new signature:
```csharp
public AccountGroup(string code, string name, AccountType accountType, long companyId, int displayOrder = 0)
```
- `companyId` required (CompanyId > 0 validation)
- `displayOrder` optional with default 0

### Files to Create
1. `src/SmeAccounting.Domain/ValueObjects/NormalBalance.cs` (new enum: Debit, Credit)

### Files to Modify
1. `src/SmeAccounting.Domain/Entities/Account.cs` — add CompanyId, Description, NormalBalance fields; update constructor; update AddChild; add NormalBalance validation
2. `src/SmeAccounting.Domain/Entities/AccountGroup.cs` — add CompanyId, DisplayOrder fields; update constructor
3. `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountConfiguration.cs` — add company_id FK, description, normal_balance columns
4. `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountGroupConfiguration.cs` — add company_id FK, display_order column
5. `src/SmeAccounting.Application/Commands/CreateAccountCommand.cs` — add CompanyId, Description, NormalBalance params
6. `src/SmeAccounting.Application/DTOs/AccountDto.cs` — add CompanyId, Description, NormalBalance fields

### Files NOT Modified
- `DeprecateAccountCommand.cs` — no changes (takes AccountId only)
- `GetAccountQuery.cs` — no changes (takes AccountId)
- `GetAccountsByGroupQuery.cs` — no changes (takes AccountGroupId)
- `AccountCreated.cs` — no changes (event contract unchanged)
- `AccountDeprecated.cs` — no changes (event contract unchanged)
- `SmeAccountingDbContext.cs` — no changes (Account/AccountGroup already have DbSets, events already ignored)
- `DependencyInjection.cs` — no changes (IAccountRepository already registered)
- `IAccountRepository.cs` — no changes (port interface stays same)

### Breaking Changes Assessment
- **Account constructor change** — breaking to any callers. No handlers exist for CreateAccountCommand yet (command is just a record definition, no handler implementation). Safe to change.
- **AddChild method change** — breaking to callers. Only called within Account entity itself (in existing AddChild method). Safe to change.
- **AccountGroup constructor change** — breaking to callers. No callers exist. Safe to change.
- **CreateAccountCommand change** — adding params to record. No handler exists. Safe to change.
- **AccountDto change** — adding params to record. No handler maps this yet. Safe to change.
- **All changes are additive** — existing method signatures on Account (Deprecate) and AccountGroup (none) are unaffected.

### NormalBalance Invariant Validation
```csharp
private static NormalBalance DetermineNormalBalance(AccountType accountType) => accountType switch
{
    AccountType.Asset => NormalBalance.Debit,
    AccountType.Expense => NormalBalance.Debit,
    AccountType.Liability => NormalBalance.Credit,
    AccountType.Equity => NormalBalance.Credit,
    AccountType.Revenue => NormalBalance.Credit,
    _ => throw new ArgumentOutOfRangeException(nameof(accountType))
};
```
Validate in constructor: `if (normalBalance != DetermineNormalBalance(accountType)) throw new DomainException(...)`
This prevents data corruption while storing the value explicitly for posting clarity.

### Verification — Source Files Confirmed

#### Account.cs (actual — `src/SmeAccounting.Domain/Entities/Account.cs`)
- Line 21: Constructor `Account(AccountCode code, string name, AccountType accountType, int level = 1, long? parentId = null, long? accountGroupId = null)`
- Line 37: `AddChild(AccountCode code, string name, AccountType accountType, long? accountGroupId = null)`
- No CompanyId, no Description, no NormalBalance — confirmed missing
- AccountCreated event at `src/SmeAccounting.Domain/Events/AccountCreated.cs` — takes `(long accountId, DateTimeOffset occurredOn)` — NO changes needed (event contract unchanged)

#### AccountGroup.cs (actual — `src/SmeAccounting.Domain/Entities/AccountGroup.cs`)
- Line 13: Constructor `AccountGroup(string code, string name, AccountType accountType)`
- No CompanyId, no DisplayOrder — confirmed missing

#### AccountConfiguration.cs (actual — `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountConfiguration.cs`)
- Table: `accounts`
- Existing columns: `id`, `level`, `name`, `parent_id`, `account_type`, `is_active`, `account_group_id`, owned `code`
- Self-referencing FK with Restrict delete on ParentId
- xmin concurrency token present
- Missing: `company_id`, `description`, `normal_balance`

#### AccountGroupConfiguration.cs (actual — `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountGroupConfiguration.cs`)
- Table: `account_groups`
- Existing columns: `id`, `code` (HasMaxLength 20), `name` (HasMaxLength 200), `account_type`
- xmin concurrency token present
- Missing: `company_id`, `display_order`

#### AccountType.cs (actual — `src/SmeAccounting.Domain/ValueObjects/AccountType.cs`)
- Namespace: `SmeAccounting.Domain.ValueObjects` — NOT a separate `Enums/` directory
- Values: `Asset, Liability, Equity, Revenue, Expense`

#### NormalBalance enum — Does NOT Exist
- No `NormalBalance` anywhere in codebase (grep confirmed)
- Must create in `ValueObjects/NormalBalance.cs` (not `Enums/`)

#### FK to Company Pattern (from FiscalYearConfiguration — verified)
```csharp
builder.HasOne<Company>()
    .WithMany()
    .HasForeignKey(e => e.CompanyId)
    .OnDelete(DeleteBehavior.Restrict);
```
- No navigation property on Account/AccountGroup to Company — just FK column
- Restrict delete prevents cascade

#### DbContext — No Changes Needed
- `SmeAccountingDbContext` already has `DbSet<Account>` and `DbSet<AccountGroup>` (lines 10-11)
- Already ignores `AccountCreated` and `AccountDeprecated` events (lines 27-28)
- No new events to add for T4

#### Application Layer — Commands/DTOs
- **CreateAccountCommand**: `(string Code, string Name, AccountType AccountType, long? ParentId, long? AccountGroupId)` — needs CompanyId, Description, NormalBalance added
- **DeprecateAccountCommand**: `(long AccountId)` — NO changes needed
- **AccountDto**: `(long Id, string Code, string Name, int Level, long? ParentId, string AccountType, bool IsActive, long? AccountGroupId)` — needs CompanyId, Description, NormalBalance added

#### IAccountRepository — No Changes Needed
- Port interface stays same: `GetByIdAsync, GetAllAsync, AddAsync, UpdateAsync`
- FK is configured at EF level, not port level

### Executor Checklist — Exact Changes Needed

**Files to CREATE (1):**
1. `src/SmeAccounting.Domain/ValueObjects/NormalBalance.cs` — enum: `Debit, Credit`

**Files to MODIFY (6):**
1. `src/SmeAccounting.Domain/Entities/Account.cs` — add `CompanyId` (long), `Description` (string?), `NormalBalance` (enum); update constructor signature; update `AddChild` method; add invariant validation
2. `src/SmeAccounting.Domain/Entities/AccountGroup.cs` — add `CompanyId` (long), `DisplayOrder` (int); update constructor signature
3. `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountConfiguration.cs` — add `company_id` FK, `description`, `normal_balance` (HasConversion<string>); add FK to Company with Restrict
4. `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountGroupConfiguration.cs` — add `company_id` FK, `display_order`; add FK to Company with Restrict
5. `src/SmeAccounting.Application/Commands/CreateAccountCommand.cs` — add `CompanyId`, `Description`, `NormalBalance` params
6. `src/SmeAccounting.Application/DTOs/AccountDto.cs` — add `CompanyId`, `Description`, `NormalBalance` fields

**Files NOT modified (confirmed safe):**
- `AccountCreated.cs` — event contract unchanged
- `AccountDeprecated.cs` — event contract unchanged
- `SmeAccountingDbContext.cs` — Account/AccountGroup already have DbSets, events already ignored
- `DependencyInjection.cs` — IAccountRepository already registered
- `IAccountRepository.cs` — port interface stays same
- `DeprecateAccountCommand.cs` — takes AccountId only, no changes
- `GetAccountQuery.cs` / `GetAccountsByGroupQuery.cs` — no changes

### Account.Group display order: default 0
- PLAN says `DisplayOrder (int)` on AccountGroup — no default specified
- Suggested: `int displayOrder = 0` in constructor — allows flexible ordering without requiring explicit value

## Task-Specific Research — T5 Dimensions

### Current JournalEntryLine Entity (`src/SmeAccounting.Domain/Entities/JournalEntryLine.cs`)
```csharp
public class JournalEntryLine : BaseEntity
{
    public long EntryId { get; private set; }
    public long AccountId { get; private set; }
    public Money Debit { get; private set; } = Money.Zero;
    public Money Credit { get; private set; } = Money.Zero;
    public string? Description { get; private set; }

    private JournalEntryLine() { }

    public JournalEntryLine(long entryId, long accountId, Money debit, Money credit, string? description = null)
    {
        EntryId = entryId;
        AccountId = accountId;
        Debit = debit ?? throw new ArgumentNullException(nameof(debit));
        Credit = credit ?? throw new ArgumentNullException(nameof(credit));
        Description = description;
    }
}
```
**Current fields:** EntryId (long), AccountId (long), Debit (Money), Credit (Money), Description (string?).
**Missing:** DepartmentId (long?), CostCenterId (long?), ProjectId (long?). All optional FKs.

### Current JournalEntryLineConfiguration (`src/SmeAccounting.Infrastructure/Persistence/Configurations/JournalEntryLineConfiguration.cs`)
- Table: `journal_entry_lines`
- Existing columns: `id`, `entry_id`, `account_id`, `description`, owned Money (`debit_amount`/`debit_currency`, `credit_amount`/`credit_currency`)
- Indexes on: `entry_id`, `account_id`
- xmin concurrency token present
- **Missing:** `department_id`, `cost_center_id`, `project_id` — all nullable FK columns
- **No FK constraints yet** for EntryId/AccountId to their respective entities (shadow props from EF auto-discovery, not explicit config)

### Dimension Entity Pattern (from ExchangeRate — closest match)
ExchangeRate is the best template for dimension entities because it:
- Has CompanyId FK (required)
- Uses string Code with uniqueness per company
- Has IsActive for soft-delete
- Raises domain event in constructor

**Pattern to follow for Department/CostCenter/Project:**
```csharp
public class Department : BaseEntity
{
    public long CompanyId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public bool IsActive { get; private set; } = true;

    private Department() { }

    public Department(long companyId, string code, string name)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");

        CompanyId = companyId;
        Code = code;
        Name = name;

        AddDomainEvent(new DepartmentCreated(Id, companyId, DateTimeOffset.UtcNow));
    }
}
```
Project adds `StartDate` (DateOnly?) and `EndDate` (DateOnly?) fields.

### FK to Company Pattern (confirmed from FiscalYear, ExchangeRate)
```csharp
builder.HasOne<Company>()
    .WithMany()
    .HasForeignKey(e => e.CompanyId)
    .OnDelete(DeleteBehavior.Restrict);
```
- Required FK (not nullable)
- Restrict delete (prevent cascade)
- No navigation property on dimension entities to Company (just FK column)
- Pattern consistent across FiscalYear, FiscalPeriod, ExchangeRate

### Unique Constraints — Composite Index Per Dimension
Code must be unique per company per dimension type. DB-level enforcement via composite unique index:

```csharp
// Department: unique (CompanyId, Code)
builder.HasIndex(e => new { e.CompanyId, e.Code }).IsUnique();

// CostCenter: unique (CompanyId, Code)
builder.HasIndex(e => new { e.CompanyId, e.Code }).IsUnique();

// Project: unique (CompanyId, Code)
builder.HasIndex(e => new { e.CompanyId, e.Code }).IsUnique();
```
This prevents duplicate codes per company per dimension type at DB level.

### JournalEntryLine Extension — Optional FK Columns
JournalEntryLine gets three new nullable FK properties:

```csharp
public long? DepartmentId { get; private set; }
public long? CostCenterId { get; private set; }
public long? ProjectId { get; private set; }
```

**Configuration additions:**
```csharp
builder.Property(e => e.DepartmentId).HasColumnName("department_id");
builder.Property(e => e.CostCenterId).HasColumnName("cost_center_id");
builder.Property(e => e.ProjectId).HasColumnName("project_id");

// Optional FK constraints (nullable — no Restrict needed, SetNull is fine)
builder.HasOne<Department>().WithMany().HasForeignKey(e => e.DepartmentId).OnDelete(DeleteBehavior.SetNull);
builder.HasOne<CostCenter>().WithMany().HasForeignKey(e => e.CostCenterId).OnDelete(DeleteBehavior.SetNull);
builder.HasOne<Project>().WithMany().HasForeignKey(e => e.ProjectId).OnDelete(DeleteBehavior.SetNull);
```
- Nullable FKs — dimension can be null (optional)
- `SetNull` delete behavior — if dimension deleted, lines keep data but lose dimension reference
- Indexes on each FK column for query performance

### JournalEntryLine Constructor Update
```csharp
public JournalEntryLine(long entryId, long accountId, Money debit, Money credit,
    string? description = null, long? departmentId = null, long? costCenterId = null, long? projectId = null)
{
    EntryId = entryId;
    AccountId = accountId;
    Debit = debit ?? throw new ArgumentNullException(nameof(debit));
    Credit = credit ?? throw new ArgumentNullException(nameof(credit));
    Description = description;
    DepartmentId = departmentId;
    CostCenterId = costCenterId;
    ProjectId = projectId;
}
```
All new params optional with defaults — backwards compatible with existing callers.

### JournalEntry.AddLine Method Update
`AddLine` in JournalEntry.cs needs to pass through the new optional params:
```csharp
public JournalEntryLine AddLine(long accountId, Money debit, Money credit,
    string? description = null, long? departmentId = null, long? costCenterId = null, long? projectId = null)
{
    if (IsPosted)
        throw new DomainException("Cannot modify a posted journal entry.");

    var line = new JournalEntryLine(Id, accountId, debit, credit, description, departmentId, costCenterId, projectId);
    _lines.Add(line);
    return line;
}
```

### Domain Events Pattern
Each dimension raises a created event in constructor:
```csharp
public class DepartmentCreated : DomainEvent
{
    public long DepartmentId { get; }
    public long CompanyId { get; }

    public DepartmentCreated(long departmentId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        DepartmentId = departmentId;
        CompanyId = companyId;
    }
}
```
Same pattern for `CostCenterCreated` and `ProjectCreated`. Follows `ExchangeRateRecorded` pattern (entity ID + CompanyId + occurredOn).

### Port Interface Pattern
```csharp
namespace SmeAccounting.Domain.Ports;

public interface IDepartmentRepository
{
    Task<Department?> GetByIdAsync(long id);
    Task<Department?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<Department>> GetAllAsync();
    Task AddAsync(Department department);
}
```
Same pattern for `ICostCenterRepository` and `IProjectRepository`. `GetByCodeAsync` enables application-level duplicate code check.

### Repository Pattern
```csharp
public class EfDepartmentRepository : IDepartmentRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfDepartmentRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Department?> GetByIdAsync(long id)
    {
        return await _context.Departments.FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<Department?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.Departments
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<Department>> GetAllAsync()
    {
        return await _context.Departments
            .AsNoTracking()
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(Department department)
    {
        await _context.Departments.AddAsync(department);
    }
}
```
Same pattern for `EfCostCenterRepository` and `EfProjectRepository`.

### DbContext Changes Needed
- Add `DbSet<Department> Departments => Set<Department>();`
- Add `DbSet<CostCenter> CostCenters => Set<CostCenter>();`
- Add `DbSet<Project> Projects => Set<Project>();`
- Add `modelBuilder.Ignore<DepartmentCreated>();`
- Add `modelBuilder.Ignore<CostCenterCreated>();`
- Add `modelBuilder.Ignore<ProjectCreated>();`

### DI Registration
```csharp
services.AddScoped<IDepartmentRepository, EfDepartmentRepository>();
services.AddScoped<ICostCenterRepository, EfCostCenterRepository>();
services.AddScoped<IProjectRepository, EfProjectRepository>();
```

### JournalEntryLineDto Update
```csharp
public record JournalEntryLineDto(
    long Id,
    long AccountId,
    MoneyDto Debit,
    MoneyDto Credit,
    string? Description,
    long? DepartmentId,
    long? CostCenterId,
    long? ProjectId);
```

### Invariants to Enforce
1. **CompanyId > 0** — validate in entity constructor (required param)
2. **Code required, non-empty** — validate in constructor
3. **Name required, non-empty** — validate in constructor
4. **Code unique per company per dimension** — enforced via composite unique index at DB level
5. **StartDate < EndDate** (Project only) — validate if both provided

### Breaking Changes Assessment
- **JournalEntryLine constructor change** — adding optional params with defaults. Existing callers still work (backwards compatible).
- **JournalEntry.AddLine change** — adding optional params with defaults. Existing callers still work.
- **JournalEntryLineDto change** — adding params to record. No handlers map this yet. Safe to change.
- **No handlers exist for CreateJournalEntry/PostJournalEntry** — no breaking changes to application layer.
- **No controllers reference JournalEntryLine directly** — all go through MediatR.

### Files to Create (10)
1. `src/SmeAccounting.Domain/Entities/Department.cs`
2. `src/SmeAccounting.Domain/Entities/CostCenter.cs`
3. `src/SmeAccounting.Domain/Entities/Project.cs`
4. `src/SmeAccounting.Domain/Events/DepartmentCreated.cs`
5. `src/SmeAccounting.Domain/Events/CostCenterCreated.cs`
6. `src/SmeAccounting.Domain/Events/ProjectCreated.cs`
7. `src/SmeAccounting.Domain/Ports/IDepartmentRepository.cs`
8. `src/SmeAccounting.Domain/Ports/ICostCenterRepository.cs`
9. `src/SmeAccounting.Domain/Ports/IProjectRepository.cs`
10. `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs`
11. `src/SmeAccounting.Infrastructure/Persistence/Configurations/CostCenterConfiguration.cs`
12. `src/SmeAccounting.Infrastructure/Persistence/Configurations/ProjectConfiguration.cs`
13. `src/SmeAccounting.Infrastructure/Repositories/EfDepartmentRepository.cs`
14. `src/SmeAccounting.Infrastructure/Repositories/EfCostCenterRepository.cs`
15. `src/SmeAccounting.Infrastructure/Repositories/EfProjectRepository.cs`

### Files to Modify (5)
1. `src/SmeAccounting.Domain/Entities/JournalEntryLine.cs` — add DepartmentId, CostCenterId, ProjectId; update constructor
2. `src/SmeAccounting.Domain/Entities/JournalEntry.cs` — update AddLine to pass through new optional params
3. `src/SmeAccounting.Infrastructure/Persistence/Configurations/JournalEntryLineConfiguration.cs` — add 3 nullable FK columns + FK constraints + indexes
4. `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` — add 3 DbSets + ignore 3 events
5. `src/SmeAccounting.Infrastructure/DependencyInjection.cs` — register 3 repositories
6. `src/SmeAccounting.Application/DTOs/JournalEntryLineDto.cs` — add 3 optional fields

### Files NOT Modified (confirmed safe)
- Domain events (DepartmentCreated, etc.) — new files, no existing events change
- JournalEntry events — JournalEntryPosted contract unchanged
- Port interfaces (IAccountRepository, IJournalEntryRepository) — no changes needed
- Commands/Queries — no handlers exist yet, no breaking changes
- Controllers — no direct entity references, MediatR dispatch only

### Executor Checklist Summary
**New entities:** Department, CostCenter, Project (3 entities, each ~30 lines)
**New events:** DepartmentCreated, CostCenterCreated, ProjectCreated (3 events, each ~15 lines)
**New ports:** IDepartmentRepository, ICostCenterRepository, IProjectRepository (3 interfaces, each ~10 lines)
**New configs:** DepartmentConfiguration, CostCenterConfiguration, ProjectConfiguration (3 configs, each ~40 lines)
**New repos:** EfDepartmentRepository, EfCostCenterRepository, EfProjectRepository (3 repos, each ~40 lines)
**Modified:** JournalEntryLine.cs (+12 lines), JournalEntry.cs (+6 lines), JournalEntryLineConfiguration.cs (+18 lines), SmeAccountingDbContext.cs (+6 lines), DependencyInjection.cs (+3 lines), JournalEntryLineDto.cs (+3 lines)
