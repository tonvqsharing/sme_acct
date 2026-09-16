# Research Log
## Context & Prior Work

### Current Repository State
- **Branch**: `main` (single branch, no feature branches)
- **Latest commit**: `c745f6a` — "remove all code, clean slate" (Sep 16 2026 09:06)
- **Total commits**: 38 (from first commit to clean slate)
- **Untracked files**: `.opencode/`, `loop-stack/`, `skill-decision-tables.md` — not yet committed

### What Exists Now
- `.git/` — repo initialized, has history
- `.opencode/` — opencode config with agents directory, node_modules, package.json
- `loop-stack/` — loop orchestration framework with `.global/` (MEMORY.md only) and `vietnamese-acct-architecture/` loop directory
- `skill-decision-tables.md` — skill routing guide (5W1H tables for development phases, user intents, agent roles, trigger types, workflow combinations)
- `AGENTS.md` — NOT at project root (only inside `loop-stack/vietnamese-acct-architecture/`)

### What Was Removed (Clean Slate Commit)
The most recent commit deleted **374 files, 24,893 lines** of a prior .NET solution:
- `SmeAccounting.slnx` — solution file
- 12+ modular monolith domain modules (Authorization, Identity, AccountingPeriod, Audit, ChartOfAccounts, FinancialReporting, GeneralLedger, Journal, MasterData, Organization, Posting, Tax)
- `src/SmeAccounting.Api/` — ASP.NET MVC controllers, views, Program.cs
- `src/SmeAccounting.Application/` — CQRS handlers, validators, MediatR pipeline
- `src/SmeAccounting.Infrastructure/` — EF Core, PostgreSQL, Serilog, health checks, file storage
- `src/SmeAccounting.Domain/` — shared kernel (BaseEntity, ValueObject, Result)
- `src/SmeAccounting.SharedKernel/` — Result pattern, abstractions
- `tests/` — 6 test projects (Architecture, Domain, Application, Security, Web, Infrastructure)
- `deploy/` — Dockerfile, docker-compose, nginx, systemd
- `.github/workflows/ci.yml` — GitHub Actions CI
- `docs/` — architecture, database, security, deployment, testing, authorization, ADRs
- `scripts/` — backup.sh, ef-migrations.sh
- Config files: `.editorconfig`, `.gitignore`, `.dockerignore`, `Directory.Build.props/targets`, `Directory.Packages.props`, `NuGet.config`, `global.json`

### Prior Project Architecture (from git history)
The deleted code was a **modular monolith** ASP.NET application:
- **Stack**: ASP.NET Core MVC, C# 13+, EF Core 9, PostgreSQL (with multi-DBMS support via provider selector), ASP.NET Identity
- **Pattern**: Clean Architecture (Domain → Application → Infrastructure → Api), CQRS with MediatR
- **Modules**: Authorization, Identity, AccountingPeriod, Audit, ChartOfAccounts, FinancialReporting, GeneralLedger, Journal, MasterData, Organization, Posting, Tax
- **Database**: snake_case naming convention, bigint PKs, xmin concurrency tokens
- **Testing**: Architecture tests, domain unit tests, integration tests (Testcontainers), security tests, web health check tests — 34+ tests
- **Compliance**: Vietnam Circular 133 Chart of Accounts seed (98 Level-1 accounts), VAS
- **DevOps**: Docker, docker-compose, systemd, nginx, GitHub Actions CI

### Prior Loop Work (Deleted)
Several loop directories existed with research/plans/reports for:
- `auth-module-roles` — Authorization module roles implementation (G1-G4 completed)
- `auth-multi-dbms-support` — Multi-DBMS provider support (completed)
- `build-identity-auth` — Identity + Auth foundation
- `sme-accounting-foundation` — Initial project scaffold

### No Configuration Files Present
- No `.env` files
- No `Dockerfile` or `docker-compose.yml`
- No `.csproj` or `.sln` files
- No `.github/` workflows
- No CI/CD configuration
- No `opencode.json` at root

### Global Loop Stack
- `loop-stack/.global/MEMORY.md` — empty ("none yet")
- `loop-stack/.global/TOOLS.md` — does not exist (was deleted in clean slate)

### Current Loop Directory State
- `AGENTS.md` — no agents created yet
- `MEMORY.md` — empty
- `PLAN.md` — mode: build, goal defined (Vietnamese accounting architecture), no tasks yet
- `RESEARCH.md` — this file
- `STATUS.md` — IN_PROGRESS, no tasks, no results
- `TOOLS.md` — PENDING
- `agents/` — directory exists, empty

### Key Observations
1. **True greenfield** — all code deliberately removed to start fresh
2. **Git history preserved** — prior architecture decisions can be recovered from commits
3. **Loop framework ready** — vietnamese-acct-architecture loop initialized but empty
4. **Domain context preserved** — prior work established Vietnam accounting domain (Circular 133, VAS compliance)
5. **No AGENTS.md at project root** — only exists within the loop directory
## External Knowledge & Resources

### 1. Vietnamese Accounting Standards (VAS)

**Overview**: 26 VAS issued by the Ministry of Finance (MoF) between 2001-2005, based on older IAS/IFRS standards. VAS have NOT been updated since initial issuance while IFRS continues evolving.

**Key Principles**:
- **Rules-based approach** (vs IFRS principles-based): Rigid rules, standardized chart of accounts, mandatory financial statement templates
- **Historical cost principle** dominant: Assets/liabilities at acquisition cost; fair value limited (VAS 03 prohibits revaluation model for tangible fixed assets; VAS 05 allows only cost model for investment property)
- **Prescribed Chart of Accounts (COA)**: Enterprises must apply MoF-stipulated COA; any amendments to Level 1/2 accounts require MoF approval
- **Standardized financial statement format**: Balance sheet, Income statement, Cash flow statement, Notes (no separate Statement of Changes in Equity)
- **VND default accounting currency**: Foreign currency allowed only under conditions similar to IFRS functional currency concept; must translate to VND for official submissions
- **No IFRS 9 equivalent**: No standards for financial instruments recognition/measurement, derivative instruments, or expected credit loss model

**Complete List of 26 VAS** (source: KMC Vietnam):
1. VAS 01 — Framework for Preparation and Presentation of Financial Statements
2. VAS 02 — Inventories
3. VAS 03 — Tangible Fixed Assets
4. VAS 04 — Intangible Fixed Assets
5. VAS 05 — Investment Property
6. VAS 06 — Leases
7. VAS 07 — Investments in Associates
8. VAS 08 — Financial Reporting for Interests in Joint Ventures
9. VAS 10 — Effects of Changes in Foreign Exchange Rates
10. VAS 11 — Business Combinations
11. VAS 14 — Revenue and Other Income
12. VAS 15 — Construction Contracts
13. VAS 16 — Borrowing Costs
14. VAS 17 — Income Taxes
15. VAS 18 — Provisions, Contingent Liabilities and Contingent Assets
16. VAS 19 — Insurance Contracts
17. VAS 21 — Presentation of Financial Statements
18. VAS 22 — Additional Disclosures for Banking/Financial Institutions
19. VAS 23 — Events After the Balance Sheet Date
20. VAS 24 — Cash Flow Statements
21. VAS 25 — Consolidated Financial Statements
22. VAS 26 — Related Party Disclosures
23. VAS 27 — Interim Financial Reporting
24. VAS 28 — Segment Reporting
25. VAS 29 — Changes in Accounting Policies, Estimates and Errors
26. VAS 30 — Earnings per Share

**Key Differences VAS vs IFRS** (verified via KPMG, Grant Thornton, GBA Vietnam):
- VAS rules-based vs IFRS principles-based
- VAS mandates prescribed COA; IFRS does not prescribe COA format
- VAS uses historical cost; IFRS emphasizes fair value
- VAS financial statements: 4 components; IFRS: 5 components (includes Statement of Changes in Equity)
- VAS 17 only recognizes deferred tax for carry-forward losses; IFRS IAS 12 allows broader recognition
- VAS 06: Operating leases record only periodic expense; IFRS 16: Right-of-use asset + lease liability
- Multiple IFRS standards have no VAS equivalent: IAS 20 (Government Grants), IAS 41 (Agriculture), IFRS 5 (Held-for-Sale), IFRS 9 (Financial Instruments), IFRS 13 (Fair Value Measurement), IFRS 15 (Revenue), IFRS 16 (Leases)

**Vietnam IFRS Transition Roadmap** (Decision 345/QĐ-BTC, 2020):
- Phase I: Voluntary application (2022-2025)
- Phase II: Compulsory application (post-2025) — mandatory for consolidated financial statements of state-owned, listed, and large non-listed companies

**Authoritative Sources**:
- KPMG Vietnam: "Differences between Vietnamese GAAP & IFRS" (Oct 2025) — https://assets.kpmg.com/content/dam/kpmgsites/vn/pdf/2025/10/differences-between-vietnamese-gaap-ifrs.pdf
- Grant Thornton Vietnam: "Comparison between VAS and IFRS" — https://www.grantthornton.com.vn/insights/audit-and-assurance/ifrs/comparison-between-vas-and-ifrs
- KMC Vietnam: "Overview of the 26 Vietnamese Accounting Standards (VAS)" — https://kmc.vn/news/kmcs-perspectives/how-many-accounting-standards-are-there-overview-of-the-26-vietnamese-accounting-standards-vas
- GBA Vietnam: "VAS versus IFRS: Battle of the Forms" (Dec 2024) — https://gba-vietnam.org/wp-content/uploads/2024.12-NF-Comparison-between-VAS-and-IFRS.pdf
- Invest Vietnam: "Vietnamese Accounting Standards and Systems" — https://investvietnam.vn/financial-report-audit.html
- Vietnam Briefing: "VAS vs IFRS: Accounting Standard Transition" — https://www.vietnam-briefing.com/doing-business-guide/vietnam/taxation-and-accounting/accounting-standards-vas-ifrs

---

### 2. Circular 99/2025/TT-BTC — Enterprise Accounting Regime

**Issued**: October 27, 2025 by the Ministry of Finance
**Effective**: January 1, 2026 (for fiscal years beginning on or after this date)
**Replaces**: Circular 200/2014/TT-BTC (after 11+ years)

**Key Changes**:

**General Provisions**:
- Expanded scope: Covers internal management, risk control, and accounting autonomy (not just bookkeeping and financial reporting)
- Applies to all enterprises across all sectors and economic components (except credit institutions which follow SBV regulations)

**Chart of Accounts — Major Revisions**:
- Accounts eliminated: 161, 441, 611, 631
- New accounts: 215 (Biological Assets), 332 (Dividends Payable), 82112 (GMT Top-Up Tax)
- Renamed accounts: 112 now "Demand deposits"
- Enterprises may supplement accounts or amend names/codes/contents to suit their operations, provided internal regulations are in place
- Significantly impacts accounting software and ERP systems

**Accounting Vouchers and Books**:
- Enterprises can DESIGN THEIR OWN voucher forms and accounting book templates (breakthrough change)
- Must issue internal accounting regulations for any deviations from prescribed templates
- Detailed procedural requirements removed (ink color, copy number)
- Reinforces legal validity of electronic documents

**Accounting Currency**:
- More flexible rules for changing accounting currency
- Balances converted at average buying-selling transfer exchange rate from primary bank
- Financial statements in foreign currency must be translated into VND using clarified methods

**Financial Statements**:
- Four basic statements remain, but explanatory notes substantially expanded
- Enhanced classification criteria for current vs non-current items
- Expanded note disclosures: cash restrictions, biological assets, BCCs, dividends payable, issued bonds, individual items >10% of total balances
- Additional transparency for valuation bases, key assumptions, uncertainty to estimates
- New disclosures for top-up corporate income tax (global minimum tax)
- Enhanced reporting for acquisition/disposal of subsidiaries and going concern assessments

**Accounting Software Requirements** (Article 28):
Software must meet at minimum:
a) Procedures/operations must comply with accounting laws, tax laws — must not alter nature/principles/methods of accounting
c) Data must be secure; system must alert or prevent intentional interference that alters recorded information
d) Must provide complete and timely output information as required by authorities
dd) Must be capable of connecting or ready to connect with other software (e-invoice, digital signature, etc.)
e) Must be capable of being upgraded/modified to comply with changes in laws

**Implementation and Transitional Provisions**:
- Changes in accounting policies due to Circular 99 applied per transitional guidance
- Enterprises must review ERP and accounting systems, train staff, develop data transition plan (2025→2026)

**Authoritative Sources**:
- KPMG Vietnam: "Key changes in Vietnamese Accounting System for Enterprises" (Nov 2025) — https://kpmg.com/vn/en/home/insights/2025/11/key-changes-in-vietnamese-accounting-system-for-enterprises.html
- KPMG Vietnam: "Financial Reporting Alert — Circular No. 99" (Nov 2025) — https://assets.kpmg.com/content/dam/kpmgsites/vn/pdf/2025/11/circular-99-en.pdf [encrypted PDF, summary from web search]
- EY Vietnam: "Updates on Circular 99/2025/TT-BTC" — https://www.ey.com/en_vn/events/ey-vietnam-events/updates-on-circular-99-2025-tt-btc-key-changes-and-impacts-on-enterprises
- KMC Vietnam: "Circular No. 99/2025/TT-BTC — 9 Key Points" — https://kmc.vn/news/latest-news/circular-no-99-2025-tt-btc-officially-replaces-circular-no-200-2014-tt-btc-9-key-points-enterprises-must-note
- Grant Thornton Vietnam: "Circular 99 Key Changes" (Nov 2025) — https://www.grantthornton.com.vn/contentassets/14b986f2c949481eb4e3056430ebd117/decree-99---eng-version.pdf
- Vietnam Briefing: "Vietnam Circular 99: 2026 Accounting Compliance Guide" — https://www.vietnam-briefing.com/news/vietnam-circular-99-accounting-compliance-guide.html
- VN Law Firm: "Circular No. 99/2025/TT-BTC" (English translation) — https://vnlawfirm.vn/van-ban/circular-no-99-2025-tt-btc-on-corporate-accounting-guidelines
- Full text: https://static3.luatvietnam.vn/uploaded/vietlawfile/2025/11/99_2025_tt_btc_incom_071125092141.pdf

---

### 3. ASP.NET MVC Clean Architecture Patterns

**Core Principle**: Dependencies flow toward the innermost circle (Domain). All outer layers depend on inner layers, never the reverse.

**Standard Layer Structure** (from Microsoft Learn, Jason Taylor's CleanArchitecture template):
```
Domain Layer (innermost)
  └── Entities, Enums, Exceptions, Interfaces, Value Objects
      └── Pure domain logic, no infrastructure dependencies

Application Layer
  └── Business logic, Use Cases, CQRS handlers
      └── Interfaces for infrastructure (ports)
      └── Depends only on Domain

Infrastructure Layer
  └── EF Core DbContext, external services implementations
      └── Implements interfaces defined in Application

API / Presentation Layer (outermost)
  └── Controllers, Views, middleware
      └── Depends on Application layer
```

**Key Patterns**:
- **Domain-Driven Design (DDD)**: Ubiquitous Language, Entities, Value Objects, Aggregates, Domain Events
- **CQRS** (Command Query Responsibility Segregation): Separate read/write models via MediatR
- **Repository Pattern**: Generic repository interfaces in Domain/Application, implementations in Infrastructure
- **Unit of Work**: Transaction management across repositories
- **Dependency Inversion**: Domain defines interfaces; Infrastructure implements them
- **Onion/Hexagonal Architecture**: Ports (interfaces) and Adapters (implementations)

**Reference Implementations**:
- Microsoft eShopOnWeb: https://github.com/dotnet-architecture/eShopOnWeb
- Jason Taylor CleanArchitecture: https://github.com/ardalis/CleanArchitecture
- EduardoPires/EquinoxProject (6.7k stars): DDD + CQRS + Event Sourcing + .NET 9
- aspnetcorehero/Boilerplate (597 stars): Onion/Hexagonal + CQRS + MediatR

**Authoritative Sources**:
- Microsoft Learn: "Common web application architectures" — https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures
- Microsoft Learn: "DDD, Microservices" — https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/
- NDepend Blog: "Clean Architecture in ASP.NET Core" (Jul 2025) — https://blog.ndepend.com/clean-architecture-for-asp-net-core-solution
- Herberto Graca: "Explicit Architecture — DDD, Hexagonal, Onion, Clean, CQRS" — https://herbertograca.com/2017/11/16/explicit-architecture-01-ddd-hexagonal-onion-clean-cqrs-how-i-put-it-all-together
- Steve Smith (.NET Conf): "Clean Architecture with ASP.NET Core" — https://learn.microsoft.com/en-us/shows/dotnetconf-2022/clean-architecture-with-aspnet-core-7

---

### 4. Vietnamese Accounting Software Requirements

**Regulatory Framework** (verified):
- Circular 99/2025/TT-BTC Article 28: Software requirements for accounting compliance
- Decree 123/2020/ND-CP: E-invoice regulations (mandatory for all taxpayers)
- Circular 78/2021/TT-BTC: Detailed guidance on e-invoices and tax administration
- Decree 70/2025/ND-CP: Amendments to e-invoice regulations (Jun 2025)

**Chart of Accounts Structure**:
- Circular 99 (large enterprises): Revised COA with ~98 Level-1 accounts (prior Circular 200 had similar structure)
- Circular 133/2016/TT-BTC (SMEs): Simplified COA with merged accounts
- Account structure: 4-digit Level 1 (e.g., 111 = Cash), Level 2 adds digits, Level 3 further detail
- Level 1 account groups: Assets (1xx), Liabilities (3xx), Equity (4xx), Revenue (5xx), Expenses (6xx-9xx)

**Tax Reporting**:
- VAT declaration: Monthly or quarterly on Form 01/GTGT
- CIT declaration: Annual, with quarterly estimates
- Tax types: VAT (0%, 5%, 8%, 10%), CIT (20%), import tax, export tax
- Tax groups must be correctly classified (VAT vs non-VAT)

**E-Invoice Integration** (mandatory since Jul 2022):
- **Two types**: Coded (có mã — GDT authentication code, real-time clearance) and Uncoded (không có mã — issued directly, reported same-day)
- **Format**: Standardized XML from General Department of Taxation (GDT)
- **Digital signature**: Mandatory (chữ ký số) from GDT-approved provider
- **Integration paths**: Direct API to GDT, or via licensed TVAN provider (Viettel, MISA, BKAV, VNPT, FPT, M-Invoice)
- **Required fields**: Invoice name/serial/number, seller/buyer name+address+tax code (MST), goods/services description, unit price, quantity, VAT rate/amount, total, digital signature, dates
- **Language**: Vietnamese (foreign text in parentheses)
- **Archive**: 10 years retention
- **Software must connect**: Accounting software must connect to e-invoice software and digital signature software

**Authoritative Sources**:
- Decree 123/2020/ND-CP: https://thuvienphapluat.vn/van-ban/EN/Doanh-nghiep/Decree-123-2020-ND-CP-prescribes-invoices-and-records/457847/tieng-anh.aspx
- Circular 78/2021/TT-BTC: https://thuvienphapluat.vn/van-ban/EN/Thue-Phi-Le-Phi/Circular-78-2021-TT-BTC-providing-guidance-on-Law-on-Tax-Administration/492057/tieng-anh.aspx
- Decree 70/2025/ND-CP: https://static3.luatvietnam.vn/uploaded/vietlawfile/2025/4/70_2025_nd_cp_incom_020425104305.pdf
- Fonoa: "Vietnam E-invoicing Guide" — https://www.fonoa.com/resources/country-tax-guides/vietnam/e-invoicing-and-digital-reporting
- Fonoa: "Vietnam E-invoice Requirements & Challenges" — https://www.fonoa.com/resources/blog/vietnam-e-invoicing-requirements-challenges
- Acclime Vietnam: "Bookkeeping and Accounting in Vietnam" — https://vietnam.acclime.com/guides/bookkeeping-accounting-international-investors
- VATupdate: "E-Invoicing and E-Reporting in Vietnam" — https://www.vatupdate.com/2025/12/12/briefing-document-podcast-e-invoicing-and-e-reporting-in-vietnam
- Open-source reference: einvoice-api (Viettel/MISA/BKAV adapters) — https://github.com/sophie-nguyenthuthuy/einvoice-api
- Viindoo/Odoo modules: Vietnam COA (Circular 99+133), E-Invoice integration — https://viindoo.com/apps/modules/17.0/l10n_vn_viin

---

### 5. Architectural Implications of VAS/Circular 99 Compliance

**Domain Model Implications**:
1. **Prescribed COA as a domain concern**: The chart of accounts is not just configuration — it's a regulatory domain entity. Account codes, levels, and grouping must be modeled as first-class domain objects. MoF amendments require software to support dynamic COA updates.
2. **Dual reporting readiness**: System must support VAS reporting AND be architecturally ready for IFRS transition (post-2025 roadmap). Consider abstraction layer for accounting policies.
3. **Circular 99 account changes**: Software must handle account lifecycle (add, rename, deprecate accounts). Accounts like 215 (Biological Assets) and 82112 (GMT Top-Up Tax) are new — domain model must be extensible.

**Infrastructure Implications**:
1. **E-invoice integration as a port**: Define `IEInvoiceProvider` interface in Application/Domain layer with adapter implementations for TVAN providers (Viettel, MISA, BKAV). This is a classic Ports & Adapters pattern.
2. **Digital signature integration**: Separate port for `IDigitalSignatureService` — HSM/USB token handling is infrastructure concern.
3. **GDT connectivity**: E-invoice data transmission to tax authority must be a background service/port, not coupled to business logic.
4. **Data integrity**: Circular 99 requires software to "alert or preventing intentional interference that alters recorded accounting information" — implies audit trail, immutability patterns, or event sourcing considerations.

**Application Layer Implications**:
1. **CQRS for financial reporting**: Read models for balance sheet (B01-DN), P&L (B02-DN), cash flow (B03-DN) are distinct from write models for journal entries.
2. **Multi-currency accounting**: Exchange rate handling with primary bank rates — currency as a value object.
3. **Fiscal period management**: Accounting periods must be manageable (Circular 99 requires disclosure for transitional periods).

**Testing Implications**:
1. **Architecture tests**: Enforce Clean Architecture dependencies (like the prior project had with NetArchTest)
2. **COA validation tests**: Verify account structure compliance
3. **E-invoice integration tests**: Sandbox environments for TVAN providers

**Security/Compliance Implications**:
1. **Audit trail**: Immutable record of all accounting entries — consider event sourcing or append-only journal
2. **Access control**: Role-based access to accounting operations (who can post, who can approve, who can close periods)
3. **Data residency**: Vietnamese data may need to stay in-country depending on regulations
## Requirements & Constraints

### Architectural Invariants (Hard Rules)

| # | Constraint | Rationale |
|---|-----------|-----------|
| H1 | Single company only — no multi-tenant, no branches, no subsidiaries | SME scope; eliminates tenant isolation complexity, eliminates intercompany elimination in consolidation |
| H2 | Presentation → Application → Domain dependency direction enforced | Circular 99 requires auditability; clean separation enables independent testing of accounting rules |
| H3 | Domain must not reference ASP.NET MVC, EF Core, or any infrastructure NuGet package | Domain must be a pure .NET class library (netstandard2.0 or net8.0). No `Microsoft.*`, no `Npgsql`, no `Serilog` references |
| H4 | Controllers must not contain accounting posting logic, business rules, or domain calculations | Controllers only: map HTTP request → command/query, dispatch via MediatR (or equivalent), map result → HTTP response |
| H5 | Accounting posting rules must be independently testable without any HTTP/database dependency | Domain unit tests run in < 1 second, no Testcontainers, no web factory |
| H6 | Regulatory traceability: every journal entry must trace to its source document and be immutable after posting | Circular 99 Art. 28(c): "system must alert or prevent intentional interference that alters recorded information" |

### Domain Boundary Map

#### Tier 1 — Accounting Core (pure domain, zero infrastructure refs)

| Bounded Context | Key Entities | Write/Read | Regulatory |
|----------------|-------------|------------|------------|
| **Chart of Accounts** | Account, AccountGroup, AccountLevel, AccountCode | Write-heavy at setup, read-heavy after | VAS prescribed COA; Circular 99 revised COA; account lifecycle (add/rename/deprecate) |
| **General Ledger** | JournalEntry, JournalEntryLine, PostingReference | Write-heavy (every transaction) | Must be immutable after posting; audit trail required |
| **Fiscal Period** | FiscalYear, FiscalPeriod, PeriodStatus | Write-light (open/close) | Circular 99 transitional period disclosure |
| **Accounting Policy** | Policy, ValuationMethod, Currency | Write-light | VAS historical cost default; abstraction needed for IFRS transition |

#### Tier 2 — Business Modules (write-heavy, may need infrastructure ports)

| Bounded Context | Key Entities | Write/Read | Regulatory |
|----------------|-------------|------------|------------|
| **Cash** | CashTransaction, PettyCash | Write-heavy | Cash management reporting |
| **Bank** | BankAccount, BankTransaction, BankReconciliation | Write-heavy | Bank statement reconciliation |
| **Sales** | SalesInvoice, SalesOrder, Customer | Write-heavy | E-invoice mandatory; VAT reporting |
| **Purchasing** | PurchaseInvoice, PurchaseOrder, Supplier | Write-heavy | Input VAT deduction; e-invoice |
| **Inventory** | Item, StockMovement, Warehouse, Valuation | Write-heavy | VAS 02 inventory valuation (FIFO/weighted avg) |
| **Fixed Assets** | FixedAsset, DepreciationSchedule, Disposal | Write-light (depreciation runs) | VAS 03/04 — cost model only; no revaluation |
| **Payroll** | PayrollEntry, Employee, Benefit | Write-periodic | PIT reporting; social insurance |

#### Tier 3 — Integration Modules (read-heavy, mostly output)

| Bounded Context | Key Entities | Write/Read | Regulatory |
|----------------|-------------|------------|------------|
| **Tax** | TaxDeclaration, VATReturn, CITReturn | Read-heavy (computation) + write (filing) | Monthly/quarterly VAT; annual CIT |
| **E-Invoice** | EInvoice, EInvoiceRequest, EInvoiceResponse | Write-heavy (generation) + read (status) | Decree 123/2020; mandatory XML format; digital signature |
| **Reporting** | FinancialStatement, ReportTemplate | Read-only | VAS standardized formats (B01-DN, B02-DN, B03-DN) |
| **Costing** | CostCenter, CostAllocation | Write-light | Management accounting, not regulatory |
| **Budget** | BudgetEntry, BudgetControl | Write-light | Internal control only |

### Architectural Seam Definitions

#### Hexagonal/Onion Boundary

```
┌─────────────────────────────────────────────────────────┐
│  Presentation (Api)                                     │
│  - Controllers (thin: HTTP → MediatR dispatch)          │
│  - ViewModels / DTOs                                    │
│  - Filters, Middleware                                  │
│  DEPENDS ON: Application layer                          │
├─────────────────────────────────────────────────────────┤
│  Application (Use Cases)                                │
│  - Command/Query handlers (MediatR)                     │
│  - Validators (FluentValidation)                        │
│  - Port interfaces (IAccountRepository, IUnitOfWork)    │
│  - DTOs for cross-module data transfer                  │
│  DEPENDS ON: Domain layer ONLY                          │
├─────────────────────────────────────────────────────────┤
│  Domain (Core)                                          │
│  - Entities (Account, JournalEntry, etc.)               │
│  - Value Objects (Money, AccountCode, Currency)         │
│  - Domain Events (JournalEntryPosted, PeriodClosed)     │
│  - Domain Exceptions (InvalidPostingRule, etc.)         │
│  - Aggregate Roots with invariants                      │
│  - Port interfaces (IForeignExchangeRateProvider)       │
│  DEPENDS ON: nothing (pure .NET)                        │
├─────────────────────────────────────────────────────────┤
│  Infrastructure (Adapters)                              │
│  - EF Core DbContext + Repositories                     │
│  - External service adapters (E-invoice, Digital Sig)   │
│  - File storage, email, reporting exports                │
│  DEPENDS ON: Application (implements its ports)         │
└─────────────────────────────────────────────────────────┘
```

#### Interface Contracts Domain Must Define

| Interface | Purpose | Implemented By |
|-----------|---------|----------------|
| `IAccountRepository` | COA persistence | Infrastructure (EF Core) |
| `IJournalEntryRepository` | GL entry persistence | Infrastructure (EF Core) |
| `IUnitOfWork` | Transaction boundary | Infrastructure (EF Core) |
| `IForeignExchangeRateProvider` | Bank exchange rates | Infrastructure (external API/bank) |
| `IAuditLogger` | Immutable audit trail | Infrastructure (append-only store) |
| `IClock` | Deterministic time (testing) | Infrastructure (system clock) |

#### Controller Responsibilities (Thin Controllers)

```
POST /api/journal-entries
  1. Validate HTTP input (model state)
  2. Map to CreateJournalEntryCommand
  3. Send via MediatR → handler executes
  4. Map result to HTTP 201/400
  0 business logic, 0 domain references
```

#### Cross-Module Accounting Posting Seam

The critical architectural question: **where does accounting posting happen?**

```
Business Module (e.g., Sales)          Accounting Core
─────────────────────────             ─────────────────
SalesInvoiceCreated                   IPostingService.Post(entry)
  → Domain Event                        → validates balance
  → Handler invokes IPostingService     → enforces rules
                                        → persists via IJournalEntryRepository
                                        → raises JournalEntryPosted event
```

**Decision**: Accounting posting is a **domain service** within Accounting Core. Business modules raise domain events; Accounting Core handles posting rules. This ensures:
- Sales module knows nothing about debit/credit rules
- Posting rules are independently testable
- Regulatory traceability: every posting links to source event

### Testing Structure Implications

#### Test Project Layout

```
tests/
├── SmeAccounting.Domain.Tests/           ← Unit tests, zero dependencies
│   ├── AccountTests.cs
│   ├── JournalEntryTests.cs
│   ├── PostingRuleTests.cs
│   └── ValueObjectTests.cs
│
├── SmeAccounting.Application.Tests/      ← Unit tests with mocked ports
│   ├── Handlers/
│   ├── Validators/
│   └── PostingServiceTests.cs
│
├── SmeAccounting.ArchitectureTests/     ← NetArchTest.Rules
│   ├── DependencyRulesTests.cs          ← Domain has no infrastructure refs
│   ├── LayerCouplingTests.cs            ← Controllers → Application only
│   └── NamingConventionsTests.cs
│
├── SmeAccounting.Infrastructure.Tests/  ← Integration, Testcontainers
│   ├── Repositories/
│   └── EInvoiceAdapterTests.cs
│
└── SmeAccounting.Api.Tests/             ← HTTP/integration
    ├── HealthChecks/
    └── ControllerSmokeTests.cs
```

#### Architecture Constraint Tests (Must-Have)

| Test | Enforces | Failure = |
|------|----------|-----------|
| Domain has no reference to Infrastructure assemblies | H3 | Compilation error or NetArchTest violation |
| Domain has no reference to ASP.NET MVC assemblies | H3 | Compilation error or NetArchTest violation |
| Controllers do not reference Domain.Entities | H4 | Architectural violation |
| Controllers do not reference Domain.Repositories | H4 | Architectural violation |
| Application layer has no reference to Infrastructure | H2 | Architectural violation |
| All Accounting Posting tests pass without HTTP/DB | H5 | Business rule leak to infrastructure |

#### Unit Test Characteristics for Domain

- **No mocking framework needed** for pure domain logic
- **Value objects** test equality, hashing, validation rules
- **Entities** test invariant enforcement (e.g., journal entry must balance)
- **Domain services** test posting rules (e.g., debit = credit validation)
- **Target**: < 1 second total execution, no I/O

### Data Model Considerations

#### Single-Company Simplifications

- No `CompanyId` / `TenantId` columns anywhere
- No row-level security
- No intercompany elimination logic
- Fiscal year is global (single company = single fiscal calendar)

#### Core Data Model Sketch (for architecture planning)

```
ChartOfAccounts
  Account (id, code, name, level, parent_id, account_type, is_active)
  AccountGroup (id, code, name, account_type)

GeneralLedger
  FiscalYear (id, year, status)
  FiscalPeriod (id, year_id, month, status, opened_at, closed_at)
  JournalEntry (id, entry_number, date, period_id, description, source_type, source_id, posted_by, posted_at)
  JournalEntryLine (id, entry_id, account_id, debit, credit, currency, exchange_rate, description)

Shared
  AuditLog (id, entity_type, entity_id, action, old_value, new_value, user_id, timestamp)
  ExchangeRate (id, currency, rate, date, source)
```

#### Key Domain Rules (must be in Domain, not Controller/Application)

1. **Journal entry must balance**: `Σ(debit) == Σ(credit)` — enforced by `JournalEntry` aggregate
2. **Period must be open**: Posting rejects if fiscal period is closed — enforced by `PostingService`
3. **Account must be leaf node**: Only leaf accounts accept postings — enforced by `Account` entity
4. **Immutability after posting**: Posted entries cannot be modified, only reversed — enforced by `JournalEntry` state
5. **Source traceability**: Every entry links to `source_type` + `source_id` (e.g., "SalesInvoice" + 12345)

### Regulatory Constraints Summary

| Regulation | Impact on Architecture | Where Enforced |
|-----------|----------------------|----------------|
| VAS 01 (Framework) | Standardized COA structure, VND currency | Domain (Account entity) |
| VAS 02 (Inventories) | FIFO/weighted avg valuation | Domain (Inventory module) |
| VAS 03 (Tangible Fixed Assets) | Cost model only, no revaluation | Domain (FixedAsset module) |
| Circular 99 Art. 28 | Software must connect to e-invoice/digital sig | Infrastructure (ports) |
| Circular 99 Art. 28(c) | Prevent intentional interference with records | Domain (immutability) + Infrastructure (audit log) |
| Decree 123/2020 | E-invoice XML format, digital signature | Infrastructure (EInvoice adapter) |
| Tax declarations | VAT/CIT computation from GL data | Application (reporting handlers) |
## Task-Specific Research — Solution Structure and Domain Layer

### 1. .NET 10 Project Structure

**Target framework**: `net10.0` for all projects (classlib and webapi).

**Solution structure** (from verified templates: MinimDev, SatyaKarki, eShopOnWeb):

```
SmeAccounting.sln
├── src/
│   ├── SmeAccounting.Domain/            # Class library, net10.0
│   │   ├── Common/                      # BaseEntity, ValueObject base classes
│   │   ├── Entities/                    # Domain entities
│   │   ├── Enums/                       # Domain enumerations
│   │   ├── Events/                      # Domain events (plain records)
│   │   ├── Exceptions/                  # Domain exceptions
│   │   ├── ValueObjects/                # Value objects (Money, AccountCode, etc.)
│   │   └── Ports/                       # Port interfaces (repositories, services)
│   ├── SmeAccounting.Application/       # Class library, refs Domain only
│   ├── SmeAccounting.Infrastructure/    # Class library, refs Application + Domain
│   └── SmeAccounting.Api/              # Web app (ASP.NET MVC), refs Application only
├── tests/
│   └── SmeAccounting.ArchitectureTests/ # xUnit + NetArchTest.Rules
├── Directory.Build.props
├── Directory.Build.targets
└── .editorconfig
```

**Dependency direction** (enforced by csproj ProjectReference):
```
Api → Application → Domain ← Infrastructure → Application
```
Api must NOT reference Infrastructure or Domain directly.

### 2. Directory.Build.props Settings

```xml
<Project>
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <LangVersion>13</LangVersion>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <AnalysisLevel>latest-recommended</AnalysisLevel>
  </PropertyGroup>
</Project>
```

**Notes**:
- `LangVersion=13` is C# 13 (shipped with .NET 10 SDK 10.0.401)
- `TreatWarningsAsErrors` ensures clean builds
- Central Package Management (CPM) optional — use `Directory.Packages.props` if desired, but per-project PackageReference is simpler for initial scaffold

### 3. BaseEntity Design

**Source**: Jason Taylor CleanArchitecture template, SatyaKarki template, NDepend patterns.

```csharp
namespace SmeAccounting.Domain.Common;

public abstract class BaseEntity
{
    public Guid Id { get; set; }
    
    private readonly List<IDomainEvent> _domainEvents = [];
    public IReadOnlyCollection<IDomainEvent> DomainEvents => _domainEvents.AsReadOnly();

    public void AddDomainEvent(IDomainEvent domainEvent) => _domainEvents.Add(domainEvent);
    public void RemoveDomainEvent(IDomainEvent domainEvent) => _domainEvents.Remove(domainEvent);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
```

**Alternative** (simpler, no domain events in base — events in separate collection):

Per the PLAN.md entity definitions, entities use `long` (bigint) PKs for PostgreSQL, not `Guid`. Adjust:

```csharp
namespace SmeAccounting.Domain.Common;

public abstract class BaseEntity
{
    public long Id { get; set; }
}
```

**Decision**: Use `long Id` — matches PostgreSQL bigint PK pattern from prior project. Domain events as records in Domain layer, no MediatR dependency.

### 4. Namespace Convention

**Pattern**: `SmeAccounting.{Layer}.{Feature}`

| Layer | Root Namespace |
|-------|---------------|
| Domain | `SmeAccounting.Domain` |
| Domain/Entities | `SmeAccounting.Domain.Entities` |
| Domain/ValueObjects | `SmeAccounting.Domain.ValueObjects` |
| Domain/Enums | `SmeAccounting.Domain.Enums` |
| Domain/Events | `SmeAccounting.Domain.Events` |
| Domain/Exceptions | `SmeAccounting.Domain.Exceptions` |
| Domain/Ports | `SmeAccounting.Domain.Ports` |
| Domain/Common | `SmeAccounting.Domain.Common` |
| Application | `SmeAccounting.Application` |
| Infrastructure | `SmeAccounting.Infrastructure` |
| Api | `SmeAccounting.Api` |

### 5. EF Core Version

**EF Core**: `Microsoft.EntityFrameworkCore` **10.0.0** (LTS, supported until Nov 2028)
**Npgsql provider**: `Npgsql.EntityFrameworkCore.PostgreSQL` **10.0.3** (latest stable)
**Targets**: net10.0 only

Package references for Infrastructure:
```xml
<PackageReference Include="Microsoft.EntityFrameworkCore" Version="10.0.0" />
<PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" Version="10.0.3" />
```

EF Core 10 requires .NET 10 SDK and runtime. No backward compat with .NET 9 or earlier.

### 6. MediatR Version

**MediatR**: `MediatR` **14.2.0** (latest stable, targets .NETStandard 2.0 — compatible with net10.0)
**DI extensions**: Included in MediatR 14.x package (uses `Microsoft.Extensions.DependencyInjection.Abstractions`)

Application layer:
```xml
<PackageReference Include="MediatR" Version="14.2.0" />
```

Domain layer: **Zero NuGet refs** — domain events are plain records, no MediatR dependency.

### 7. FluentValidation Version

**FluentValidation**: `FluentValidation` **12.1.0** (supports .NET 8+, including .NET 10)
**DI extensions**: `FluentValidation.DependencyInjectionExtensions` **12.1.0**

⚠️ Note: `FluentValidation.AspNetCore` is **deprecated** in v12. Use `FluentValidation.DependencyInjectionExtensions` + `builder.Services.AddValidatorsFromAssemblyContaining<T>()` instead.

Application layer:
```xml
<PackageReference Include="FluentValidation" Version="12.1.0" />
<PackageReference Include="FluentValidation.DependencyInjectionExtensions" Version="12.1.0" />
```

### 8. Solution Structure — Enforcing Dependency Direction

**Enforcement mechanisms**:

1. **csproj ProjectReference** — Api refs only Application; Application refs only Domain; Infrastructure refs Application + Domain
2. **Architecture tests** (G4) — NetArchTest.Rules enforces at build time:
   - Domain has no reference to Application, Infrastructure, Api
   - Application has no reference to Infrastructure or Api
   - Api has no reference to Infrastructure
3. **Directory.Build.props** — shared settings don't add cross-layer references
4. **Port interfaces in Domain** — Domain defines `IAccountRepository`, `IJournalEntryRepository`, `IUnitOfWork`, etc.; Infrastructure implements them

**Critical rule**: Api → Application only. Never Api → Domain or Api → Infrastructure.

### 9. Entity Definitions (from PLAN.md)

All entities inherit `BaseEntity` (which provides `long Id`):

| Entity | Key Fields | Aggregate Root? | Notes |
|--------|-----------|-----------------|-------|
| `Account` | code, name, level, parent_id, account_type, is_active | Yes | COA hierarchy, 4-digit Level 1 |
| `AccountGroup` | code, name, account_type | No | Grouping within COA |
| `JournalEntry` | entry_number, date, period_id, description, source_type, source_id, posted_by, posted_at | Yes | Immutable after posting |
| `JournalEntryLine` | entry_id, account_id, debit, credit, currency, exchange_rate, description | No | Must balance: Σdebit == Σcredit |
| `FiscalYear` | year, status | No | Global (single company) |
| `FiscalPeriod` | year_id, month, status, opened_at, closed_at | No | Open/Closing/Closed lifecycle |
| `PostingReference` | journal_entry_id, source_type, source_id | No | Source traceability |

### 10. Value Objects — Equality Implementation

**Recommended approach**: C# `record` types for automatic value equality.

```csharp
namespace SmeAccounting.Domain.ValueObjects;

public record Money(decimal Amount, string Currency);
public record AccountCode(string Value);
public record Currency(string Code, string Name, bool IsDefault);
```

Records automatically implement:
- `IEquatable<T>` with value equality
- `Equals(object?)` override
- `GetHashCode()` override
- `==` and `!=` operators

**If records cannot be used** (e.g., EF Core owned types issues), use the classic ValueObject base class pattern:

```csharp
public abstract class ValueObject
{
    protected abstract IEnumerable<object> GetEqualityComponents();

    public override bool Equals(object? obj)
    {
        if (obj is null || obj.GetType() != GetType()) return false;
        var other = (ValueObject)obj;
        return GetEqualityComponents().SequenceEqual(other.GetEqualityComponents());
    }

    public override int GetHashCode()
    {
        var hash = new HashCode();
        foreach (var component in GetEqualityComponents())
            hash.Add(component);
        return hash.ToHashCode();
    }

    public static bool operator ==(ValueObject left, ValueObject right) => EqualOperator(left, right);
    public static bool operator !=(ValueObject left, ValueObject right) => !EqualOperator(left, right);

    private static bool EqualOperator(ValueObject left, ValueObject right)
    {
        if (left is null ^ right is null) return false;
        return left?.Equals(right!) != false;
    }
}
```

**Enums** (not value objects, but domain types):
```csharp
public enum AccountType { Asset, Liability, Equity, Revenue, Expense }
public enum PeriodStatus { Open, Closing, Closed }
```

### 11. Port Interfaces (Domain Layer)

All port interfaces live in `SmeAccounting.Domain.Ports`:

```csharp
namespace SmeAccounting.Domain.Ports;

public interface IAccountRepository
{
    Task<Account?> GetByIdAsync(long id);
    Task<Account?> GetByCodeAsync(string code);
    Task<IReadOnlyList<Account>> GetAllAsync();
    Task AddAsync(Account account);
    Task UpdateAsync(Account account);
}

public interface IJournalEntryRepository
{
    Task<JournalEntry?> GetByIdAsync(long id);
    Task AddAsync(JournalEntry entry);
}

public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}

public interface IForeignExchangeRateProvider
{
    Task<Money> GetRateAsync(string fromCurrency, string toCurrency, DateTimeOffset date);
}

public interface IAuditLogger
{
    Task LogAsync(string entityType, long entityId, string action, string? oldValues, string? newValues, string userId);
}

public interface IClock
{
    DateTimeOffset UtcNow { get; }
}

public interface IPostingService
{
    Task<JournalEntry> PostAsync(JournalEntry entry);
}
```

**Key design points**:
- `IClock` enables deterministic testing (mock clock returns fixed time)
- `IAuditLogger` is a port — infrastructure implements with append-only storage
- `IPostingService` is a domain service interface — orchestration lives in Domain, not Application
- No infrastructure NuGet packages in Domain csproj
- All interfaces return domain entities, not DTOs

### 12. Domain Events (Plain Records)

```csharp
namespace SmeAccounting.Domain.Events;

public interface IDomainEvent
{
    DateTimeOffset OccurredOn { get; }
}

public record JournalEntryPosted(long EntryId, DateTimeOffset OccurredOn) : IDomainEvent;
public record PeriodClosed(long PeriodId, DateTimeOffset OccurredOn) : IDomainEvent;
public record AccountCreated(long AccountId, DateTimeOffset OccurredOn) : IDomainEvent;
public record AccountDeprecated(long AccountId, DateTimeOffset OccurredOn) : IDomainEvent;
```

No MediatR dependency. Domain events are raised by entities and collected by BaseEntity's `_domainEvents` list. Infrastructure or Application layer dispatches them.

### 13. Domain Exceptions

```csharp
namespace SmeAccounting.Domain.Exceptions;

public class InvalidPostingRuleException : Exception
{
    public InvalidPostingRuleException(string message) : base(message) { }
}

public class PeriodClosedException : Exception
{
    public PeriodClosedException(long periodId)
        : base($"Period {periodId} is closed and cannot accept new postings.") { }
}

public class AccountNotLeafException : Exception
{
    public AccountNotLeafException(long accountId)
        : base($"Account {accountId} has child accounts and cannot accept postings.") { }
}
```

### 14. Test Project Structure

```
tests/SmeAccounting.ArchitectureTests/
├── SmeAccounting.ArchitectureTests.csproj  # xUnit + NetArchTest.Rules
└── ArchitectureTests/
    ├── DependencyRulesTests.cs
    ├── LayerCouplingTests.cs
    └── NamingConventionsTests.cs
```

**Package references for architecture tests**:
```xml
<PackageReference Include="xunit" Version="2.*" />
<PackageReference Include="xunit.runner.visualstudio" Version="2.*" />
<PackageReference Include="NetArchTest.Rules" Version="1.*" />
<PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.*" />
```

### 15. Summary — NuGet Package Matrix

| Package | Version | Project |
|---------|---------|---------|
| Microsoft.EntityFrameworkCore | 10.0.0 | Infrastructure |
| Npgsql.EntityFrameworkCore.PostgreSQL | 10.0.3 | Infrastructure |
| MediatR | 14.2.0 | Application |
| FluentValidation | 12.1.0 | Application |
| FluentValidation.DependencyInjectionExtensions | 12.1.0 | Application |
| NetArchTest.Rules | 1.* | ArchitectureTests |
| xunit | 2.* | ArchitectureTests |

**Domain project**: Zero NuGet references — only `<FrameworkReference Include="Microsoft.AspNetCore.App" />` is NOT needed; just `net10.0` target framework with implicit SDK references.

---

*Research completed: Sep 16 2026. Sources: Microsoft Learn, NuGet.org, GitHub templates (MinimDev, SatyaKarki, amantinband, Jason Taylor), Npgsql docs, FluentValidation docs, MediatR NuGet page.*

---

## Task-Specific Research — Regulatory Documentation Structure

### 1. Complete List of 26 VAS Standards (Verified)

All 26 Vietnamese Accounting Standards (VAS) issued by the Ministry of Finance (2001-2005), based on older IAS/IFRS:

| # | Standard | Title | IAS/IFRS Equivalent | Applicability to SME Accounting Software |
|---|----------|-------|---------------------|------------------------------------------|
| 1 | VAS 01 | Framework for Preparation and Presentation of Financial Statements | IAS 1 | **Core** — prescribes COA structure, VND currency, financial statement format |
| 2 | VAS 02 | Inventories | IAS 2 | **Core** — FIFO/weighted avg valuation (Account 156) |
| 3 | VAS 03 | Tangible Fixed Assets | IAS 16 | **Core** — cost model only, no revaluation (Accounts 153, 21x) |
| 4 | VAS 04 | Intangible Fixed Assets | IAS 38 | **Core** — recognition/amortization (Accounts 154, 24x) |
| 5 | VAS 05 | Investment Property | IAS 40 | Low — SMEs rarely have investment property |
| 6 | VAS 06 | Leases | IAS 17 (not IFRS 16) | **Core** — operating lease only, periodic expense recording |
| 7 | VAS 07 | Investments in Associates | IAS 28 | Low — equity method for associates |
| 8 | VAS 08 | Financial Reporting for Interests in Joint Ventures | IAS 31 | Low — BCC/joint venture reporting |
| 9 | VAS 10 | Effects of Changes in Foreign Exchange Rates | IAS 21 | **Core** — multi-currency, exchange differences (Accounts 413, 811/711) |
| 10 | VAS 11 | Business Combinations | IFRS 3 | Low — M&A accounting |
| 11 | VAS 14 | Revenue and Other Income | IAS 18 | **Core** — revenue recognition (Accounts 511, 515, 711) |
| 12 | VAS 15 | Construction Contracts | IAS 11 | Medium — percentage-of-completion for construction |
| 13 | VAS 16 | Borrowing Costs | IAS 23 | Medium — capitalization of borrowing costs |
| 14 | VAS 17 | Income Taxes | IAS 12 | **Core** — deferred tax, CIT (Accounts 333, 82112 GMT) |
| 15 | VAS 18 | Provisions, Contingent Liabilities and Contingent Assets | IAS 37 | **Core** — provisions (Account 351) |
| 16 | VAS 19 | Insurance Contracts | IFRS 4 | Low — insurance-specific |
| 17 | VAS 21 | Presentation of Financial Statements | IAS 1 (revised) | **Core** — Balance Sheet (B01-DN), P&L (B02-DN), Cash Flow (B03-DN), Notes |
| 18 | VAS 22 | Additional Disclosures for Banking/Financial Institutions | IAS 30 | N/A — credit institutions excluded from Circular 99 scope |
| 19 | VAS 23 | Events After the Balance Sheet Date | IAS 10 | Medium — adjusting/non-adjusting events |
| 20 | VAS 24 | Cash Flow Statements | IAS 7 | **Core** — B03-DN cash flow statement |
| 21 | VAS 25 | Consolidated Financial Statements | IAS 27 | Low — single-company scope, no consolidation |
| 22 | VAS 26 | Related Party Disclosures | IAS 24 | Medium — related party note disclosures |
| 23 | VAS 27 | Interim Financial Reporting | IAS 34 | Low — optional interim reports |
| 24 | VAS 28 | Segment Reporting | IAS 14 | Low — optional segment reporting |
| 25 | VAS 29 | Changes in Accounting Policies, Estimates and Errors | IAS 8 | **Core** — transitional guidance for Circular 99 adoption |
| 26 | VAS 30 | Earnings per Share | IAS 33 | Low — SMEs rarely issue shares |

**Key**: "Core" = directly impacts accounting software domain model or reporting. "Low" = not applicable to single-company SME scope. "Medium" = may apply depending on business type.

### 2. Circular 99/2025/TT-BTC — Article-by-Article Structure

**Issued**: October 27, 2025 | **Effective**: January 1, 2026 | **Replaces**: Circular 200/2014/TT-BTC

| Chapter | Article | Title | Content Summary | Architecture Impact |
|---------|---------|-------|-----------------|---------------------|
| **I — General** | Art. 1 | Scope of regulation | Guidance on accounting documents, accounts, books, financial statements | Defines what software must cover |
| | Art. 2 | Subjects of application | All enterprises except credit institutions (SBV-governed) | Single-company scope confirmed |
| | Art. 3 | Corporate governance and internal control | Internal governance regulations; roles/responsibilities | Audit trail, access control design |
| | Art. 4 | Accounting currency | VND default; foreign currency criteria; changing currency | `Currency` value object, exchange rate handling |
| | Art. 5-7 | Accounting principles | Accrual basis, going concern, consistency, prudence | Domain service validation rules |
| **II — Accounting Documents** | Art. 8 | General provisions | Prepared per Law on Accounting | Document entity design |
| | Art. 9 | Standard forms | Enterprise may design own forms; Appendix I templates | Flexible voucher template system |
| | Art. 10 | Preparation and signing | Chief accountant signs; no signing "on behalf of" executives | Authorization controls |
| **III — Accounts** | Art. 11 | Chart of accounts | Appendix II COA; enterprises may supplement/modify | `Account` entity extensibility; COA seed data |
| | Art. 22 | Account application | Apply Appendix II COA to record transactions | Default COA loading |
| | Art. 25 | Account modification | Add/modify names, codes, structure with internal policy | Account lifecycle management |
| | Art. 26 | Unaddressed transactions | Follow Law on Accounting, VAS, and Circular principles | Fallback handling |
| **IV — Accounting Books** | Art. 12 | Accounting books | Entries recorded promptly, clearly, completely | Journal entry entity design |
| | Art. 27-28 | Book templates | Appendix III templates; enterprises may customize | Flexible book template system |
| **V — Financial Statements** | Art. 29 | General provisions | Four statements: Balance Sheet (now "Statement of Financial Position"), Income Statement, Cash Flow, Notes | Report generation handlers |
| | Art. 30 | Statement of Financial Position | Renamed from Balance Sheet; enhanced classification | B01-DN report model |
| | Art. 31-35 | Other statements | Income Statement, Cash Flow, Notes to Financial Statements | B02-DN, B03-DN report models |
| | Art. 36 | Transitional provisions | Circular 200 provisions preserved for specific cases | Migration/transitional handling |
| **VI — Implementation** | Art. 28* | Use of accounting software | Software requirements (a), (c), (d), (dd), (e) | **Critical** — architecture enforcement points |
| | Art. 37-38 | Implementation | Enterprise executive/chief accountant responsibility | User role design |

*Note: Article 28 appears in multiple sources under different chapter numbering. The software requirements article is consistently cited as Art. 28 across KPMG, VN Law Firm, and VietAnLaw sources.*

### 3. Article 28 — Accounting Software Requirements (Detailed Mapping)

Article 28 of Circular 99 defines minimum requirements for accounting software. Each requirement maps to specific architecture layers:

| Art. 28 | Requirement Text | Architecture Layer | Enforcement Point | Implementation |
|---------|-----------------|-------------------|-------------------|----------------|
| **(a)** | Procedures/operations must comply with accounting laws, tax laws — must not alter nature/principles/methods of accounting | **Domain** | Posting rules, validation | `PostingService` enforces debit=credit, period-open rules; `Account` entity enforces COA structure |
| **(c)** | Data must be secure; system must alert or prevent intentional interference that alters recorded information | **Domain + Infrastructure** | Immutability, audit trail | `JournalEntry.IsPosted` flag; `IAuditLogger` append-only; EF Core concurrency (`xmin`) |
| **(d)** | Must provide complete and timely output information as required by authorities | **Application** | Report generation | `IAccountingReportService` generates B01-DN, B02-DN, B03-DN; query handlers for balance sheet/income statement |
| **(dd)** | Must be capable of connecting or ready to connect with other software (e-invoice, digital signature, etc.) | **Infrastructure** | Port/adapter interfaces | `IEInvoiceProvider`, `IDigitalSignatureService` port interfaces; adapter stubs for TVAN providers |
| **(e)** | Must be capable of being upgraded/modified to comply with changes in laws | **All layers** | Extensibility design | Modular architecture; COA extensibility (add/modify accounts); `Account` entity supports lifecycle (add/deprecate) |

**Additional Art. 28 requirements** (from VietAnLaw source, Art. 29 in some numbering):
- Processing must ensure accuracy, consistency, no duplication
- When making corrections, traces of recorded accounting contents must be kept in chronological order
- Chief accountant/accounting manager responsible for accuracy and truthfulness

### 4. Chart of Accounts Structure Under Circular 99

**Source**: Circular 99 Appendix II, RSM Vietnam comparison, Grant Thornton presentation

#### 9 Main Account Categories (Reorganized by Nature)

| Category | Account Range | Vietnamese Name | Description | Key Changes from Circular 200 |
|----------|--------------|-----------------|-------------|-------------------------------|
| **1 — Assets** | 1xx | Tài sản | Current + non-current assets | Accounts 161 eliminated; 215 (Biological Assets) added |
| **2 — Liabilities** | 2xx, 3xx (partial) | Nợ obligations | Short-term + long-term liabilities | Account 332 (Dividends Payable) added |
| **3 — Owner's Equity** | 4xx | Vốn chủ sở hữu | Equity, retained earnings, reserves | Account 441 eliminated |
| **4 — Revenue** | 5xx | Doanh thu | Revenue and income | Account 137 (Accrued Revenue) added |
| **5 — Cost of Goods Sold** | 6xx | Giá vốn hàng bán | Cost of goods/services sold | Account 611 eliminated |
| **6 — Expenses** | 8xx | Chi phí hoạt động kinh doanh | Operating expenses | Accounts 711/811 merged into Other Income/Expenses |
| **7 — Other Income** | 7xx | Thu nhập khác | Non-operating income | Merged from old separate accounts |
| **8 — Other Expenses** | 821xx-841xx | Chi phí khác | Non-operating expenses | Account 82112 (GMT Top-Up Tax) added |
| **9 — Off-Balance Sheet** | 9xx | Outside balance sheet | Contingent items | Unchanged |

#### Account Code Hierarchy

```
Level 1: 4 digits (e.g., 111 = Cash)
  └── Level 2: +1 digit (e.g., 1111 = Cash on hand VND)
       └── Level 3: +1 digit (e.g., 11111 = Petty cash)
            └── Level 4: +1 digit (enterprise-specific, optional)
```

#### Key Account Codes (Circular 99)

| Code | Name (English) | Name (Vietnamese) | Category | Notes |
|------|---------------|-------------------|----------|-------|
| 111 | Cash | Tiền mặt | Assets | |
| 112 | Demand deposits | Tiền gửi không kỳ hạn | Assets | **Renamed** from old name |
| 113 | Short-term deposits | Tiền gửi có kỳ hạn ngắn hạn | Assets | |
| 131 | Accounts receivable | Phải thu của khách hàng | Assets | |
| 133 | VAT deductible | Thuế GTGT được khấu trừ | Assets | |
| 137 | Accrued revenue | Doanh thu cần phân bổ | Assets | **New** in Circular 99 |
| 153 | Tangible fixed assets | Tài sản cố định hữu hình | Assets | VAS 03 — cost model only |
| 154 | Intangible fixed assets | Tài sản cố định vô hình | Assets | VAS 04 |
| 156 | Inventories | Hàng tồn kho | Assets | VAS 02 — FIFO/weighted avg |
| 211 | Short-term borrowings | Vay ngắn hạn | Liabilities | |
| 215 | Biological assets | Tài sản sinh học | Liabilities | **New** in Circular 99 |
| 246 | Long-term prepaid expenses | Chi phí trả trước dài hạn | Liabilities | **New** in Circular 99 |
| 331 | Accounts payable | Phải trả người bán | Liabilities | |
| 332 | Dividends payable | Cổ tức phải trả | Liabilities | **New** in Circular 99 |
| 333 | CIT payable | Thuế TNDN phải nộp | Liabilities | |
| 351 | Provision for obligations | Dự phòng nghĩa vụ phải trả | Liabilities | **New** in Circular 99 |
| 411 | Charter capital | Vốn đầu tư của chủ sở hữu | Equity | |
| 413 | Foreign exchange differences | Chênh lệch tỷ giá | Equity | VAS 10 |
| 511 | Revenue from sales | Doanh thu bán hàng | Revenue | |
| 515 | Revenue from services | Doanh thu cung cấp dịch vụ | Revenue | |
| 611 | ~~Periodic inventory cost~~ | ~~Chi phí hàng tồn kho theo kỳ~~ | — | **Eliminated** in Circular 99 |
| 711 | Other income | Thu nhập khác | Other Income | Merged |
| 811 | Other expenses | Chi phí khác | Other Expenses | Merged |
| 82112 | GMT Top-Up Tax | Thuế TNDN bổ sung (GMT) | Other Expenses | **New** in Circular 99 |

#### COA Extensibility Rules (Art. 25)

1. Enterprises may add accounts not in Appendix II
2. Enterprises may modify names, codes, structure, content of existing accounts
3. Must issue internal accounting policy documenting changes
4. Policy must state necessity and legal responsibility
5. If no changes, apply Appendix II as-is

**Software implication**: `Account` entity must support:
- Dynamic account creation (not hardcoded COA)
- Account deprecation (not deletion — for audit trail)
- Account code validation (4-digit Level 1 pattern)
- Parent-child hierarchy (Level 1 → Level 2 → Level 3)

### 5. E-Invoice Requirements Under Decree 123/2020

**Effective**: July 1, 2022 (mandatory nationwide) | **Amended by**: Decree 70/2025/ND-CP (June 1, 2025)

#### Two Types of E-Invoices

| Type | Vietnamese | Description | Tax Authority Code | Data Transmission |
|------|-----------|-------------|-------------------|-------------------|
| **With code** | Có mã | Real-time clearance by GDT before issuance | Required — GDT issues authentication code | Real-time via GDT portal or TVAN provider |
| **Without code** | Không có mã | Issued directly, reported same-day | Not required | Data transmitted to GDT no later than issuance day |

#### E-Invoice XML Format Structure (Decree 123 Art. 12)

The legally binding format is **XML** (not PDF). PDF is convenience-only.

```
Hóa đơn điện tử (E-Invoice XML)
├── Transaction Data (Thông tin nghiệp vụ)
│   ├── Seller Information (Thông tin người bán)
│   │   ├── Name, Address, Tax Code (MST)
│   │   ├── Bank account info
│   │   └── Digital signature
│   ├── Buyer Information (Thông tin người mua)
│   │   ├── Name, Address, Tax Code (MST)
│   │   └── Representative
│   ├── Invoice Header
│   │   ├── Invoice series (Ký hiệu)
│   │   ├── Invoice number (Số hóa đơn)
│   │   ├── Invoice date (Ngày lập)
│   │   └── Invoice type (Loại hóa đơn)
│   ├── Invoice Lines (Chi tiết hàng hóa/dịch vụ)
│   │   ├── Item name/description
│   │   ├── Unit, Quantity
│   │   ├── Unit price
│   │   ├── Amount (before VAT)
│   │   ├── VAT rate (%)
│   │   ├── VAT amount
│   │   └── Total amount
│   ├── Summary
│   │   ├── Total before VAT
│   │   ├── Total VAT
│   │   ├── Total after VAT
│   │   └── Amount in words (số tiền bằng chữ)
│   └── Additional fields (contract ref, delivery order, etc.)
├── Digital Signature (Chữ ký số)
│   └── GDT-approved certificate (USB token or cloud HSM)
└── Tax Authority Code (Mã cơ quan thuế) — if applicable
    └── Real-time authentication code from GDT
```

#### Key Technical Requirements

| Requirement | Detail | Architecture Impact |
|-------------|--------|---------------------|
| **Format** | Standardized XML per GDT specification | `IEInvoiceProvider` interface returns XML; TVAN adapter generates XML |
| **Digital signature** | Mandatory (except POS cash registers); GDT-approved certificate | `IDigitalSignatureService` port interface; adapter for HSM/USB token |
| **Language** | Vietnamese (foreign text in parentheses) | Localization support in invoice generation |
| **Retention** | 10 years in original XML form with digital signature | `EInvoice` entity with `XmlContent`, `DigitalSignature`, `IssuedAt` fields |
| **Archive** | Original electronic form (XML + signature); in-house or outsourced | File storage port interface; blob storage or file system |
| **Data transmission** | XML via secure web services to GDT or TVAN provider | `IEInvoiceProvider.SubmitAsync(EInvoiceRequest)` returns `EInvoiceResponse` |
| **Error handling** | Invalid format: VND 4-8M fine; missing invoice: VND 5-10M fine | Validation before submission; retry logic |

#### TVAN Provider Integration (Ports & Adapters)

```
IEInvoiceProvider (Domain/Application port)
├── ViettelEInvoiceAdapter (Infrastructure)
├── MisaEInvoiceAdapter (Infrastructure)
├── BkavEInvoiceAdapter (Infrastructure)
├── VnptEInvoiceAdapter (Infrastructure)
├── FptEInvoiceAdapter (Infrastructure)
└── MInvoiceAdapter (Infrastructure)
```

**Registration**: Enterprises register via GDT e-portal (Form 01/DKTD-HDDT) or through TVAN providers.

#### Decree 70/2025 Updates

- Expanded scope to overseas suppliers without PE in Vietnam (voluntary e-invoice registration)
- Stricter retail/POS rules
- Real-time data transmission and regulatory reporting for consumer-facing businesses
- Integrated e-invoice + e-receipt format allowed for single-transaction payments

### 6. ADR Format Specification

**Standard**: Michael Nygard's ADR format (simplified, widely adopted)

**Template** (for `docs/architecture/ADR-NNN-title.md`):

```markdown
# ADR-NNN: {Title}

## Status
Proposed | Accepted | Deprecated | Superseded by [ADR-XXX]

## Date
YYYY-MM-DD

## Context
What is the issue that we're seeing that is motivating this decision or change?
What forces are at play (technical, political, social, project)?

## Decision
What is the change that we're proposing and/or doing?
State the decision clearly and concisely.

## Consequences
What becomes easier or more difficult to do because of this change?
List positive and negative consequences.

### Positive
- ...

### Negative
- ...

## Notes
Optional: links to related ADRs, references, supporting docs.
```

**File naming**: `docs/architecture/ADR-001-clean-architecture.md`

**ADR-001** (Clean Architecture): Status, Context (dependency chaos from prior project), Decision (4-layer Clean Architecture), Consequences (testability vs coupling)
**ADR-002** (CQRS/MediatR): Status, Context (read/write separation needed), Decision (MediatR CQRS), Consequences (handler complexity vs scalability)
**ADR-003** (Posting Seam): Status, Context (where accounting posting happens), Decision (domain service in Accounting Core), Consequences (sales module ignorance vs orchestration complexity)

### 7. Regulatory-to-Code-to-Test Traceability

**Design**: A three-way traceability matrix linking regulations → architecture components → tests.

#### Traceability Matrix Structure

```
Regulation ──────────→ Architecture Component ──────────→ Test
   │                         │                              │
   │ VAS 01 (COA structure)  │ Account entity (Domain)      │ AccountTests.cs
   │ Circular 99 Art. 28(c)  │ JournalEntry immutability    │ PostingRuleTests.cs
   │ Decree 123 Art. 12      │ IEInvoiceProvider (Infra)    │ EInvoiceAdapterTests.cs
```

#### Implementation Pattern

Each documentation file (`VAS-compliance.md`, `Circular99-mapping.md`) should include a traceability table:

```markdown
| Regulation | Article/Section | Architecture Component | Layer | Test | Status |
|-----------|-----------------|----------------------|-------|------|--------|
| VAS 01 | Para 22 | Account entity | Domain | AccountTests | ✅ Planned |
| Circular 99 | Art. 28(c) | JournalEntry.IsPosted | Domain | PostingRuleTests | ✅ Planned |
| Circular 99 | Art. 28(dd) | IEInvoiceProvider | Infrastructure | EInvoiceAdapterTests | ⏳ Stub |
| Decree 123 | Art. 12 | EInvoice XML generation | Infrastructure | EInvoiceAdapterTests | ⏳ Stub |
```

#### Traceability Enforcement

1. **Architecture tests** (G4) verify that regulatory-mandated components exist in correct layers
2. **Domain tests** verify business rules match regulatory requirements
3. **Integration tests** verify port interfaces are implemented (even as stubs)
4. **Documentation** links each regulation to its implementation and verification

**Example traceability chain**:
```
Circular 99 Art. 28(c) — "prevent intentional interference"
  → Domain: JournalEntry.IsPosted = true after posting
  → Domain: JournalEntry cannot be modified after IsPosted
  → Infrastructure: IAuditLogger.Append() — append-only log
  → Test: PostingRuleTests.PostedEntryCannotBeModified()
  → Test: AuditTests.AuditLogIsAppendOnly()
```

### 8. IFRS Transition Roadmap (Decision 345/QĐ-BTC)

**Decision 345/QĐ-BTC (2020)**: Phased IFRS adoption

| Phase | Period | Scope | Action |
|-------|--------|-------|--------|
| Phase I | 2022-2025 | Voluntary | Listed companies and large enterprises may voluntarily apply IFRS |
| Phase II | Post-2025 | Compulsory (consolidated) | Mandatory for consolidated financial statements of SOEs, listed, and large non-listed companies |

**Architecture implication**: The accounting engine needs an abstraction layer for accounting policies (VAS vs IFRS). The domain model should not be locked to VAS-only measurement rules.

**Abstraction design**:
- `IAccountingPolicy` interface — defines measurement rules (historical cost vs fair value)
- `VasAccountingPolicy` implementation — current default
- `IfrsAccountingPolicy` implementation — future, under IFRS transition
- Revenue recognition: VAS 14 (point of transfer) → IFRS 15 (five-step model)
- Leases: VAS 06 (operating lease expense) → IFRS 16 (ROU asset + lease liability)

### 9. Key TVAN Providers (E-Invoice Integration)

| Provider | Market Share | API Style | Notes |
|----------|-------------|-----------|-------|
| **Viettel** | ~40% market | REST API | Largest telecom; integrated e-invoice platform |
| **MISA** | ~25% market | REST API | Accounting software + e-invoice bundle |
| **BKAV** | ~10% market | REST API | Digital signature + e-invoice |
| **VNPT** | ~10% market | REST API | State telecom |
| **FPT** | ~8% market | REST API | Tech conglomerate |
| **M-Invoice** | ~5% market | REST API | Specialized e-invoice provider |

**Open-source reference**: https://github.com/sophie-nguyenthuthuy/einvoice-api (Viettel/MISA/BKAV adapters)

### 10. Summary — Documentation Deliverables for [G1]

| File | Path | Content | Key Sections |
|------|------|---------|-------------|
| **VAS-compliance.md** | `docs/regulatory/VAS-compliance.md` | 26 VAS → domain module mapping | Table of all 26 VAS with applicability; traceability matrix |
| **Circular99-mapping.md** | `docs/regulatory/Circular99-mapping.md` | Art. 28(a),(c),(d),(dd),(e) → architecture layers | Article-by-article mapping; implementation enforcement points |
| **ChartOfAccounts-structure.md** | `docs/regulatory/ChartOfAccounts-structure.md` | Account hierarchy, 9 categories, key codes | Level 1-3 structure; extensibility rules; Circular 99 changes |
| **EInvoice-integration.md** | `docs/regulatory/EInvoice-integration.md` | Decree 123 requirements, port interfaces, TVAN adapters | XML format; IEInvoiceProvider contract; TVAN adapter pattern |
| **IFRS-transition-roadmap.md** | `docs/regulatory/IFRS-transition-roadmap.md` | Decision 345 phases, abstraction layer | IAccountingPolicy interface; phased migration design |
| **ADR-001-clean-architecture.md** | `docs/architecture/ADR-001-clean-architecture.md` | Clean Architecture decision | Status, Context, Decision, Consequences |
| **ADR-002-cqrs-mediatr.md** | `docs/architecture/ADR-002-cqrs-mediatr.md` | CQRS/MediatR pattern choice | Status, Context, Decision, Consequences |
| **ADR-003-posting-seam.md** | `docs/architecture/ADR-003-posting-seam.md` | Where accounting posting happens | Status, Context, Decision, Consequences |

### 11. Authoritative Sources for This Task

| Source | URL | Relevance |
|--------|-----|-----------|
| KPMG Vietnam — Circular 99 Alert | https://kpmg.com/vn/en/home/insights/2025/11/key-changes-in-vietnamese-accounting-system-for-enterprises.html | COA changes, Art. 28 |
| KPMG — Financial Reporting Alert (PDF) | https://assets.kpmg.com/content/dam/kpmgsites/vn/pdf/2025/11/circular-99-en.pdf | Detailed changes summary |
| Grant Thornton — Circular 99 Presentation | https://www.grantthornton.com.vn/contentassets/14b986f2c949481eb4e3056430ebd117/decree-99---eng-version.pdf | COA changes, accounting policies |
| RSM Vietnam — Circular 200 vs 99 | https://www.rsm.global/vietnam/sites/default/files/media/audit-news/2025/11/RSM_VN_Assurance_Update_Key_differences_between_Circular_200_and_Circular_99_en.pdf | Detailed comparison |
| VN Law Firm — Circular 99 English | https://vnlawfirm.vn/van-ban/circular-no-99-2025-tt-btc-on-corporate-accounting-guidelines | Full text Art. 28 |
| Decree 123/2020 (English) | https://thuvienphapluat.vn/van-ban/EN/Doanh-nghiep/Decree-123-2020-ND-CP-prescribes-invoices-and-records/457847/tieng-anh.aspx | E-invoice format Art. 12 |
| Decree 70/2025 (PDF) | https://static3.luatvietnam.vn/uploaded/vietlawfile/2025/4/70_2025_nd_cp_incom_020425104305.pdf | E-invoice amendments |
| VATupdate — E-Invoicing Briefing | https://www.vatupdate.com/2025/12/12/briefing-document-podcast-e-invoicing-and-e-reporting-in-vietnam | XML format, retention |
| Fonoa — Vietnam E-Invoicing Guide | https://www.fonoa.com/resources/country-tax-guides/vietnam/e-invoicing-and-digital-reporting | Integration paths |
| MADR Template | https://github.com/adr/madr | ADR format standard |
| Michael Nygard ADR Template | https://github.com/architecture-decision-record/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md | ADR format |

---

*Research completed: Sep 16 2026. Sources: KPMG Vietnam, Grant Thornton Vietnam, RSM Vietnam, VN Law Firm, Thuvienphapluat, VATupdate, Fonoa, Edicom, MADR project, architecture-decision-record project.*

---

## Task-Specific Research — Application and Infrastructure Layers

### 1. MediatR Patterns for Commands/Queries

**Package**: MediatR 14.2.0 (already referenced in Application.csproj)

**Command Pattern** (write side):
- Commands are C# `record` types implementing `IRequest<TResult>`
- Return a result type (ID, DTO, or `Unit` for void-like operations)
- Named as imperative verbs: `CreateAccountCommand`, `PostJournalEntryCommand`
- Carries only input data needed for the write operation
- One handler per command: `IRequestHandler<TCommand, TResult>`

```csharp
// Command definition
public record CreateAccountCommand(
    string Code, string Name, AccountType AccountType, int Level = 1, long? ParentId = null)
    : IRequest<long>;  // returns created Account.Id

// Handler
public class CreateAccountCommandHandler : IRequestHandler<CreateAccountCommand, long>
{
    private readonly IAccountRepository _repository;
    private readonly IUnitOfWork _unitOfWork;

    public CreateAccountCommandHandler(IAccountRepository repository, IUnitOfWork unitOfWork)
    {
        _repository = repository;
        _unitOfWork = unitOfWork;
    }

    public async Task<long> Handle(CreateAccountCommand request, CancellationToken ct)
    {
        var code = new AccountCode(request.Code);
        var account = new Account(code, request.Name, request.AccountType, request.Level, request.ParentId);
        await _repository.AddAsync(account, ct);
        await _unitOfWork.SaveChangesAsync(ct);
        return account.Id;
    }
}
```

**Query Pattern** (read side):
- Queries are C# `record` types implementing `IRequest<TResult>`
- Return DTOs (not domain entities)
- Query handlers use `AsNoTracking()` for performance — skip EF Core change detection
- Query handlers may inject `DbContext` directly (not via repository) for LINQ projections
- Repositories add value on write side (aggregate boundaries); queries benefit from direct DbContext access for projections

```csharp
// Query definition
public record GetAccountQuery(long Id) : IRequest<AccountDto?>;

// Handler — queries can use DbContext directly for projections
public class GetAccountQueryHandler : IRequestHandler<GetAccountQuery, AccountDto?>
{
    private readonly SmeAccountingDbContext _context;

    public GetAccountQueryHandler(SmeAccountingDbContext context) => _context = context;

    public async Task<AccountDto?> Handle(GetAccountQuery request, CancellationToken ct)
    {
        return await _context.Accounts
            .AsNoTracking()
            .Where(a => a.Id == request.Id)
            .Select(a => new AccountDto(a.Id, a.Code.Value, a.Name, a.AccountType.ToString(), a.Level, a.IsActive))
            .FirstOrDefaultAsync(ct);
    }
}
```

**MediatR Registration** (in Application layer DI extension):
```csharp
services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssembly(typeof(DependencyInjection).Assembly);
    cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
});
```

**Key conventions**:
- Use `ISender` (not `IMediator`) in handlers/endpoints when only Send is needed
- Use `IMediator` when also publishing domain events as MediatR notifications
- Commands/queries organized by feature folder: `Features/Accounts/Commands/CreateAccount/`
- CancellationToken propagated from controller → MediatR → handler → EF Core

**Source**: NippySoft CQRS article, csharp-coder.com guide, codingdroplets template, codewithmukesh.com guide, ADR-002 already accepted.

---

### 2. FluentValidation Patterns

**Package**: FluentValidation 12.1.0 + FluentValidation.DependencyInjectionExtensions 12.1.0 (already referenced)

**Validator Pattern**:
- Validators inherit `AbstractValidator<T>` where T is the command/query
- One validator per command (not per entity)
- Validators live in Application layer alongside commands
- Fluent API: `RuleFor(x => x.Property).NotEmpty().MaximumLength(200)`

```csharp
public class CreateAccountCommandValidator : AbstractValidator<CreateAccountCommand>
{
    public CreateAccountCommandValidator()
    {
        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Account code is required.")
            .Matches(@"^\d{4,}$").WithMessage("Account code must be numeric, at least 4 digits.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Account name is required.")
            .MaximumLength(200).WithMessage("Account name cannot exceed 200 characters.");

        RuleFor(x => x.AccountType)
            .IsInEnum().WithMessage("Invalid account type.");
    }
}
```

**ValidationBehavior Pipeline** (MediatR pipeline behavior):
- Intercepts every command/query before handler execution
- Runs all registered `IValidator<TRequest>` instances in parallel via `Task.WhenAll`
- Throws `ValidationException` on failure — handler never executes
- Registered via `cfg.AddOpenBehavior(typeof(ValidationBehavior<,>))`

```csharp
public class ValidationBehavior<TRequest, TResponse>(
    IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        if (!validators.Any())
            return await next(cancellationToken);

        var context = new ValidationContext<TRequest>(request);
        var results = await Task.WhenAll(
            validators.Select(v => v.ValidateAsync(context, cancellationToken)));
        var failures = results
            .SelectMany(r => r.Errors)
            .Where(f => f is not null)
            .ToList();

        if (failures.Count != 0)
            throw new ValidationException(failures);

        return await next(cancellationToken);
    }
}
```

**DI Registration**:
```csharp
services.AddValidatorsFromAssembly(typeof(DependencyInjection).Assembly);
```

**Key conventions**:
- Validators for input shape/format checks (not business rules)
- Business rules (uniqueness, period-open) belong in handlers/domain
- Async validators (`MustAsync`) for DB checks — but prefer handler for complex business rules
- `ValidationException` type should be defined in Application layer

**Source**: FluentValidation official docs, NippySoft FluentValidation article, Learnixo article, SEMastery article.

---

### 3. DTO Mapping Patterns

**Approach**: Manual mapping with C# records (no AutoMapper for this project)

**Rationale**: AutoMapper adds runtime reflection overhead, configuration complexity, and obscures mapping logic. With C# records and primary constructors, manual mapping is concise and type-safe.

**DTO Definition** (Application layer, plain records):
```csharp
public record AccountDto(long Id, string Code, string Name, string AccountType, int Level, bool IsActive);
public record MoneyDto(decimal Amount, string Currency);
public record JournalEntryDto(long Id, string EntryNumber, DateTimeOffset Date, long PeriodId, string? Description, bool IsPosted, DateTimeOffset? PostedAt);
public record JournalEntryLineDto(long Id, long AccountId, MoneyDto Debit, MoneyDto Credit, string? Description);
public record FiscalPeriodDto(long Id, long YearId, int Month, string Status, DateTimeOffset? OpenedAt, DateTimeOffset? ClosedAt);
public record BalanceSheetDto(/* fields per B01-DN */);
public record IncomeStatementDto(/* fields per B02-DN */);
```

**Entity → DTO Mapping** (in query handlers via LINQ Select):
```csharp
.Select(a => new AccountDto(a.Id, a.Code.Value, a.Name, a.AccountType.ToString(), a.Level, a.IsActive))
```

**DTO → Entity Mapping** (in command handlers via constructor):
```csharp
var code = new AccountCode(request.Code);
var account = new Account(code, request.Name, request.AccountType, request.Level, request.ParentId);
```

**Key conventions**:
- DTOs are in `SmeAccounting.Application.DTOs` namespace
- DTOs have no domain entity references (no navigation properties)
- Money value objects map to `MoneyDto(decimal Amount, string Currency)`
- Enums map to strings via `.ToString()` in DTOs (not raw enum values)
- DTOs are records for value equality and immutability
- No shared kernel DTOs — each layer defines its own shapes

**Source**: NippySoft CQRS article (DTOs as records), codingdroplets template (ProductDto pattern), csharp-coder.com guide.

---

### 4. EF Core Configuration Patterns

**Package**: Microsoft.EntityFrameworkCore 10.0.4, Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3 (already in Infrastructure.csproj)

**DbContext Setup**:
```csharp
public class SmeAccountingDbContext : DbContext
{
    public DbSet<Account> Accounts => Set<Account>();
    public DbSet<AccountGroup> AccountGroups => Set<AccountGroup>();
    public DbSet<JournalEntry> JournalEntries => Set<JournalEntry>();
    public DbSet<JournalEntryLine> JournalEntryLines => Set<JournalEntryLine>();
    public DbSet<FiscalYear> FiscalYears => Set<FiscalYear>();
    public DbSet<FiscalPeriod> FiscalPeriods => Set<FiscalPeriod>();
    public DbSet<PostingReference> PostingReferences => Set<PostingReference>();

    public SmeAccountingDbContext(DbContextOptions<SmeAccountingDbContext> options)
        : base(options) { }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(SmeAccountingDbContext).Assembly);
        base.OnModelCreating(modelBuilder);
    }
}
```

**Entity Configuration** (one per entity, `IEntityTypeConfiguration<T>`):
```csharp
internal sealed class AccountConfiguration : IEntityTypeConfiguration<Account>
{
    public void Configure(EntityTypeBuilder<Account> builder)
    {
        builder.ToTable("accounts");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.Level)
            .HasColumnName("level");

        builder.Property(e => e.ParentId)
            .HasColumnName("parent_id");

        builder.Property(e => e.AccountType)
            .HasColumnName("account_type")
            .HasConversion<string>();

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        // Value object: AccountCode as owned type
        builder.OwnsOne(e => e.Code, codeBuilder =>
        {
            codeBuilder.Property(c => c.Value)
                .HasColumnName("code")
                .IsRequired()
                .HasMaxLength(20);
        });

        // Self-referencing hierarchy
        builder.HasOne<Account>()
            .WithMany(a => a.Children)
            .HasForeignKey(e => e.ParentId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(e => e.ParentId);
    }
}
```

**Snake-case naming convention** (PostgreSQL):
```csharp
// In AddDbContext registration:
options.UseNpgsql(connectionString)
    .UseSnakeCaseNamingConvention();  // Requires EFCore.NamingConventions package
```

**Note**: The Infrastructure.csproj does NOT currently reference `EFCore.NamingConventions`. Either add it or configure snake-case manually in each `IEntityTypeConfiguration`. Since we already have `UseSnakeCaseNamingConvention` as a common pattern, recommend adding the package.

**Value Objects as Owned Types**:
- `Money` → `OwnsOne(e => e.Debit)` with `HasColumnName("debit_amount")`, `HasColumnName("debit_currency")`
- `AccountCode` → `OwnsOne(e => e.Code)` with `HasColumnName("code")`
- PostgreSQL: owned type columns are prefixed by default; use explicit `HasColumnName` to control

**Concurrency Tokens** (xmin for PostgreSQL):
```csharp
builder.Property<uint>("xmin")
    .IsRowVersion()
    .HasColumnName("xmin");
```

**Private Parameterless Constructors**: All entities already have `private Entity() { }` — EF Core uses these for materialization. No explicit configuration needed.

**Query Filters** (for soft delete):
```csharp
// In AccountConfiguration:
builder.HasQueryFilter(e => e.IsActive);
```

**Source**: ronnythedev EF Core configuration skill, OpenBaseNETPostgres template, shadykhblog tutorial, LucasBonato template, PostgreSQL best practices skill.

---

### 5. Repository Implementation Patterns

**Pattern**: Repositories implement Domain port interfaces. Write-side repositories only track changes — `SaveChangesAsync` is called by `IUnitOfWork` in the handler, NOT inside the repository.

**EfAccountRepository**:
```csharp
public class EfAccountRepository : IAccountRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfAccountRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Account?> GetByIdAsync(long id, CancellationToken ct = default)
    {
        return await _context.Accounts
            .Include(a => a.Children)
            .FirstOrDefaultAsync(a => a.Id == id, ct);
    }

    public async Task<IReadOnlyList<Account>> GetAllAsync(CancellationToken ct = default)
    {
        return await _context.Accounts
            .AsNoTracking()
            .OrderBy(a => a.Code.Value)
            .ToListAsync(ct);
    }

    public async Task AddAsync(Account account, CancellationToken ct = default)
    {
        await _context.Accounts.AddAsync(account, ct);
        // NO SaveChangesAsync —UnitOfWork handles commit
    }

    public async Task UpdateAsync(Account account, CancellationToken ct = default)
    {
        _context.Accounts.Update(account);
        // NO SaveChangesAsync —UnitOfWork handles commit
    }
}
```

**EfJournalEntryRepository**:
```csharp
public class EfJournalEntryRepository : IJournalEntryRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfJournalEntryRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<JournalEntry?> GetByIdAsync(long id, CancellationToken ct = default)
    {
        return await _context.JournalEntries
            .Include(e => e.Lines)
            .FirstOrDefaultAsync(e => e.Id == id, ct);
    }

    public async Task<IReadOnlyList<JournalEntry>> GetAllAsync(CancellationToken ct = default)
    {
        return await _context.JournalEntries
            .AsNoTracking()
            .OrderByDescending(e => e.Date)
            .ToListAsync(ct);
    }

    public async Task AddAsync(JournalEntry entry, CancellationToken ct = default)
    {
        await _context.JournalEntries.AddAsync(entry, ct);
    }
}
```

**Key rules**:
- Repositories NEVER call `SaveChangesAsync` —UnitOfWork owns the commit
- Read methods use `AsNoTracking()` for performance
- Write methods use `Add`/`Update`/`Remove` on DbContext (tracked)
- Include navigation properties only when needed (aggregate loading)
- CancellationToken propagated through all async methods

**Source**: Milan Jovanović Unit of Work article, Woodruff UoW article, Rodrigo Bercocano article, codingdroplets template.

---

### 6. Unit of Work Implementation

**Approach**: `SmeAccountingDbContext` implements `IUnitOfWork` directly — no separate class needed.

```csharp
// In SmeAccountingDbContext:
public class SmeAccountingDbContext : DbContext, IUnitOfWork
{
    // ... DbSets and configuration ...

    public async Task<int> SaveChangesAsync(CancellationToken ct = default)
    {
        return await base.SaveChangesAsync(ct);
    }
}
```

**Registration** (factory method ensuring same scoped instance):
```csharp
services.AddDbContext<SmeAccountingDbContext>(options =>
    options.UseNpgsql(connectionString)
        .UseSnakeCaseNamingConvention());

services.AddScoped<IUnitOfWork>(sp =>
    sp.GetRequiredService<SmeAccountingDbContext>());
```

**Critical**: Both `SmeAccountingDbContext` and `IUnitOfWork` resolve to the SAME scoped instance. Repositories and UoW share the same change tracker.

**Usage in handler**:
```csharp
public async Task<long> Handle(CreateAccountCommand request, CancellationToken ct)
{
    var code = new AccountCode(request.Code);
    var account = new Account(code, request.Name, request.AccountType);
    await _repository.AddAsync(account, ct);
    await _unitOfWork.SaveChangesAsync(ct);  // ONE commit for all tracked changes
    return account.Id;
}
```

**When NOT to use explicit UoW**: If handlers use `DbContext` directly (common in query handlers), the DbContext itself is already the UoW. Only expose `IUnitOfWork` for write-side handlers that use repositories.

**Source**: Milan Jovanović UoW article, Milan Jovanović Transactions article, StackLesson UoW article.

---

### 7. External Adapter Stubs

**Pattern**: Port interfaces defined in Domain layer; stub implementations in Infrastructure throw `NotImplementedException` (architecture placeholder per PLAN.md).

**BankExchangeRateProvider**:
```csharp
public class BankExchangeRateProvider : IForeignExchangeRateProvider
{
    public Task<Money> ConvertAsync(Money amount, string targetCurrency, DateTimeOffset date)
    {
        // Stub: return mock rate for development
        if (amount.Currency == targetCurrency)
            return Task.FromResult(amount);

        // TODO: Integrate with real bank exchange rate API
        var mockRate = amount.Currency == "VND" && targetCurrency == "USD" ? 25000m : 1m;
        var converted = amount.Amount / mockRate;
        return Task.FromResult(new Money(converted, targetCurrency));
    }
}
```

**EInvoiceProviderAdapter**:
```csharp
public class EInvoiceProviderAdapter : IEInvoiceProvider
{
    // IEInvoiceProvider is an Application-layer port (defined in Application, not Domain)
    // per EInvoice-integration.md: IEInvoiceProvider.SubmitAsync(EInvoiceRequest) → EInvoiceResponse
    public Task<object> SubmitAsync(object request, CancellationToken ct = default)
    {
        throw new NotImplementedException("E-invoice TVAN provider integration — architecture placeholder.");
    }
}
```

**Note**: `IEInvoiceProvider` needs to be defined. Per PLAN.md it belongs in Application layer (as a port), not Domain. Create it in `SmeAccounting.Application.Ports` or `SmeAccounting.Application.Common.Interfaces`.

**DigitalSignatureAdapter**:
```csharp
public class DigitalSignatureAdapter : IDigitalSignatureService
{
    public Task<byte[]> SignAsync(byte[] data, CancellationToken ct = default)
    {
        throw new NotImplementedException("Digital signature HSM/USB token integration — architecture placeholder.");
    }
}
```

**AuditLogger**:
```csharp
public class AuditLogger : IAuditLogger
{
    public async Task LogAsync(string action, string entity, long entityId, string details)
    {
        // Stub: console logging for development
        Console.WriteLine($"[AUDIT] {action} on {entity}:{entityId} — {details}");
        // TODO: Append-only audit log storage
        await Task.CompletedTask;
    }
}
```

**SystemClock**:
```csharp
public class SystemClock : IClock
{
    public DateTimeOffset Now => DateTimeOffset.UtcNow;
}
```

**Key conventions**:
- External adapters throw `NotImplementedException` (stub per PLAN.md acceptance criteria)
- `BankExchangeRateProvider` returns mock data (functional stub, not exception stub)
- `AuditLogger` and `SystemClock` are simple implementations (not stubs)
- All adapters implement Domain/Application port interfaces
- Adapters live in `SmeAccounting.Infrastructure/Adapters/` or `SmeAccounting.Infrastructure/Services/`

**Source**: codingdroplets template (ProductRepository NotImplementedException pattern), Stripe Systems article (adapter pattern), ardalis/CleanArchitecture (infrastructure adapters).

---

### 8. DI Registration Patterns

**Application Layer** (`DependencyInjection.cs`):
```csharp
namespace SmeAccounting.Application;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssembly(typeof(DependencyInjection).Assembly);
            cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
        });

        services.AddValidatorsFromAssembly(typeof(DependencyInjection).Assembly);

        return services;
    }
}
```

**Infrastructure Layer** (`DependencyInjection.cs`):
```csharp
namespace SmeAccounting.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        var connectionString = configuration.GetConnectionString("DefaultConnection")
            ?? throw new InvalidOperationException("Connection string 'DefaultConnection' not found.");

        services.AddDbContext<SmeAccountingDbContext>(options =>
            options.UseNpgsql(connectionString)
                .UseSnakeCaseNamingConvention());

        // Unit of Work — same scoped instance as DbContext
        services.AddScoped<IUnitOfWork>(sp =>
            sp.GetRequiredService<SmeAccountingDbContext>());

        // Repositories
        services.AddScoped<IAccountRepository, EfAccountRepository>();
        services.AddScoped<IJournalEntryRepository, EfJournalEntryRepository>();

        // External adapters
        services.AddSingleton<IClock, SystemClock>();
        services.AddScoped<IAuditLogger, AuditLogger>();
        services.AddScoped<IForeignExchangeRateProvider, BankExchangeRateProvider>();

        // TODO: Register when IEInvoiceProvider is defined
        // services.AddScoped<IEInvoiceProvider, EInvoiceProviderAdapter>();

        return services;
    }
}
```

**API Layer** (`Program.cs`):
```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddApplication()
    .AddInfrastructure(builder.Configuration);

var app = builder.Build();

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();
app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();
```

**Key conventions**:
- Each layer exposes one `Add{Layer}()` extension method on `IServiceCollection`
- Application registers MediatR, FluentValidation, pipeline behaviors
- Infrastructure registers DbContext, repositories, adapters
- API composes: `AddApplication().AddInfrastructure(config)`
- `IClock` as Singleton (no state), everything else Scoped
- Repositories registered as `I{Repository}` → `Ef{Repository}` (scoped)
- `IUnitOfWork` resolved via factory to same DbContext instance

**Source**: Milan Jovanović dependency rule article, Luong Hong Thuan Clean Architecture article, ekolsoft article, codingdroplets template.

---

### 9. File/Folder Structure for Application and Infrastructure

**Application Layer**:
```
src/SmeAccounting.Application/
├── SmeAccounting.Application.csproj
├── Common/
│   ├── Behaviors/
│   │   └── ValidationBehavior.cs
│   └── Exceptions/
│       └── ValidationException.cs
├── DTOs/
│   ├── AccountDto.cs
│   ├── JournalEntryDto.cs
│   ├── JournalEntryLineDto.cs
│   ├── FiscalPeriodDto.cs
│   ├── FiscalYearDto.cs
│   ├── MoneyDto.cs
│   ├── BalanceSheetDto.cs
│   └── IncomeStatementDto.cs
├── Features/
│   ├── Accounts/
│   │   ├── Commands/
│   │   │   ├── CreateAccount/
│   │   │   │   ├── CreateAccountCommand.cs
│   │   │   │   ├── CreateAccountCommandHandler.cs
│   │   │   │   └── CreateAccountCommandValidator.cs
│   │   │   └── DeprecateAccount/
│   │   │       ├── DeprecateAccountCommand.cs
│   │   │       ├── DeprecateAccountCommandHandler.cs
│   │   │       └── DeprecateAccountCommandValidator.cs
│   │   └── Queries/
│   │       ├── GetAccount/
│   │       │   ├── GetAccountQuery.cs
│   │       │   └── GetAccountQueryHandler.cs
│   │       └── GetAccountsByGroup/
│   │           ├── GetAccountsByGroupQuery.cs
│   │           └── GetAccountsByGroupQueryHandler.cs
│   ├── JournalEntries/
│   │   ├── Commands/
│   │   │   ├── CreateJournalEntry/
│   │   │   │   ├── CreateJournalEntryCommand.cs
│   │   │   │   ├── CreateJournalEntryCommandHandler.cs
│   │   │   │   └── CreateJournalEntryCommandValidator.cs
│   │   │   └── PostJournalEntry/
│   │   │       ├── PostJournalEntryCommand.cs
│   │   │       ├── PostJournalEntryCommandHandler.cs
│   │   │       └── PostJournalEntryCommandValidator.cs
│   │   └── Queries/
│   │       ├── GetJournalEntry/
│   │       │   ├── GetJournalEntryQuery.cs
│   │       │   └── GetJournalEntryQueryHandler.cs
│   │       └── GetBalanceSheet/
│   │           ├── GetBalanceSheetQuery.cs
│   │           └── GetBalanceSheetQueryHandler.cs
│   └── FiscalPeriods/
│       ├── Commands/
│       │   ├── OpenFiscalPeriod/
│       │   │   ├── OpenFiscalPeriodCommand.cs
│       │   │   ├── OpenFiscalPeriodCommandHandler.cs
│       │   │   └── OpenFiscalPeriodCommandValidator.cs
│       │   └── CloseFiscalPeriod/
│       │       ├── CloseFiscalPeriodCommand.cs
│       │       ├── CloseFiscalPeriodCommandHandler.cs
│       │       └── CloseFiscalPeriodCommandValidator.cs
│       └── Queries/
│           └── GetFiscalPeriods/
│               ├── GetFiscalPeriodsQuery.cs
│               └── GetFiscalPeriodsQueryHandler.cs
├── DependencyInjection.cs
└── Ports/
    └── IAccountingReportService.cs
```

**Infrastructure Layer**:
```
src/SmeAccounting.Infrastructure/
├── SmeAccounting.Infrastructure.csproj
├── Adapters/
│   ├── BankExchangeRateProvider.cs
│   ├── EInvoiceProviderAdapter.cs
│   └── DigitalSignatureAdapter.cs
├── DependencyInjection.cs
├── Persistence/
│   ├── SmeAccountingDbContext.cs
│   ├── Configurations/
│   │   ├── AccountConfiguration.cs
│   │   ├── AccountGroupConfiguration.cs
│   │   ├── JournalEntryConfiguration.cs
│   │   ├── JournalEntryLineConfiguration.cs
│   │   ├── FiscalYearConfiguration.cs
│   │   ├── FiscalPeriodConfiguration.cs
│   │   └── PostingReferenceConfiguration.cs
│   └── Repositories/
│       ├── EfAccountRepository.cs
│       └── EfJournalEntryRepository.cs
└── Services/
    ├── AuditLogger.cs
    └── SystemClock.cs
```

---

### 10. Additional Package Needed

**EFCore.NamingConventions** — Required for `UseSnakeCaseNamingConvention()`:
```xml
<PackageReference Include="EFCore.NamingConventions" Version="10.0.*" />
```

This package provides PostgreSQL snake_case naming. Add to Infrastructure.csproj alongside Npgsql.

---

*Research completed: Sep 16 2026. Sources: NippySoft, csharp-coder.com, codingdroplets, codewithmukesh.com, FluentValidation docs, Learnixo, SEMastery, ronnythedev skills, OpenBaseNETPostgres, shadykhblog, LucasBonato template, Milan Jovanović, Woodruff, Rodrigo Bercocano, StackLesson, Stripe Systems, ardalis/CleanArchitecture, Luong Hong Thuan, ekolsoft.*
