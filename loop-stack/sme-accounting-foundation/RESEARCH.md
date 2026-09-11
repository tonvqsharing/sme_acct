# Research Log

## Pre-Implementation Baseline — Research Validation 2026-09-11

**Database baseline change**
- OLD baseline: MariaDB 10.11 LTS / 11.4 LTS, Pomelo.EntityFrameworkCore.MySql 9.0.0, EF Core 9.x, Testcontainers.MariaDb, utf8mb4_unicode_ci.
- NEW baseline: PostgreSQL 16.14, ASP.NET Core 10, EF Core 10, Npgsql, Testcontainers.PostgreSql.
- PostgreSQL 16.14 is installed on Windows 10 and reachable from Kali WSL at 172.21.208.1:5432. Connection verified via `psql`.
- All MariaDB-specific decisions in this file are retained for historical reference only and must NOT be used for implementation unless explicitly re-validated.

**Accounting regulatory baseline — uncertainty explicit**
- Previous research referenced Circular 133/2016/TT-BTC, Circular 200/2014/TT-BTC, Circular 99/2025/TT-BTC.
- Status: OPEN QUESTION — which regime is the target for MVP? Circular 133 is simplified SME regime, Circular 99 replaces Circular 200 for enterprises. No regulatory authority has been confirmed in this loop.
- CONFIRMED: Vietnam requires numbered chart of accounts, double-entry invariants, VAT tracking, VAS 10 FX rules, 90-day FS deadline.
- ASSUMPTION to be resolved: default COA seed set and reporting templates must be confirmed with authoritative source before seeding.
- No accounting business rules will be implemented in foundation phase.

**Technology validation summary**
- PostgreSQL 16 + ASP.NET Core 10: compatible.
- EF Core 10 + Npgsql: Npgsql 8.x+ targets EF Core 10; provider supports PostgreSQL 16.
- Data types for accounting: `numeric(18,2)` for money, `timestamptz` for timestamps, UUID or bigint for PKs — OPEN QUESTION.
- Concurrency: optimistic with `xmin`/`RowVersion` or `xmin` timestamp — TECHNICAL DECISION pending.
- Indexing: btree on account codes, date ranges, composite indexes — RECOMMENDATION.
- JSONB viable for audit snapshots — RECOMMENDATION.
- Testcontainers.PostgreSql supports integration tests; Docker required locally.

**Requirements classification snapshot**
- CONFIRMED REQUIREMENT: ASP.NET Core 10, Clean Architecture, Modular Monolith, on-premise deployment, Vietnamese UI, 12 module boundaries, Identity/Authorization foundations, audit fields, soft delete.
- ASSUMPTION: single tenant, MVC, MVC cookie auth, 5 standard roles, branch-scoped access, CompanyId field, soft delete mandatory, workflow/approval, inventory costing, accounting period automation, audit granularity, report versioning.
- OPEN QUESTION: OQ-1 naming convention (snake_case vs PascalCase — PostgreSQL prefers snake_case), OQ-2 tenant-ID field from day 1, OQ-3 assertion library, OQ-4 MVC vs Minimal API, OQ-5 multi-tenant strategy, OQ-6 payroll, OQ-7 audit granularity, OQ-8 workflow engine, OQ-9 report versioning, OQ-10 COA seed source.
- TECHNICAL DECISION: EF Core migrations idempotent SQL, Central Package Management, MediatR 12.5.0, Modular monolith with IModule registry.
- RISK: accounting regime ambiguity, PostgreSQL migration from existing MariaDB research, Windows dev/Linux prod parity, Npgsql EF Core 10 version pin, license changes for FluentAssertions/AwesomeAssertions.

**Non-goals for foundation**
- No accounting engine implementation, no business rules invention, no fake CRUD, no complete COA seed with authoritative data, no e-invoice integration, no payroll.

**Items Planner must resolve before coding**
- Confirm accounting regime and authoritative source for COA/report templates.
- Decide PK strategy UUID vs bigint, naming convention for PostgreSQL, timestamp strategy, concurrency token.
- Select Npgsql version for EF Core 10 and pin in Directory.Packages.props.
- Re-validate Testcontainers.PostgreSql version and CI strategy for Windows-hosted PostgreSQL vs Linux CI.
- Resolve open questions OQ-1, OQ-2, OQ-3, OQ-7, OQ-10.

## Context & Prior Work

### Repository State

The repository is a **fresh, empty project** with only scaffolding files:

```
.git/                          # Git initialized, 2 commits
.opencode/                     # Agent definitions for loop-engineer
loop-stack/                    # Loop tracking files
README.md                      # Contains only "# sme_acct"
```

- **Git history**: 2 commits, both titled "first commit"
- **No source code, no solution file, no projects** — everything must be created from scratch
- **No existing conventions, patterns, or constraints** in the codebase
- **No `.editorconfig`, `Directory.Build.props`, `.gitignore`, or `global.json`** yet

### .NET 10 Platform Characteristics

.NET 10 is an **LTS release** (supported until November 2028). Key facts:

- **Runtime**: JIT inlining improvements, escape analysis for stack allocation, AVX10.2 support, Arm64 write-barrier improvements (8-20% GC pause reduction)
- **ASP.NET Core 10**: OpenAPI 3.1 support (JSON Schema draft 2020-12), built-in validation via `AddValidation()`, Server-Sent Events, automatic memory pool eviction, passkey (WebAuthn/FIDO2) support for Identity
- **EF Core 10**: LINQ enhancements, named query filters, performance optimizations, improved Cosmos DB support
- **SDK**: Native container image creation for console apps, `dotnet tool exec`, `dnx` execution script, CLI introspection
- **C# 14**: Expected improvements (check release notes for specifics)
- **Target framework moniker**: `net10.0`

### Clean Architecture — Recommended .NET 10 Structure

Multiple authoritative sources converge on this standard 4-layer layout:

```
SmeAccounting.sln
├── src/
│   ├── SmeAccounting.Domain/           # Entities, Value Objects, Domain Events, Interfaces
│   ├── SmeAccounting.Application/      # Use Cases, CQRS, DTOs, Validators, Interfaces
│   ├── SmeAccounting.Infrastructure/   # EF Core, Repositories, External Services
│   └── SmeAccounting.Api/              # Controllers, Middleware, Program.cs
├── tests/
│   ├── SmeAccounting.Domain.Tests/
│   ├── SmeAccounting.Application.Tests/
│   ├── SmeAccounting.Infrastructure.Tests/
│   └── SmeAccounting.Architecture.Tests/  # NetArchTest enforcement
├── Directory.Build.props               # Shared MSBuild properties
└── global.json                         # SDK pinning
```

**Dependency Rule** (compiler-enforced via project references):
- Domain → **zero dependencies**
- Application → Domain only
- Infrastructure → Application + Domain
- Api → Application + Infrastructure

**Key packages** (based on research):
- `MediatR` — CQRS dispatching
- `FluentValidation` + `FluentValidation.DependencyInjectionExtensions` — input validation
- `Mapster` or `AutoMapper` — object mapping
- `NetArchTest` — architecture rule enforcement in tests
- `OneOf` or custom `Result<T>` — result pattern (avoid exceptions for flow control)

### Modular Monolith Pattern

For a multi-module accounting system, the recommended approach combines Clean Architecture with module boundaries:

```
SmeAccounting.sln
├── src/
│   ├── SharedKernel/                   # Base entities, domain events, shared abstractions
│   ├── Modules/
│   │   ├── Accounting/                 # Chart of accounts, journal entries, ledger
│   │   │   ├── Domain/
│   │   │   ├── Application/
│   │   │   └── Infrastructure/
│   │   ├── Identity/                   # Auth, users, roles, tenants
│   │   ├── Reporting/                  # Financial reports, statements
│   │   └── Tax/                        # VAT, tax calculations
│   └── Api/                            # Composition root, controllers
└── tests/
```

Module interaction happens through:
- **SharedKernel** — shared value objects, base entities, domain events
- **Internal events** — in-process event bus for cross-module communication
- **Explicit contracts** — no direct module-to-module project references

Reference architecture: [ardalis/VerticalCleanModularMicroservices](https://github.com/ardalis/VerticalCleanModularMicroservices) shows progression from vertical slice → clean → modular monolith → microservices.

### Accounting Domain — Bounded Contexts

Based on research of open-source accounting systems ([NerfedChou/Accounting-System](https://github.com/NerfedChou/Accounting-System), [amirhosein2015/FinLedger](https://github.com/amirhosein2015/FinLedger), [gabrielribeirof/summa](https://github.com/gabrielribeirof/summa)), the core bounded contexts for an SME accounting system are:

1. **Identity & Access Management** — Users, roles, permissions, multi-tenant isolation
2. **Company Management** — Company profiles, fiscal years, accounting periods
3. **Chart of Accounts** — Account hierarchy, account types (asset/liability/equity/revenue/expense), sub-accounts
4. **Transaction Processing** — Journal entries with double-entry validation, posting, draft→approved→posted lifecycle
5. **Ledger & Posting** — Balance tracking, account balances derived from journal entries (never stored as a column)
6. **Financial Reporting** — Balance sheet, income statement, trial balance, cash flow statement
7. **Tax Management** — VAT calculation, tax codes, tax reporting
8. **Audit Trail** — Complete activity logging, immutable append-only records
9. **Approval Workflow** — Transaction approval chains
10. **Multi-tenancy** — Tenant isolation (schema-per-tenant or database-per-tenant for on-premise)

**Core accounting invariants**:
- Every journal entry must balance: `SUM(debits) == SUM(credits)`
- Ledger entries are immutable (append-only); corrections via reversal entries
- Balance is always derived from journal entries, never stored
- Double-entry bookkeeping enforced at domain level

### Vietnamese Accounting Standards

Vietnam has specific accounting regulations relevant to this SME system:

- **Thông tư 200/2014/TT-BTC** (Circular 200) — Standard accounting regime for enterprises
- **Thông tư 133/2016/TT-BTC** (Circular 133) — Simplified accounting regime specifically for **SMEs** (doanh nghiệp nhỏ và vừa)
- **Thông tư 99/2025/TT-BTC** (replaces Circular 200) — Updated accounting guidance

Key Vietnamese accounting features:
- **Chart of accounts** follows a numbered system (111-Tiền mặt, 112-Tiền gửi ngân hàng, 131-Phải thu khách hàng, etc.)
- Account hierarchy: Level 1 (major category) → Level 2 → Level 3
- **VAT (Thuế GTGT)** — Value Added Tax with deductible input tax tracking (account 133)
- **Multi-currency support** — VND as functional currency with foreign currency transactions
- **Fiscal year** alignment with calendar year (typically)
- Vietnamese Accounting Standards (VAS) — 26 standards, SMEs exempt from several (CM 11, 19, 22, 25, 27, 28, 30)

### EF Core + MariaDB Provider

**Critical finding**: `Pomelo.EntityFrameworkCore.MySql` (the most popular MySQL/MariaDB EF Core provider) has a **delayed EF Core 10 support situation**:

- **Pomelo 9.0.0** (released 2025-08-17) supports EF Core 9.x — works with .NET 10 runtime but NOT EF Core 10
- **EF Core 10 support is still in progress** as of August 2026 — original maintainer appears inactive
- **Microting fork** (`Microting.EntityFrameworkCore.MySql`) has a working EF Core 10 preview (10.0.0-preview.3) with `ToJson()` support
- Tested MariaDB versions: 11.6, 11.5, 11.4 LTS, 11.3, 10.11 LTS, 10.6 LTS, 10.5 LTS

**Options for this project**:
1. **Use Pomelo 9.0.0** with .NET 10 (EF Core 9.x) — works today, stable, but misses EF Core 10 features
2. **Use Microting fork** for EF Core 10 — preview quality, community-maintained, risk of abandonment
3. **Use `MySQL.EntityFrameworkCore`** (Oracle's official provider) — has EF Core 10 RC, but lacks `ToJson()` for complex types

**Recommendation**: Start with **Pomelo 9.0.0** (proven stable, tested against MariaDB 10.5-11.6), migrate to Pomelo 10 when released. The EF Core 9→10 migration path is well-established.

### Technology Stack Summary

| Layer | Technology | Notes |
|-------|-----------|-------|
| Runtime | .NET 10 (LTS) | Supported until Nov 2028 |
| Web Framework | ASP.NET Core 10 | Minimal APIs or Controllers |
| ORM | EF Core 9 (via Pomelo) | MariaDB-compatible |
| Database | MariaDB 10.6+ LTS | On-premise deployment |
| CQRS | MediatR | Command/Query separation |
| Validation | FluentValidation | Pipeline behavior pattern |
| Testing | xUnit + NSubstitute + FluentAssertions | Standard .NET testing |
| Architecture Tests | NetArchTest | Enforce dependency rules |
| API Docs | Swagger/OpenAPI 3.1 | Built into ASP.NET Core 10 |
| Authentication | ASP.NET Core Identity + JWT | Passkey support available |
| PDF Generation | QuestPDF or DinkToPdf | Financial report export |
| Multi-tenancy | Shared database / Schema isolation | Per Vietnamese SME needs |

### Key References

- [Ardalis Clean Architecture Template](https://github.com/ardalis/CleanArchitecture) — .NET 10 reference template
- [Clean Architecture with .NET 10 and CQRS](https://medium.com/@michaelmaurice410/clean-architecture-with-net-10-and-cqrs-project-setup-90bc74fb3e93) — Complete project setup guide
- [rijwanansari/clean-architecture-dotnet10](https://github.com/rijwanansari/clean-architecture-dotnet10) — Production-grade .NET 10 with custom CQRS (no MediatR)
- [FinLedger](https://github.com/amirhosein2015/FinLedger) — .NET 9 double-entry accounting engine (Modular Monolith)
- [NerfedChou/Accounting-System](https://github.com/NerfedChou/Accounting-System) — DDD accounting system with 8 bounded contexts
- [What's new in .NET 10](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-10/overview) — Official docs
- [Pomelo EF Core MySQL](https://github.com/PomeloFoundation/Pomelo.EntityFrameworkCore.MySql) — MariaDB EF Core provider
- [Thông tư 133/2016/TT-BTC](https://cdn.thuvienphapluat.vn/uploads/DanLuat-BanAn/2025/10/Thong-tu-99-thay-the-thong-tu-200-ve-che-do-ke-toan.pdf) — Vietnamese SME accounting standards
- [Vietnam Accounting Standards overview](https://www.vietnam-briefing.com/doing-business-guide/vietnam/taxation-and-accounting/accounting-standards)

## External Knowledge & Resources

### ASP.NET Core 10 — Official Docs & Project Templates

- **Official docs**: [ASP.NET Core documentation](https://learn.microsoft.com/en-us/aspnet/core/?view=aspnetcore-10.0) (default moniker `aspnetcore-10.0`), [Host & deploy hub](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy?view=aspnetcore-10.0), [Minimal API tutorial](https://learn.microsoft.com/en-us/aspnet/core/tutorials/min-web-api?view=aspnetcore-10.0)
- **Preinstalled SDK templates** (from []dotnet-new-sdk-templates](https://github.com/dotnet/docs/blob/main/docs/core/tools/dotnet-new-sdk-templates.md)): `webapi`, `webapiaot`, `web` (empty), `mvc`, `webapp`/`razor` (Razor Pages), `apicontroller`, `grpc`, `blazor`, `xunit`, `sln`
- **Template packages on NuGet**: `Microsoft.DotNet.Common.ProjectTemplates.10.0`, `Microsoft.DotNet.Web.ProjectTemplates.10.0` (install with `dotnet new install <Pkg>`)
- **.NET 10 SDK changes relevant to scaffolding**:
  - `dotnet new sln` defaults to **slnx format** starting with .NET 10 (use `-f sln|slnx` to choose)
  - `dotnet new classlib` gains `--test-runner` (VSTest or **MTP** — Microsoft Testing Platform) — new in .NET 10 SDK
  - File-based apps `#:package` directive works from .NET 10 preview 4
- **Custom templates** (worth creating for this repo): [custom templates docs](https://learn.microsoft.com/en-us/dotnet/core/tools/custom-templates), [create project template tutorial](https://learn.microsoft.com/en-us/dotnet/core/tutorials/cli-templates-create-project-template), [install/manage templates](https://learn.microsoft.com/en-us/dotnet/core/install/templates). Template source is a runnable project + `.template.config/template.json`

### Clean Architecture Reference Templates (current, .NET 10)

- **Jason Taylor "Clean Architecture"** — de-facto standard reference. [Repo](https://github.com/jasontaylordev/CleanArchitecture), [site](https://cleanarchitecture.jasontaylordev.dev/), [architecture overview](https://cleanarchitecture.jasontaylordev.dev/docs/architecture). Install: `dotnet new install Clean.Architecture.Solution.Template`, then `dotnet new ca-sln -cf [angular|react|none] -db [postgresql|sqlite|sqlserver]`. v10.x (2026): now wired to **Aspire** (AppHost + ServiceDefaults), EF Core **10**, MediatR, FluentValidation pipeline behaviours, tests use **NUnit + Shouldly + Moq + Respawn**, `CleanArchitecture.slnx`. Note: after ~v10.8 the template moved to minimal API style; older controller/Identity style lives on `net8.0`/`net9.0` branches.
- **MinimDev/dotnet-clean-architecture-template** — .NET 10 minimal-hosting, MediatR **v12**, EF Core 10, Mapster, Scalar UI, OpenTelemetry. [Repo](https://github.com/MinimDev/dotnet-clean-architecture-template)
- **deadislove/dotnet-CleanArchMediatR-template** — Clean Arch + MediatR + multi-DB factory abstraction. [Repo](https://github.com/deadislove/dotnet-CleanArchMediatR-template)
- **Milan Jovanović** (influential .NET Clean/Modular blogger) — [Clean Architecture + CQRS + MediatR deep dive (.NET 10, 35 controllers ~200 endpoints)](https://umutkorkmaz.net/blog/clean-architecture-cqrs-mediatr-dotnet)

### Modular Monolith Patterns (.NET)

- **kgrzybek/modular-monolith-with-ddd** — the canonical production-grade reference (~13.9k stars). DDD, event-driven, in-process messaging, each module = mini Clean Architecture, module→module via **internal commands/queries/domain events** only (never project refs). [Repo](https://github.com/kgrzybek/modular-monolith-with-ddd) · forks: [arno-cassaniga](https://github.com/arno-cassaniga/modular-monolith-with-ddd), [U-dot-du](https://github.com/U-dot-du/modular-monolith-with-ddd) · [InfoQ 2019 write-up](https://www.infoq.com/news/2019/09/design-ddd-modular-monolith) · [podcast on "Design & Implementation"](https://www.infoq.com/news/2019/09/design-ddd-modular-monolith/)
- **NET-Architecture-Templates/ModularMonolith** (2026) — minimal, opinionated template; `BuildingBlocks/` shared kernel + `Modules/{Module}/` each with Domain/Application/Infrastructure; module→module communication ONLY via events/contracts. [Repo](https://github.com/NET-Architecture-Templates/ModularMonolith)
- **deadislove/dotnet-ModularMonolith-template** — .NET 9, dynamic module discovery (`IModule` + `IEntityTypeConfiguration<T>` reflection), multi-DB. [Repo](https://github.com/deadislove/dotnet-ModularMonolith-template)
- **Anton DevTips Modular Monolith template** (updated to .NET 10 + Aspire, 2026). [Download](https://antondevtips.com/templates/modular-monolith)
- NimblePros (Ardalis): [Building a Modular Monolith in .NET](https://blog.nimblepros.com/blogs/modular-monolith-dotnet); reference progression [ardalis/VerticalCleanModularMicroservices](https://github.com/ardalis/VerticalCleanModularMicroservices)

**Key takeaways for the executor**: module isolation rules (no module→module references, all cross-module comms through shared kernel contracts / in-process events), single database OK (schema/table-prefix per module) — appropriate for on-premise SME.

### MariaDB + .NET / Pomelo / MySqlConnector

- **Pomelo** (official, tested against MariaDB 11.6/11.5/11.4 LTS/11.3/10.11 LTS/10.6 LTS/10.5 LTS): [Repo/README](https://github.com/PomeloFoundation/Pomelo.EntityFrameworkCore.MySql), [Configuration Options wiki](https://github.com/PomeloFoundation/Pomelo.EntityFrameworkCore.MySql/wiki/Configuration-Options), [EF tutorial](https://mysqlconnector.net/tutorials/efcore)
- **Setup pattern**: register with `UseMySql(connectionString, new MariaDbServerVersion(new Version(10, 6, 0)))` (prefer explicit `MariaDbServerVersion` over `ServerVersion.AutoDetect()` in production). Optional: `EnableRetryOnFailure()`, `EnableIndexOptimizedBooleanColumns()`, `LimitKeyedOrIndexedStringColumnLength` (default on — caps string column length so indices fit). Production: `DisableSensitiveDataLogging`/`DisableDetailedErrors`.
- **MySqlConnector** powers Pomelo; connection string syntax `Server=...;User ID=...;Password=...;Database=...` — see [connection string options](https://github.com/mysql-net/MySqlConnector/blob/master/docs/content/tutorials/efcore.md)
- **Charset/collation critical for Vietnamese**: 
  - MariaDB default charset is **latin1 until 11.6** — gotcha. Must set `utf8mb4` at database creation: `CREATE DATABASE ... CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci` (or server `character-set-server=utf8mb4`)
  - `utf8mb4_unicode_ci` (UCA) handles Vietnamese diacritics correctly; MariaDB ≥10.10 adds `utf8mb4_uca1400_*`, ≥11.4.5 adds `utf8mb4_0900_*` aliases. [MariaDB unicode docs](https://mariadb.com/docs/server/reference/data-types/string-data-types/character-sets/unicode), [Setting character sets/collations](https://mariadb.com/docs/server/reference/data-types/string-data-types/character-sets/setting-character-sets-and-collations)
  - In EF Core via Pomelo: `modelBuilder.HasCharSet("utf8mb4").UseCollation("utf8mb4_unicode_ci")` at the model/database level (docs for Oracle provider: [Configuring Character Sets and Collations in EF Core](https://dev.mysql.com/doc/connector-net/en/connector-net-entityframework-core-charset.html))
- **Money columns**: use EF `decimal(precision: 18, scale: 2)` (VND has no decimals in accounting books; but rates/quantities may need 2-4 scale). Pomelo maps `decimal` → `DECIMAL(18,2)` by default.

### Vietnamese Accounting Standards — operational details (drill-down beyond R1)

- **Circular 133/2016/TT-BTC (SME regime)** — sources: [full text THƯ VIỆN PHÁP LUẬT](https://thuvienphapluat.vn/van-ban/doanh-nghiep/circular-133-2016-tt-btc-accounting-for-small-medium-enterprises-337431.aspx), [English edition (partial)](https://thuvienphapluat.vn/van-ban/EN/Doanh-nghiep/Circular-133-2016-TT-BTC-accounting-for-small-medium-enterprises/337431/tieng-anh.aspx), [official gazette summary](https://congbao.chinhphu.vn/van-ban/thong-tu-so-133-2016-tt-btc-21048.htm), [analysis by law firm](https://luatvietan.vn/thong-tu-moi-ve-che-ke-toan-doanh-nghiep-nho-va-vua.html)
  - Effective 01/01/2017 for fiscal years starting on/after that; ~90 articles + annexes
  - **Chapter II = Chart of accounts** (numbered system: 1-2 = assets, 3 = liabilities, 4 = equity, 5 = revenue, 6 = costs) — e.g. 111 cash, 112 bank, 131 receivables, **133 deductible VAT**, 214 accumulated depreciation, 228 equity investments, 229 asset impairment provisions
  - Enterprises may add level-2/level-3 sub-accounts freely (must match content/structure) — so the app must support an **open, seedable chart of accounts**
  - **Foreign currency** (Article 52): balances reassessed at financial-statement time using the "regular bank's" closing-average transfer rate; exchange differences → financial income/expense; VND-denominated legal FS required
  - **Annual FS deadline**: within **90 days** after fiscal year end (Art. 80); monthly/quarterly statements optional
  - SMEs may OPTIONALLY adopt Circular 200 regime (must notify tax authority; consistent for the whole fiscal year)
  - **Excluded VAS standards for SMEs**: VAS 11 (Amalgamation), 19 (Insurance contracts), 22, 27 (interim FS), 28, 30 (public offerings)
- **Circular 200/2014/TT-BTC (enterprise regime)** — [full text](https://thuvienphapluat.vn/van-ban/doanh-nghiep/circular-no-200-2014-tt-btc-on-guidelines-for-accounting-policies-for-enterprises-273356.aspx), [Vietnamese summary](https://luatvietnam.vn/doanh-nghiep/toan-van-thong-tu-200-2014-tt-btc-che-do-ke-toan-doanh-nghiep-92289-d1.html)
  - **Phụ lục (annexes)**: PL1 chart of accounts + posting guidance, PL2 FS forms, PL3 documents/working papers, PL4 ledger/book forms
  - Ledger books (Sổ Cái, Sổ Nhật ký, kế toán chi tiết) forms are **NOT mandated** — free format as long as complete/clear/auditable → print/export freedom
  - FS forms have **standard indices** — enterprises must get Ministry approval to add/change FS line items → **report templates are regulatory constraints**, version them in code/seed data
  - Effectively superseded by **Circular 99/2025/TT-BTC** ("replaces 200"; new account chart in PL II) — [note on 99 vs 133](https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/ho-tro-phap-luat/chinh-sach-moi/97431/thong-tu-133-2016-tt-btc-co-bi-thay-the-boi-thong-tu-99-2025-tt-btc-che-do-ke-toan-doanh-nghiep-khong), [new chart of accounts under 99](https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/ho-tro-phap-luat/tu-van-phap-luat/105580/bang-he-thong-tai-khoan-ke-toan-moi-nhat-theo-thong-tu-99-2025-tt-btc). **Executor must decide**: seed default COA per 133 (SME target) with 200/99 as alternates.
  - **Business-registration linked docs**: [dangkykinhdoanh.gov.vn](https://dangkykinhdoanh.gov.vn/vn/Pages/ChiTietVanBan.aspx?vID=26994)

### Bootstrap 5 + jQuery for Razor Pages / MVC

- **LibMan** (Microsoft's lightweight client-side asset manager — right fit for jQuery/Bootstrap without npm):
  - [LibMan docs](https://learn.microsoft.com/en-us/aspnet/core/client-side/libman?view=aspnetcore-10.0), [LibMan CLI](https://learn.microsoft.com/en-us/aspnet/core/client-side/libman/libman-cli?view=aspnetcore-10.0) (`dotnet tool install -g Microsoft.Web.LibraryManager.Cli`), [LibMan in VS](https://learn.microsoft.com/en-us/aspnet/core/client-side/libman/libman-vs?view=aspnetcore-10.0)
  - `libman.json` manifest: providers **cdnjs | jsDelivr | unpkg**; e.g. `jquery@3.7.1` + `bootstrap@5.3.6` → `wwwroot/lib/`
- **Layout structure**: `_Layout.cshtml` (`Views/Shared/` for MVC, `Pages/Shared/` for Razor Pages) + `_ViewImports.cshtml` (`@addTagHelper *, Microsoft.AspNetCore.Mvc.TagHelpers`) + `@section Scripts` for page-locale script injection. [Layout docs](https://learn.microsoft.com/en-us/aspnet/core/mvc/views/layout?view=aspnetcore-10.0), [Tag Helpers](https://learn.microsoft.com/en-us/aspnet/core/mvc/views/tag-helpers/intro?view=aspnetcore-10.0), [built-in tag helpers](https://learn.microsoft.com/en-us/aspnet/core/mvc/views/tag-helpers/built-in?view=aspnetcore-10.0)
- **Free Bootstrap 5 admin dashboards that ship ASP.NET Core MVC versions** (sidebar layout w/ razor rollup, good starting point for internal tool UI): **Sneat** Free — [themeselection/sneat-bootstrap-html-aspnet-core-mvc-admin-template-free](https://github.com/themeselection/sneat-bootstrap-html-aspnet-core-mvc-admin-template-free)
- Static assets served from `wwwroot/` automatically; cache-busting via `asp-append-version` tag helper (ImageTagHelper/`ScriptTagHelper` cache-busting) — see Tag Helpers docs.

### On-premise Deployment for ASP.NET Core

- **General model**: publish to folder → process manager starts it → optional reverse proxy. [Host and deploy overview](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy?view=aspnetcore-10.0)
- **Windows IIS**: install **.NET Hosting Bundle**; default **in-process** hosting model; publish framework-dependent or self-contained. [Host on IIS](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/iis?view=aspnetcore-10.0), [Publish app to IIS tutorial](https://learn.microsoft.com/en-us/aspnet/core/tutorials/publish-to-iis?view=aspnetcore-10.0)
- **Windows Service**: for background/headless workloads (ASP.NET Worker) — [Host as Windows Service](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/windows-service?view=aspnetcore-10.0)
- **Linux Nginx**: Kestrel behind nginx reverse proxy + systemd; use `ForwardedHeaders` middleware (Microsoft.AspNetCore.HttpOverrides) so HTTPS/X-Forwarded-* resolve. [Host on Linux with Nginx](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/linux-nginx?view=aspnetcore-10.0). **Recommended for on-premise Linux + MariaDB bundles.**
- **Web server implementations** (Kestrel/IIS in-process/out-of-process/HTTP.sys): [fundamentals/servers](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/servers?view=aspnetcore-10.0)
- Zero-downtime: blue-green deployments + IIS Overlapped Recycle recommended in [IIS article](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/iis?view=aspnetcore-10.0)

### Testing / TDD for ASP.NET Core

- **Framework choice (2026 status)**:
  - xUnit is default; xUnit **v3** (~4.0) + **Microsoft Testing Platform (MTP)** is the modern runner — `dotnet new xunit --test-runner MTP` (SDK 10). Docs: [Building and testing .NET](https://docs.github.com/en/actions/tutorials/build-and-test-code/net)
  - NUnit 4.x and MSTest remain viable; MS Learn integration-test docs cover all three ([Integration tests in ASP.NET Core](https://learn.microsoft.com/en-us/aspnet/core/test/integration-tests?view=aspnetcore-10.0))
  - **TUnit** — new MTP-native source-generated framework, fast, ASP.NET Core + Aspire + Playwright integrations ([github](https://github.com/thomhurst/TUnit)); benchmark leader but younger ecosystem — xUnit still safer default
- **Mocking**: NSubstitute (recommended; clean syntax, active) vs Moq (**controversy**: 4.20 analytics scandal + [issue #1372](https://github.com/moq/moq/issues/1372); contributors still recommend switching). FakeItEasy as alternative. See [list of .NET testing tools](https://github.com/dariusz-wozniak/List-of-Testing-Tools-and-Frameworks-for-.NET/blob/master/README.md) and [mocking-strategy notes](https://github.com/valinerosgordov/NET-Mastery-Hub/blob/main/Testing/Middle/mocking-strategies.md)
  - **Anti-pattern**: don't mock DbContext; use real DB in integration tests
- **Assertions**: FluentAssertions **changed to paid license in 2025** for commercial use → community fork **AwesomeAssertions** (formerly FluentAssertions, actively maintained). [Fork](https://github.com/awesomeassertions/AwesomeAssertions). Shouldly = fine alternative. **Executor: decide FA pre-license versions vs AwesomeAssertions vs Shouldly before writing assertion-heavy code.**
- **Integration tests**: `Microsoft.AspNetCore.Mvc.Testing` → `WebApplicationFactory<TEntryPoint>` hosts the real app in `TestServer`; override configuration/services for test DB. [Official docs](https://learn.microsoft.com/en-us/aspnet/core/test/integration-tests?view=aspnetcore-10.0), [Testcontainers-ASP.NET example](https://dotnet.testcontainers.org/examples/aspnet)
- **DB-in-tests**: **Testcontainers** `Testcontainers.MariaDb` ([module](https://testcontainers.com/modules/mariadb) / [nuget](https://www.nuget.org/packages/Testcontainers.MariaDb)) or `Testcontainers.MySql`; xUnit integration `Testcontainers.Xunit` / `Testcontainers.XunitV3`. **Respawn** ([github](https://github.com/jbogard/Respawn)) — fast DB reset between tests (Jason Taylor template uses it). Rule: pin image versions.
- **Architecture tests**: **NetArchTest.Rules 1.3.2** (latest; original repo slow/dev-dormant, MIT, .NET Standard 2.0) — [repo](https://github.com/BenMorris/NetArchTest), [nuget](https://www.nuget.org/packages/NetArchTest.Rules); alternative maintained: **TNG/ArchUnitNET** ([github](https://github.com/TNG/ArchUnitNET), `TngTech.ArchUnitNET.xUnit`, reads IL in Debug). Milan Jovanović: [architecture testing with NetArchTest](https://milanjovanovic.tech/blog/shift-left-with-architecture-testing-in-dotnet)

### Open-Source Double-Entry Accounting (architecture inspiration)

- **NLedger** — complete pure-C# port of Ledger CLI, double-entry engine, zero external deps: [dmitry-merzlyakov/nledger](https://github.com/dmitry-merzlyakov/nledger) (FreeBSD license)
- **dubbl** — full-featured OSS Xero/QuickBooks alternative (double-entry core, invoicing, reports, multi-currency, audit trail, API-first): [dubbl](https://github.com/dubbl-org/dubbl) (Apache-2.0, TS/Next.js stack)
- **Ledger** (C++ reference engine), **GnuCash** (C, double-entry, multi-currency) — good domain-behavior references, non-.NET
- See also Researcher 1's FinLedger / NerfedChou/Accounting-System for .NET modular monolith accounting engines

### CI/CD for .NET (GitHub Actions)

- **Canonical template**: [Building and testing .NET (GitHub Docs)](https://docs.github.com/en/actions/tutorials/build-and-test-code/net): `actions/checkout@v6` + `actions/setup-dotnet@v4` (`dotnet-version: '10.0.x'`) → `dotnet restore` → `dotnet build --no-restore -c Release` → `dotnet test --no-build -c Release`. Current versions observed mid-2026: checkout v6/v7, setup-dotnet v4/v6 (setup-dotnet upgraded to node24, [repo](https://github.com/actions/setup-dotnet)).
- **MariaDB in CI** (no Docker service needed): **shogo82148/actions-setup-mysql@v1** — supports `distribution: mariadb` with `mysql-version: 11.8 | 11.4 | 10.11` (LTS chains), also `11.8`/`11.4`/`10.11` via `mariadb-` prefix, `my-cnf` input to force utf8mb4. [Marketplace](https://github.com/marketplace/actions/actions-setup-mysql)
- **Docker service alternative**: `services: mariadb: image: mariadb:lts` with `ports: 3306`, `credentials: root`; wait via `healthcheck.sh --connect --innodb_initialized` (incl. GitHub Actions service config; see [MariaDB healthcheck docs](https://mariadb.com/docs/server/server-management/automated-mariadb-deployment-and-administration/docker-and-mariadb/using-healthcheck-sh) & [openemr compose example](https://github.com/openemr/openemr/blob/master/docker/production/docker-compose.yml))
- .NET + Actions primer: [.NET blog intro](https://devblogs.microsoft.com/dotnet/dotnet-loves-github-actions), [MS Learn: DevOps + GitHub Actions for .NET](https://learn.microsoft.com/en-us/dotnet/devops/github-actions-overview), [test-validation workflow](https://learn.microsoft.com/en-us/dotnet/devops/dotnet-test-github-action)

### EF Core migration strategy (MariaDB)

- **Official guidance**: [Applying migrations (EF Core)](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying) — 4 strategies:
  1. **SQL script / idempotent script** (`dotnet ef migrations script --idempotent -o migrations.sql`) — best for DBA/review-gated deploys (recommended for on-premise accounting customers)
  2. **Migration bundle** (`dotnet ef migrations bundle --self-contained -r linux-x64 -o efbundle`) — automated CI/CD, no SDK needed, single-process, idempotent, uses EF migration locking + seeding
  3. EF CLI tools — dev only
  4. Runtime `db.Database.Migrate()` at startup — simplest, but couples startup to DB availability; fine for single-instance on-premise
- **EF Core 9+ behavior change**: throws if model has pending changes without a migration (breaks naive `Migrate()` upgrades)
- **Best practice (Milan Jovanović, 2026)**: review generated SQL; one logical change per migration; **expand-contract** for breaking column changes; never `dotnet ef database update` in production under load-balanced/multi-instance. [Article](https://milanjovanovic.tech/blog/ef-core-migrations-best-practices). Migration bundles intro: [.NET blog](https://devblogs.microsoft.com/dotnet/introducing-devops-friendly-ef-core-migration-bundles)
- **Separate Migrations project** keeps DbContext clean and enables design-time factory across modules: [EF docs — separate migrations project](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/projects)
- **Modular monolith caveat**: one migrations project per module or a single shared one — decide during planning; Pomelo supports standard EF migrations (`PomeloFoundation` wiki, [Migration doc](https://deepwiki.com/PomeloFoundation/Pomelo.EntityFrameworkCore.MySql/4.1-migrations))

### PDF / Report Generation (financial reports, sổ/BC)

- **QuestPDF** — most popular code-first PDF for .NET (invoices/reports; Vietnamese FS export). **License change (2025)**: now requires a **license key**; **free Community license** available for small org/hobby. Latest `2026.8.0`. [GitHub](https://github.com/QuestPDF/QuestPDF), [NuGet](https://www.nuget.org/packages/QuestPDF), [site](https://www.questpdf.com/). Supports Linux (on-prem) via SkiaSharp native assets.

### Recommendations for executor (synthesis)

1. Scaffold templates: use built-in SDK 10 templates (`webapi`/`mvc`/`sln` with slnx) or install `Clean.Architecture.Solution.Template` and adapt (swap EF Core provider to Pomelo + MariaDB; template ships SQL Server/Postgres/SQLite only).
2. DB: MariaDB **10.11 LTS or 11.4 LTS**; force `utf8mb4` + `utf8mb4_unicode_ci` at DB creation and in EF model (`HasCharSet/UseCollation`); explicit `MariaDbServerVersion` in Pomelo registration; `decimal(18,2)` money columns.
3. Standards: seed chart of accounts per **Circular 133** (SME) as default; design FS report templates as versioned data (indices are regulated); support VND + foreign-currency reassessment (Art. 52), VAT 133, 90-day annual FS cycle.
4. UI: Razor Pages or MVC with LibMan-managed Bootstrap 5 + jQuery; Sneat free MVC admin template as layout seed.
5. Deploy: Linux Nginx + systemd (recommended) or Windows IIS in-process via Hosting Bundle; framework-dependent publish; forward-headers middleware.
6. Migrations: versioned `--idempotent` SQL script produced in CI, applied as deploy step before app start; keep one logical change per migration.
7. Tests: xUnit v3 (+ MTP), NSubstitute, Testcontainers.MariaDb + Respawn for integration; NetArchTest.Rules (pin 1.3.2) or ArchUnitNET for dependency rules; **resolve FluentAssertions license → AwesomeAssertions/Shouldly** before writing asserts (global memory update recommended).
8. CI: GitHub Actions `setup-dotnet@v4` + `dotnet restore/build --no-restore --no-build test`; MariaDB via `shogo82148/actions-setup-mysql` (mariadb distribution) for integration tests.
9. Reports: QuestPDF (Community license) for FS/ledger PDF export.

## Requirements & Constraints

### 1. CONFIRMED REQUIREMENTS — Vietnamese Accounting Domain

#### 1A. Chart of Accounts (Circular 133/2016/TT-BTC — Appendix I)

The system MUST implement a Vietnamese SME chart of accounts per Circular 133. Key structural facts:

- **49 Level-1 accounts** across 9 account types (1=Short-term Assets, 2=Long-term Assets, 3=Liabilities, 4=Equity, 5=Revenue, 6=COGS, 7=Production/Business Costs, 8=Other Costs, 9=Result Determination)
- **Level-2 sub-accounts** prescribed for most Level-1 accounts; enterprises may freely add Level-2/Level-3 sub-accounts without MoF approval — only Level-1/Level-2 code/name/content changes require written MoF approval
- **Account numbering convention**: 3-digit Level-1 (e.g. 111, 112, 131, 133, 156, 211, 331, 511, 632, 911); Level-2 is 4-digit; Level-3 is 5+ digits
- **Key Level-1 accounts for MVP**:
  - `111` Cash (1111-VND, 1112-Foreign currency)
  - `112` Bank Deposits (1121-VND, 1122-Foreign currency)
  - `121` Trading Securities
  - `128` Held-to-Maturity Investments
  - `131` Accounts Receivable
  - `133` Deductible VAT (1331-Services/Goods, 1332-Fixed Assets)
  - `136` Intra-company Receivables
  - `138` Other Receivables
  - `141` Advances
  - `151` Goods in Transit
  - `152` Raw Materials
  - `153` Tools & Instruments
  - `154` WIP Production Costs
  - `155` Finished Goods
  - `156` Merchandise
  - `157` Goods Sent for Sale
  - `211` Fixed Assets (2111-Tangible, 2112-Finance Lease, 2113-Intangible)
  - `214` Accumulated Depreciation
  - `217` Investment Property
  - `228` Equity Investments in Other Entities
  - `229` Asset Impairment Provisions (2291-Securities, 2293-Doubtful Debts, 2294-Inventory)
  - `241` Capital Construction in Progress
  - `242` Prepaid Expenses
  - `331` Accounts Payable
  - `333` Taxes & State Payables (3331-VAT Payable, 3334-CIT, 3335-PIT, 3338-Other Taxes, 3339-Fees)
  - `334` Employee Payables
  - `335` Accrued Expenses
  - `336` Intra-company Payables
  - `338` Other Payables (3382-Trade Union Fund, 3383-Social Insurance, 3384-Health Insurance, 3385-Unemployment Insurance)
  - `341` Loans & Finance Lease Liabilities
  - `352` Provisions (3521-Warranty, 3522-Construction)
  - `353` Bonus & Welfare Funds
  - `411` Charter Capital
  - `413` Foreign Exchange Rate Differences
  - `511` Sales Revenue (5111-Goods, 5112-Sub-goods, 5113-Services)
  - `515` Financial Income (Exchange Rate Gains)
  - `632` Cost of Goods Sold
  - `635` Financial Expenses (Exchange Rate Losses)
  - `911` Result Determination
- **CRITICAL**: The system MUST support an open, seedable chart of accounts — enterprises customize freely; no rigid hardcoding of account list in domain logic

#### 1B. Double-Entry Accounting Invariants

These are non-negotiable domain invariants:

1. **Every journal entry MUST balance**: `SUM(debits) == SUM(credits)` — enforced at domain level, not just UI
2. **Ledger entries are immutable** (append-only); corrections via reversal entries only (never delete/modify posted entries)
3. **Balance is always derived** from journal entries — never stored as a denormalized column (calculated via query)
4. **Account types constrain posting direction**: Asset/Expense accounts increase on debit; Liability/Equity/Revenue increase on credit — enforce at domain level
5. **Every journal entry requires**: date, voucher number, description, at least 2 lines (debit + credit), reference to original document
6. **Accounting period lock**: entries cannot be posted to closed periods

#### 1C. Multi-Currency & Foreign Exchange

Per VAS 10 and Circular 133 Art. 52 / Circular 99:

- **VND is the default functional currency** (mandatory for statutory FS); Circular 99 allows foreign currency as accounting currency with specific criteria
- **Exchange rate types**: Transaction date rate (spot), Average rate (period), Closing rate (period-end revaluation)
- **Foreign currency transactions**: recorded at spot rate on transaction date; exchange differences → financial income (Account 515) or financial expense (Account 635)
- **Period-end revaluation**: monetary items in foreign currency revalued at closing rate; unrealized differences → Account 413 (Foreign Exchange Rate Differences)
- **Rate source**: average buying-selling transfer rate from the enterprise's primary bank; may use approximate rate within ±1% deviation
- **FS presentation**: all statutory financial statements must be in VND

#### 1D. VAT Tracking

- Account `133` (Deductible VAT) with sub-accounts `1331` (Goods/Services) and `1332` (Fixed Assets)
- Account `3331` (VAT Payable) with sub-accounts `33311` (Output VAT) and `33312` (Import VAT)
- VAT rates: 10% (standard), 5% (essential goods), 0% (exports); 8% temporary reduction extended through 2026
- Non-deductible VAT must be recorded separately (entertainment, certain expenses per CIT law)
- VAT declaration support: Form 01/GTGT (monthly/quarterly)

#### 1E. Financial Reporting

- **Statutory FS forms** (Appendix IV of Circular 133):
  - Balance Sheet (B01-DN — renamed "Statement of Financial Position" under Circular 99)
  - Income Statement / Business Results (B02-DN)
  - Cash Flow Statement (B03-DN)
  - Notes to Financial Statements
- **FS line items have standard indices** — enterprises need MoF approval to add/change FS items → report templates are **regulatory constraints**, must be versioned in code/seed data
- **Annual FS deadline**: within 90 days after fiscal year end
- **Trial Balance**: prerequisite check before period closing
- **Ledger books** (Sổ Cái, Sổ Nhật ký, Sổ kế toán chi tiết): forms are **NOT mandated** — free format, only print/export freedom

#### 1F. Accounting Period Management

- **Fiscal year** typically calendar year (Jan 1 – Dec 31), but configurable
- **Period structure**: Year → Quarters → Months (or just Year → Months)
- **Period states**: Open → Closed (locked); closing generates closing entries
- **Period-end processes**: trial balance, revaluation of foreign currency, accruals, depreciation, closing entries
- **Cannot post to closed periods** — hard constraint

#### 1G. Document & Voucher System

- **Accounting vouchers** (Chứng từ kế toán): each economic transaction requires exactly one voucher
- **Standard voucher templates** (Appendix I of Circular 133/99): Enterprises may design custom forms (must meet Law on Accounting Art. 16 requirements)
- **Voucher types**: Receipt (Phiếu thu Mẫu 01-TT), Payment (Phiếu chi Mẫu 02-TT), Journal Entry, plus business-specific vouchers
- **Document lifecycle**: Draft → Submitted → Approved → Posted (with rejection/cancellation)
- **E-invoicing integration** readiness (Decree 123/2020/ND-CP): software must be "capable of connecting or ready to connect" with e-invoice, digital signature software

---

### 2. CONFIRMED REQUIREMENTS — Module Boundaries

Based on domain analysis and existing research, the application must implement these modules:

#### 2A. Core Accounting Modules (MVP Priority)
1. **Chart of Accounts** — COA hierarchy, account types, sub-accounts, open extension
2. **Accounting Period** — fiscal year, periods, opening/closing, lock enforcement
3. **Journal** — journal entry creation, balanced validation, draft→approved→posted lifecycle
4. **Posting** — posting engine, period validation, balance calculation
5. **General Ledger** — account balances (derived), trial balance, ledger queries

#### 2B. Operational Modules (Phase 2)
6. **Accounts Receivable** — customer invoices, aging, payment matching
7. **Accounts Payable** — vendor invoices, aging, payment matching
8. **Cash & Bank** — cash management, bank reconciliation, foreign currency cash
9. **Sales** — sales orders, delivery, invoicing, revenue recognition
10. **Purchasing** — purchase orders, receipt, vendor invoicing
11. **Inventory** — stock management, cost methods (weighted average, FIFO), stocktake
12. **Fixed Assets** — asset register, depreciation calculation, disposal

#### 2C. Tax & Reporting Modules
13. **Tax Management** — VAT calculation, tax codes, VAT declaration preparation
14. **Financial Reporting** — Balance Sheet, Income Statement, Cash Flow, Trial Balance, Notes — all versioned as regulatory templates

#### 2D. Platform Modules (MVP Priority)
15. **Identity** — user management, authentication, session
16. **Authorization** — roles, permissions, RBAC
17. **Organization** — company, branch, department structure
18. **Master Data** — customers, vendors, currencies, exchange rates
19. **Audit** — activity logging, change tracking
20. **Document Management** — voucher attachments, document storage
21. **Configuration** — system settings, accounting policies
22. **Workflow** — approval chains for journal entries, vouchers

#### 2E. Future Modules
23. **Inventory** (advanced) — multi-warehouse, lot tracking, serial numbers
24. **Reporting** — custom reports, dashboards, management reporting
25. **System Administration** — user/role management UI, system health

---

### 3. CONFIRMED REQUIREMENTS — Authentication & Security

- **Authentication**: ASP.NET Core Identity (cookie-based for MVC/Razor Pages; JWT for API if needed)
- **Login/Logout**: standard Identity UI; session management via cookie authentication
- **Password policy**: configurable minimum length, complexity, expiry
- **Failed login lockout**: configurable attempts threshold, lockout duration
- **Password reset**: email-based flow (if email provider configured) or admin-initiated
- **Account status**: Active, Locked, Disabled states
- **Session management**: configurable timeout; single-session or multi-session policy
- **Security audit log**: every auth event logged (login success/failure, password changes, role assignments)

---

### 4. CONFIRMED REQUIREMENTS — Authorization (RBAC)

Per Vietnamese accounting regulations and standard practice:

- **Role-based access control** with fine-grained permissions per module
- **Standard roles** (minimum):
  - `Admin` — full system access
  - `ChiefAccountant` — all accounting operations, period closing, FS preparation
  - `Accountant` — journal entry, voucher processing, master data maintenance
  - `Viewer` — read-only access to reports and data
  - `Auditor` — read-only + audit trail access (cannot modify data)
- **Permission granularity**: per-module, per-action (View, Create, Edit, Delete, Approve, Post)
- **Policy-based authorization** using ASP.NET Core `IAuthorizationRequirement` + `AuthorizationHandler`
- **Multi-branch access**: users assigned to branches; branch-scoped data access
- **Approval authority limits**: amount-based thresholds for journal entry approval (e.g., Accountant < 500M VND, ChiefAccountant < 5B VND)

---

### 5. CONFIRMED REQUIREMENTS — Organizational Structure

Per Vietnamese SME structure:

- **Company** (Đơn vị): single legal entity; the base tenant
- **Branch** (Chi nhánh): optional subdivisions; shares same COA, currency, fiscal year; may have separate cash accounts and warehouses
- **Department** (Bộ phận): internal organizational unit; for reporting and access control
- **Employee** (Nhân viên): linked to a branch/department; maps to system users
- **Key constraint**: All branches within a company share the same COA, base currency (VND), and fiscal year — branches are NOT independent tenants

---

### 6. CONFIRMED REQUIREMENTS — Master Data

- **Customers** (Khách hàng): customer profiles with tax code, address, contact, payment terms
- **Vendors** (Nhà cung cấp): vendor profiles with tax code, address, contact, payment terms
- **Currencies** (Loại tiền tệ): VND (mandatory default) + configurable foreign currencies
- **Exchange Rates** (Tỷ giá): daily rates per currency; buy/sell/transfer; manual entry or API import (Vietcombank, ACB recommended)
- **Inventory Items** (Vật tư, hàng hóa): item codes, names, units, cost methods, VAT rates
- **Chart of Accounts**: as detailed in §1A above

---

### 7. CONFIRMED REQUIREMENTS — Cross-Cutting Concerns

| Concern | Requirement | Implementation Notes |
|---------|-------------|---------------------|
| **Localization** | Vietnamese (vi-VN) primary; UI strings in Vietnamese; number/currency/date formatting per Vietnamese conventions | Resource files; Vietnamese number format uses `.` for thousands, `,` for decimal |
| **Audit Trail** | Every create/update/delete logged with: user, timestamp, before/after values | EF Core `IInterceptor` or domain events; append-only audit log table |
| **Validation** | Input validation on all commands; business rule validation in domain layer | FluentValidation as MediatR pipeline behavior |
| **Error Handling** | Consistent error responses; structured error logging; user-friendly error pages | Global exception middleware; ProblemDetails for API |
| **Logging** | Structured logging (Serilog); request/response correlation; security events | Serilog + SEQ or file sink |
| **Configuration** | System settings per company: fiscal year, accounting policies, posting rules | Configuration module with admin UI |
| **Current User** | `ICurrentUserProvider` abstraction for accessing authenticated user context | Injected into MediatR handlers; NOT HTTP context dependency |
| **Time Provider** | `IDateTimeProvider` abstraction for testable time-dependent logic | `SystemTime.UtcNow` pattern |
| **Database Transactions** | Explicit transaction management for multi-step operations; EF Core `IDbContextTransaction` | Transaction scope per use case, not per request |
| **File Storage** | Document attachments (vouchers, invoices): local file system for on-premise | `wwwroot/uploads/` or configurable path; file metadata in DB |
| **Notifications** | In-app notifications for: period closing reminders, approval requests, system alerts | Simple notification table + UI; email optional (Phase 2) |
| **Health Checks** | Database connectivity, disk space, memory usage | ASP.NET Core health checks middleware |
| **Caching** | Reference data caching (COA, master data, exchange rates) | In-memory (IMemoryCache) for single-instance on-premise |
| **Concurrency** | Optimistic concurrency for concurrent journal entry posting | EF Core `RowVersion` / `ConcurrencyStamp` on key entities |

---

### 8. CONFIRMED REQUIREMENTS — Database

- **Engine**: MariaDB 10.11 LTS (recommended) or 11.4 LTS
- **Charset**: `utf8mb4` + `utf8mb4_unicode_ci` (MANDATORY for Vietnamese diacritics; MariaDB defaults to latin1 until 11.6)
- **ORM**: EF Core 9 via Pomelo.EntityFrameworkCore.MySql 9.0.0
- **Money columns**: `decimal(18, 2)` — VND has no decimal in accounting books; rates/quantities may need higher scale
- **Naming convention**: snake_case for tables/columns (MariaDB convention) or PascalCase (EF Core convention) — DECIDE
- **Audit fields**: `Created_at`, `Created_by`, `Updated_at`, `Updated_by`, `Is_deleted`, `Deleted_at`, `Deleted_by` on all mutable entities
- **Soft delete**: mandatory for all entities (accounting data must never be physically deleted)
- **Migration strategy**: EF Core migrations → idempotent SQL script for on-premise deployment review
- **Indexing strategy**: composite indexes on frequently queried columns (account + period, date + account, voucher number unique)
- **Constraint strategy**: foreign keys at DB level; unique constraints on business keys (account codes, voucher numbers, tax codes)

---

### 9. CONFIRMED REQUIREMENTS — Architecture Constraints

These are hard architectural rules (compiler-enforced via NetArchTest):

1. **Domain layer has ZERO external dependencies** — no NuGet packages, no framework references beyond BCL
2. **Application layer depends ONLY on Domain** — no Infrastructure, no API references
3. **Infrastructure layer depends on Application + Domain** — implements interfaces defined in upper layers
4. **API layer depends on Application + Infrastructure** — composition root, controllers, middleware
5. **No circular dependencies** between any layers
6. **No business logic in controllers** — controllers delegate to MediatR handlers
7. **No `static` methods in domain** — use injectable services for testability
8. **Domain entities are persistence-ignorant** — no EF Core annotations, no database concerns in domain
9. **Module boundaries**: no direct module→module project references; cross-module communication via SharedKernel contracts or internal domain events

---

### 10. CONFIRMED REQUIREMENTS — Testing

- **Unit Tests**: domain logic, validation rules, use case handlers (xUnit + NSubstitute)
- **Application Tests**: MediatR handler integration with in-memory fakes (xUnit)
- **Integration Tests**: full request→response cycle with real MariaDB (WebApplicationFactory + Testcontainers.MariaDb + Respawn)
- **Database Tests**: EF Core migrations, seed data, constraint verification
- **Architecture Tests**: dependency rule enforcement (NetArchTest.Rules 1.3.2)
- **Security Tests**: authentication/authorization policy verification
- **TDD encouraged**: write tests before implementation for domain-critical logic

---

### 11. ASSUMPTIONS (NOT YET VERIFIED)

1. **Single-company, multi-branch**: assuming on-premise deployment targets a single Vietnamese legal entity with optional branches — NOT multi-tenant SaaS
   - **Risk if wrong**: entire architecture pivots from branch-scoped to tenant-scoped isolation
2. **MVC over Razor Pages**: assuming ASP.NET Core MVC pattern (controllers + views) based on Sneat template compatibility
   - **Risk if low**: Razor Pages would simplify CRUD but Sneat is MVC-oriented
3. **No e-invoicing in MVP**: assuming e-invoice integration (VNPT, Viettel, MISA) is Phase 2+; foundation only needs "readiness" (API surface)
4. **No payroll in scope**: PIT (3335) and social insurance accounts exist in COA but payroll calculation/management is out of scope
5. **No multi-company consolidation**: assuming single-company only; intercompany accounts (136, 336) exist in COA but consolidation logic is Phase 3+
6. **On-premise file storage**: assuming documents stored on local filesystem, not cloud storage (S3/Azure Blob)
7. **Vietnamese language UI only**: assuming no i18n/l10n framework needed beyond Vietnamese; English UI is not required
8. **No mobile app**: assuming web-only (responsive Bootstrap 5) for now

---

### 12. OPEN QUESTIONS

| # | Question | Impact | Decision Needed By |
|---|----------|--------|-------------------|
| OQ-1 | **Naming convention**: snake_case (MariaDB native) vs PascalCase (EF Core default) for DB objects? | Migration scripts, EF configuration, query writing | Architect |
| OQ-2 | **Multi-tenancy later?**: Should the data model include `CompanyId`/`TenantId` on all entities from day 1, even if single-tenant for MVP? | Schema change is expensive; adding tenant isolation later requires migration of ALL tables | Architect + PM |
| OQ-3 | **Assertion library**: AwesomeAssertions (FA fork) vs Shouldly? Global memory says "revisit" | All test code; license implications | Architect |
| OQ-4 | **Period closing automation**: How much of period-end processing should be automated vs manual? (Depreciation, revaluation, closing entries) | UX complexity, domain logic scope | PM + Accountant |
| OQ-5 | **Inventory costing method**: Weighted average only, or also support FIFO/specific identification? | Inventory module complexity; Circular 99 allows more flexibility | PM |
| OQ-6 | **Currency rate API**: Should we integrate Vietcombank/ACB rate APIs, or manual entry only for MVP? | Integration scope, API reliability | PM |
| OQ-7 | **Audit granularity**: Every field change, or entity-level before/after snapshot? | Storage, performance, compliance needs | Architect + Compliance |
| OQ-8 | **Workflow engine**: Simple status machine in code, or configurable rule engine for approvals? | Development complexity, flexibility | PM |
| OQ-9 | **Report template versioning**: How to handle FS form changes when regulations update? | Deployment, data migration | Architect |
| OQ-10 | **Seed data scope**: Only Circular 133 COA, or include Circular 99/200 as alternate templates? | Configuration complexity, market reach | PM |

---

### 13. TECHNICAL DECISIONS (ALREADY MADE)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Runtime | .NET 10 LTS | LTS support until Nov 2028; latest performance |
| ORM | EF Core 9 via Pomelo 9.0.0 | Stable MariaDB support; migrate to Pomelo 10 when available |
| CQRS | MediatR | Battle-tested; clean separation; ecosystem maturity |
| Validation | FluentValidation (pipeline behavior) | Integrates with MediatR; expressive rule syntax |
| Testing framework | xUnit v3 + MTP | Modern .NET 10 testing; `dotnet new xunit --test-runner MTP` |
| Mocking | NSubstitute | Clean syntax; no Moq analytics controversy |
| Architecture tests | NetArchTest.Rules 1.3.2 (pinned) | Standard for .NET dependency rule enforcement |
| DB engine | MariaDB 10.11 LTS | On-premise friendly; utf8mb4_unicode_ci for Vietnamese |
| PDF generation | QuestPDF (Community license) | Code-first; Linux compatible; standard for .NET |
| Frontend | Bootstrap 5.3.x + jQuery 3.7.x + Sneat MVC template | Lightweight; no SPA framework needed for internal tool |
| CI/CD | GitHub Actions + shogo82148/actions-setup-mysql (mariadb) | MariaDB native in CI; no Docker required |
| Deployment | Linux Nginx + systemd (primary); Windows IIS (secondary) | On-premise target; ForwardedHeaders middleware |
| EF Migrations | Idempotent SQL script (`--idempotent`) | Review-gated on-premise deployment |

---

### 14. BUSINESS DECISIONS

| Decision | Choice | Notes |
|----------|--------|-------|
| Target market | Vietnamese SMEs | Circular 133 regime; Vietnamese-only UI |
| Deployment model | On-premise (single server) | No cloud dependency; data stays with customer |
| Pricing model | TBD | Not in scope for foundation |
| Language | Vietnamese only (vi-VN) | No i18n framework for MVP |
| Single company per install | Yes (MVP) | Branches within company, not multi-tenant |

---

### 15. RISKS

| Risk | Severity | Mitigation |
|------|----------|------------|
| Pomelo EF Core 10 delay | Medium | Use Pomelo 9.0.0 now; EF Core 9→10 migration path is well-established |
| Circular 99 supersedes Circular 200 | Low | Circular 133 remains in effect for SMEs; seed COA per 133, add 99 as alternate |
| MariaDB default charset (latin1 before 11.6) | High | Force `utf8mb4` at DB creation AND in EF model (`HasCharSet/UseCollation`) |
| FluentAssertions license change (2025) | Medium | Use AwesomeAssertions fork; pin version |
| Vietnamese accounting regulation changes | Medium | Version FS report templates in seed data; design for template updates |
| E-invoice integration complexity | Medium | Design API surface now; implement connectors in Phase 2 |
| Single-tenant assumption may be wrong | High | Include `CompanyId` field on key entities from day 1 (low cost, high safety) |
| On-premise deployment variability | Medium | Provide both Linux and Windows deployment guides; test both in CI |
| Audit trail storage growth | Medium | Implement log rotation/archival strategy; partition audit tables by year |

---

### 16. CONSTRAINTS (NON-NEGOTIABLE)

1. **Domain layer MUST NOT depend on Infrastructure or Web** — compiler-enforced via project references + NetArchTest
2. **No business logic in controllers** — all logic in MediatR handlers or domain services
3. **Every journal entry MUST balance** — `SUM(debits) == SUM(credits)` — domain invariant, never bypassed
4. **Posted journal entries are immutable** — corrections only via reversal entries
5. **Cannot post to closed accounting periods** — hard constraint in posting engine
6. **VND is the functional currency for statutory reporting** — all FS in VND
7. **utf8mb4_unicode_ci collation for all tables** — Vietnamese diacritics support mandatory
8. **Soft delete for all mutable entities** — no physical deletion of accounting data
9. **Audit trail on all data mutations** — regulatory requirement for accounting systems
10. **EF Core migrations must be idempotent SQL scripts** — for review-gated on-premise deployment
11. **.NET 10 LTS (net10.0)** — target framework moniker is non-negotiable
12. **MariaDB 10.6+ (recommend 10.11 LTS)** — minimum database version

---

### 17. REFERENCES

| Reference | Source |
|-----------|--------|
| Circular 133/2016/TT-BTC (SME accounting regime) | [thuvienphapluat.vn](https://thuvienphapluat.vn/van-ban/Doanh-nghiep/Circular-133-2016-TT-BTC-accounting-for-small-medium-enterprises-337431.aspx) |
| Circular 99/2025/TT-BTC (replaces Circular 200) | [vnlawfirm.vn](https://vnlawfirm.vn/van-ban/circular-no-99-2025-tt-btc-on-corporate-accounting-guidelines/) |
| Circular 200/2014/TT-BTC (enterprise regime, superseded) | [thuvienphapluat.vn](https://thuvienphapluat.vn/van-ban/doanh-nghiep/circular-no-200-2014-tt-btc-on-guidelines-for-accounting-policies-for-enterprises-273356.aspx) |
| Grant Thornton Circular 133 analysis | [grantthornton.com.vn](https://www.grantthornton.com.vn/insights/audit-and-assurance/accounting-alert---circular-no.1332016tt-btc) |
| VAS 10 — Foreign Exchange | [docs.kreston.vn](https://docs.kreston.vn/vbpl/ke-toan/chuan-muc-ke-toan/vas-10/) |
| KPMG Circular 99 key changes | [kpmg.com/vn](https://kpmg.com/vn/en/insights/2025/11/key-changes-in-vietnamese-accounting-system-for-enterprises.html) |
| GTG CRM accounting features (reference implementation) | [gtgcrm.com](https://gtgcrm.com/en/features/bo-ke-toan-hoa-don-dien-tu) |
| Viindoo Vietnam COA (Odoo module reference) | [viindoo.com](https://viindoo.com/apps/modules/19.0/l10n_vn_viin) |
| Odoo Vietnam localization guide 2026 | [ecosire.com](https://ecosire.com/blog/odoo-vietnam-localization-guide-2026) |
| Vietnamese chart of accounts full list (Công ty TNHH Kế Toán FAT) | [fastca.vn](https://fastca.vn/he-thong-tai-khoan-theo-thong-tu-133) |
| FinLedger (.NET accounting reference) | [github.com/amirhosein2015/FinLedger](https://github.com/amirhosein2015/FinLedger) |
| MyERP (.NET accounting reference) | [github.com/amerfathullah/MyERP](https://github.com/amerfathullah/MyERP) |
| MiniAccountManagement (ASP.NET Identity + RBAC) | [github.com/masumKazibd/MiniAccountManagement](https://github.com/masumKazibd/MiniAccountManagement) |
| SS Audit — Foreign Currency Revaluation workflow | [local.docs.ssaudit.com](https://local.docs.ssaudit.com/english-1/cash-management-module/release-batches) |

## Environment & Integration

> Covers build structure, CI/CD, Docker, on-premise deploy (Linux+Windows), config/secrets, Serilog, health checks, backup/restore, publish strategy, and EF migrations/seeding. Builds on TOOLS.md CI/CD + deployment notes — this section adds the complete, production-ready artifacts (full YAML, Dockerfile, systemd unit, Caddy/Nginx config, backup script, Directory.*.props). Verified against 2026 docs.

### Build Structure (solution-level conventions)

- **`.slnx` (new XML solution format)** is the `.NET 10 SDK` default for `dotnet new sln` (`-f sln|slnx`). Recommend `.slnx` for cleaner diffs (no nested {GUID} project entries).
- **`global.json`** — pin SDK at repo root (`rollForward: latestFeature`, e.g. `"version": "10.0.400"`). Guarantees CI runners and dev boxes build the same SDK. getversion from `dotnet --version`.
- **`Directory.Build.props`** (auto-imported from repo root walking up) — centralize per-project defaults:
  ```xml
  <Project>
    <PropertyGroup>
      <TargetFramework>net10.0</TargetFramework>
      <LangVersion>latest</LangVersion>
      <Nullable>enable</Nullable>
      <ImplicitUsings>enable</ImplicitUsings>
      <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
      <AnalysisLevel>latest-recommended</AnalysisLevel>
      <RootNamespace>$(MSBuildProjectName)</RootNamespace>
      <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
    </PropertyGroup>
  </Project>
  ```
  - Pitfall: `$(TargetFramework)` conditions in `.props` **silently fail** for single-target projects (TFM is empty during props evaluation) — move TFM-conditional logic to `Directory.Build.targets`. Rule: properties/items → `.props`; custom targets/late-bound logic → `.targets`.
  - Evaluaton order: `Directory.Build.props` → SDK `.props` → `Project.csproj` → SDK `.targets` → `Directory.Build.targets`.
- **Central Package Management (CPM)** via `Directory.Packages.props` — single `PackageVersion` per package, project `.csproj` files carry only versionless `<PackageReference>`.
  ```xml
  <Project>
    <ItemGroup>
      <PackageVersion Include="MediatR" Version="12.4.1" />
      <PackageVersion Include="Pomelo.EntityFrameworkCore.MySql" Version="9.0.0" />
      <!-- analyzers applied to every project -->
      <GlobalPackageReference Include="StyleCop.Analyzers" Version="1.2.0-beta.517" />
      <GlobalPackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers" Version="10.0.0" />
    </ItemGroup>
  </Project>
  ```
  - Enable `CentralPackageTransitivePinningEnabled=true` to lift vulnerable transitive deps solution-wide; disable `VersionOverride` (`CentralPackageVersionOverrideEnabled=false`) if drift must be impossible. NU1507 (multiple sources) → use **package source mapping** in `NuGet.config`.
  - SDK 10 package commands are CPM-aware (`dotnet package add/update` edit `Directory.Packages.props` automatically).
- **`NuGet.config`** at root: single `nuget.org` source (+ optional private feed) with **packageSourceMapping** (mitigates dependency-confusion; requires per-feed clear pattern list).
- **`Directory.Build.targets`** — regex / API-approval / license linting gates that need final values; safe place for custom `Target`s.
- **`.editorconfig`** — enforce `csharp_style_namespace_declarations=file_scoped`, `dotnet_diagnostic.*.severity`, max line length, etc.; analyzer-driven, no build cost. The template dotsnet/skills `directory-build-organization` SKILL is the canonical reference for the props/targets split.
- **Artifacts layout**: use `--artifacts-path artifacts` (SDK 8+, default in templates) → `artifacts/bin`, `artifacts/obj` (single globally-organized output; clear in CI).
- **Recommended layout for this repo** (converges with Researcher 1):
  ```
  SmeAccounting.slnx
  ├── src/{SmeAccounting.Domain,Application,Infrastructure,Api}/
  ├── src/Modules/*/ {Domain,Application,Infrastructure}/
  ├── tests/{...Tests}/
  ├── docs/
  ├── scripts/                      # tangle: ef-migrations, backup, restore, deploy
  ├── deploy/                       # nginx/Caddy conf, systemd unit, IIS web.config, Dockerfile, compose
  ├── Directory.Build.props/.targets
  ├── Directory.Packages.props
  ├── NuGet.config
  ├── global.json
  └── .editorconfig / .gitignore / .dockerignore
  ```

### CI/CD — complete GitHub Actions workflow (.NET 10 + MariaDB)

Two MariaDB options already in TOOLS.md: `shogo82148/actions-setup-mysql@v1` (`distribution: mariadb`) or Docker `services:` block. Full workflow (fails-fast, caching, integration tests, migration SQL artifact, container publish):

```yaml
name: ci
on:
  push: { branches: [main] }
  pull_request:
permissions: { contents: read }

env:
  DOTNET_NOLOGO: true

jobs:
  build-test:
    runs-on: ubuntu-latest
    services:
      mariadb:
        image: mariadb:11.4
        env:
          MARIADB_ROOT_PASSWORD: root
          MARIADB_DATABASE: smeacct_test
          MARIADB_USER: smeacct
          MARIADB_PASSWORD: smeacct
        ports: ['3306:3306']
        options: >-
          --health-cmd "healthcheck.sh --connect --innodb_initialized"
          --health-interval 10s --health-timeout 5s --health-retries 3 --health-start-period 30s
          --health-start-period 30s
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: '10.0.x' }
      - uses: actions/cache@v4
        with:
          path: ~/.nuget/packages
          key: ${{ runner.os }}-nuget-${{ hashFiles('**/packages.lock.json') }}
          restore-keys: ${{ runner.os }}-nuget
      - run: dotnet restore --locked-mode --use-lock-file   # reproducible restore
      - run: dotnet build -c Release --no-restore
      - run: dotnet test -c Release --no-build --test-runner MTP   # unit + architecture
      - run: dotnet test tests/SmeAccounting.Infrastructure.Tests -c Release --no-build \
              -e ConnectionStrings__DefaultConnection="Server=127.0.0.1;Port=3306;Database=smeacct_test;User ID=smeacct;Password=smeacct;"
  ef-artifacts:          # produces review-gated migration SQL + bundle for the CD/deploy step
    runs-on: ubuntu-latest
    needs: build-test
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: '10.0.x' }
      - run: dotnet tool restore
      - run: dotnet ef migrations bundle --configuration Release \
              --target-project src/SmeAccounting.Infrastructure \
              --startup-project src/SmeAccounting.Api --self-contained -r linux-x64 -o artifacts/efbundle
      - run: dotnet ef migrations script --idempotent \
              --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api \
              -o artifacts/migrations-idempotent.sql
      - uses: actions/upload-artifact@v4
        with:
          name: migrate
          path: artifacts/*
  docker:
    runs-on: ubuntu-latest
    needs: build-test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: '10.0.x' }
      - run: dotnet publish src/SmeAccounting.Api -c Release -t:PublishContainer \
              -p ContainerRegistry=${{ vars.REGISTRY }} -p ContainerRepository=sme-acct \
              -p ContainerImageTag=${{ github.sha }}
```

Key facts:
- **Reproducible restore**: commit `packages.lock.json` (`dotnet restore --use-lock-file` then commit), restore with `--locked-mode`. Pins exact versions regardless of upstream changes.
- **Lint/code-quality gate**: run analyzers in build (SDK built-in `AnalysisLevel`), optionally `dotnet format --verify-no-changes`, plus a CodeQL/Security-101 workflow. No separate "lint" tool needed for C# beyond analyzers + format.
- **Versions observed 2026**: `actions/checkout@v6` (v7 exists), `actions/setup-dotnet@v4` (v6 exists; v4 suffices), `actions/cache@v4`, `actions/upload-artifact@v4`.
- **Gate docker push** to main only; tag image with SHA and/or semver (`-p:Version`).
- CD to a VPS user reveals gaps: ship `artifacts` (plus a `deploy` job on tags) → rsync/SCP → run migration bundle or SQL → swap symlink → restart systemd (see Deployment strategy).

### Docker — multi-stage Dockerfile & compose

**.NET 10 container image facts (2026)**:
- Default Linux distro changed to **Ubuntu 24.04 Noble** (Debian images are not shipped for .NET 10). Tags: `10.0`, `10.0-noble`, `10.0-noble-chiseled`; Alpine `10.0-alpine3.22`; Azure Linux; Windows `nanoserver-ltsc2022/2025`.
- Chiseled (distroless): no shell, no apt, **non-root by default (UID 1654)**, chisel manifest available (install extra slices with `chisel`). `-extra` variant has ICU+tz for full globalization.
- Default port 8080, `ASPNETCORE_HTTP_PORTS=8080`; non-root can't bind <1024.
- `.NET 10 chiseled = transfer full-file IDs` … `dotnet publish /t:PublishContainer` builds images without a Dockerfile; `PublishContainer` infers base: ASP.NET project → `aspnet:*`, self-contained → `runtime-deps:*`. Native AOT SDK images: `sdk:10.0-noble-aot` (clang/zlib bundled).
- Default `nano` → use framework-dependent on chiseled `aspnet` for accelerated CVE fixes (base-image bump fixes runtime vulns without app rebuild) — the right default for a single-instance on-premise app too.

**Production Dockerfile** (3-stage: restore → publish → chiseled runtime):

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0-noble AS restore
WORKDIR /src
COPY Directory.Build.props Directory.Packages.props global.json ./
COPY NuGet.config ./
COPY SmeAccounting.slnx ./
COPY src/ src/
RUN dotnet restore SmeAccounting.slnx --locked-mode

FROM restore AS publish
COPY . .
RUN dotnet publish src/SmeAccounting.Api/SmeAccounting.Api.csproj \
    -c Release --no-restore -o /app/publish \
    /p:DebugType=None /p:DebugSymbols=false /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled AS final
WORKDIR /app
ENV DOTNET_EnableDiagnostics=0
COPY --from=publish /app/publish .
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8080/health/live || exit 1
USER $APP_UID
ENTRYPOINT ["dotnet", "SmeAccounting.Api.dll"]
```
Notes: chiseled has no shell — the `HEALTHCHECK` above should be implemented at the **orchestration/compose level** (curl/wget exists in the `c` base but not chiseled; prefer compose-level healthcheck against the app's `/health/live`). `/p:UseAppHost=false` avoids the redundant native host; `ENV + traps` — DebugType eviction shaves ~10-30MB. `.dockerignore` (**.git, bin, obj, artifacts, .vs**) keeps the build context to <1MB and preserves restore-layer caching.

**docker-compose.yml** (dev + on-premise reference):

```yaml
services:
  app:
    build: .
    restart: unless-stopped
    ports: ["8080:8080"]
    environment:
      ASPNETCORE_ENVIRONMENT: Production
      ConnectionStrings__DefaultConnection: "Server=mariadb;Port=3306;Database=smeacct;User ID=smeacct;Password=${DB_PASSWORD:?set in .env}"
      Serilog__MinimumLevel__Default: Information
    volumes:
      - app-keys:/app/keys
      - app-uploads:/app/uploads
    depends_on:
      mariadb: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8080/health/ready"]
      interval: 30s, timeout: 5s, start_period: 20s, retries: 3
  mariadb:
    image: mariadb:11.4
    restart: unless-stopped
    environment:
      MARIADB_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:?set in .env}
      MARIADB_DATABASE: smeacct
      MARIADB_USER: smeacct
      MARIADB_PASSWORD: ${DB_PASSWORD}
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --innodb-buffer-pool-size=256M
    volumes:
      - mariadb-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      start_period: 60s, interval: 30s, timeout: 10s, retries: 5
volumes: { mariadb-data: {}, app-keys: {}, app-uploads: {} }
```
- Force `utf8mb4`+`utf8mb4_unicode_ci` via `command:` args (MariaDB default latin1 until 11.6 — Researcher warnings).
- Healthcheck users are auto-created by official image (`healthcheck@localhost` etc. with USAGE); `--innodb_initialized` covers crash-recovery-before-ready.
- Secrets via `.env` (not committed); app -> `compose` infers base. Volumes keep Data Protection keyring + uploads across container rebuilds.

### On-premise deployment

**Linux — Kestrel + Nginx + systemd** (canonical MS Learn host-and-deploy/linux-nginx pattern):
- systemd unit `/etc/systemd/system/sme-acct.service`:
  ```ini
  [Unit]
  Description=SmeAccounting ASP.NET Core App
  After=network.target mariadb.service
  [Service]
  WorkingDirectory=/srv/sme-acct/current
  ExecStart=/usr/bin/dotnet /srv/sme-acct/current/SmeAccounting.Api.dll
  Restart=always
  RestartSec=10
  Environment=ASPNETCORE_ENVIRONMENT=Production
  Environment=DOTNET_PRINT_TELEMETRY_MESSAGE=false
  Environment=ConnectionStrings__DefaultConnection=Server=127.0.0.1;Port=3306;Database=smeacct;User ID=smeacct;Password=${DB_PASSWORD}
  User=smeacct
  Group=smeacct
  # hardening
  NoNewPrivileges=true
  PrivateTmp=true
  LimitNOFILE=65535
  [Install]
  WantedBy=multi-user.target
  ```
  The systemd Environment loads from `/etc/systemd/system/sme-acct.service` — prefer an `EnvironmentFile=/etc/sme-acct.env` (mode 600) so secrets aren't in the unit.
- Kestrel listens on `http://127.0.0.1:5000` (or a socket); proxy terminates TLS. **Set** `ASPNETCORE_URLS=http://127.0.0.1:5000` explicitly.
- Nginx `server` block: `proxy_pass http://127.0.0.1:5000`, `proxy_set_header Host $host`, `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host`. Enable **ForwardedHeaders**:
  - .NET 10 shortcut: env `ASPNETCORE_FORWARDEDHEADERS_ENABLED=true` (equivalent to `UseForwardedHeaders()` defaults — does NOT set KnownNetworks/KnownProxies).
  - Production hardening: configure `UseForwardedHeaders` manually with `KnownNetworks`/`KnownProxies` set to the proxy IP so **spoofed X-Forwarded-For from clients is rejected**:
    ```csharp
    builder.Services.Configure<ForwardedHeadersOptions>(o =>
    {
        o.ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto | ForwardedHeaders.XForwardedHost;
        o.KnownProxies.Add(IPAddress.Parse("127.0.0.1"));
    });
    app.UseForwardedHeaders(); // MUST be placed before UseHsts / UseAuthentication / redirect logic
    ```
- **HTTPS**: terminate TLS at proxy. Options: (a) Nginx w/ certbot+Let's Encrypt; (b) **Caddy** — auto HTTPS, zero-config cert provisioning/renewal:
  ```
  # Caddyfile — reverse proxy + automatic Let's Encrypt for public domain
  (security) {
      header X-Content-Type-Options nosniff
      header X-Frame-Options DENY
      header Strict-Transport-Security "max-age=31536000"
  }
  accounting.contoso.vn {
      encode zstd gzip
      reverse_proxy 127.0.0.1:5000
      import security
      request_body {
          max_size 50MB
      }
  }
  ```
  Caddy ELIGIBLE: single binary, auto-TLS, `reverse_proxy` handles Host/headers/websockets, HTTP/3. For internal/LAN on-premise (no public domain) use Nginx with a self-signed cert (documented trust), or Caddy with explicit internal CA. Recommendation for this project (Vietnamese on-premise, often intranet): **Nginx** for LAN/self-signed, **Caddy** where a public domain exists.
- Windows: **IIS in-process** via `.NET Hosting Bundle`, `web.config` is auto-generated at publish (`<aspNetCore processPath="dotnet" arguments=".\SmeAccounting.Api.dll" hostingModel="inProcess"/>`). App Pool identity → `setProfileEnvironment` note. Set env vars on App Pool (ConnectionStrings, ASPNETCORE_ENVIRONMENT). Windows Service (`dotnet run` via `worker` templates or chez `sc.exe` / NSSM) if no IIS.
- **Data Protection key ring — critical on-premise detail** (if using cookies/antiforgery):
  - Default in IIS = DPAPI + registry (recycled-ok); default standalone Linux = **in-memory only → every restart invalidates auth cookies**. On Docker/Linux **must** `PersistKeysToFileSystem` to a persistent directory (volume/`/srv/sme-acct/keys`) + `SetApplicationName("SmeAccounting")` (must match across instances).
  - On Windows use `ProtectKeysWithDpapi()` (DPAPI at rest). Keys default lifetime 90 days; **never delete keys** (breaks existing cookies/tokens). Key ring → treat like secrets volume, include in backup. This is the single most common "users randomly logged out after deploy/recycle" root cause for ASP.NET Core on-premise.

### Configuration management & secrets

- **Configuration order** (later wins): `appsettings.json` → `appsettings.{Environment}.json` → user-secrets (dev) → env vars (`KEY__SUBKEY`) → command-line. Same image/config tree across environments; only env vars + `ASPNETCORE_ENVIRONMENT` change per site.
- **Recommended shape** — settings sections as strongly-typed options (`builder.Services.Configure<JournalOptions>(cfg.GetSection("Journal"))`), connection strings under `ConnectionStrings:DefaultConnection`.
- **Secrets policy (on-premise)**:
  - Dev: `dotnet user-secrets set "ConnectionStrings:DefaultConnection" "..."` (stores under `~/.microsoft/usersecrets/{guid}`).
  - Server: Windows → App Pool env vars / IIS config `appSettings`; Linux → `EnvironmentFile=/etc/sme-acct.env` (0600) or systemd `LoadCredential`; Docker → `.env` + compose variables. **Never** commit real values; ship placeholder `appsettings.Production.json` with empty `${...}` placeholders and document required env vars in `deploy/README`.
  - Optional: `KeyVault`-style → skip; for on-premise a 0600 file is the pragmatic "vault".
- **App-secret hygiene specifics**: connection string password, SMTP, Data Protection purpose name, external rate API keys, QuestPDF license key — all env-var-driven.

### Logging — Serilog (structured)

- Packages (`Serilog.AspNetCore 10.0.0` bundles core + Console + File + Settings.Configuration): `Serilog.AspNetCore`, `Serilog.Enrichers.Environment/Thread/Process`, `Serilog.Exceptions`, `Serilog.Sinks.Seq` (9.0.0), `Serilog.Sinks.Async`, optional `Serilog.Formatting.Compact`. Serilog 4.x is AOT/trimming-safe.
- **Two-stage bootstrap** in Program.cs (capture startup failures):
  ```csharp
  Log.Logger = new LoggerConfiguration().WriteTo.Console().CreateBootstrapLogger();
  try {
      var builder = WebApplication.CreateBuilder(args);
      builder.Services.AddSerilog((services, lc) => lc
          .ReadFrom.Configuration(builder.Configuration)
          .ReadFrom.Services(services)
          .Enrich.FromLogContext());
      var app = builder.Build();
      app.UseSerilogRequestLogging();   // before routing/auth; one structured line per request
      app.Run();
  }
  catch (Exception ex) { Log.Fatal(ex, "Startup failed"); }
  finally { await Log.CloseAndFlushAsync(); }
  ```
- `appsettings.json` template (sinks + level overrides):
  ```json
  { "Serilog": {
      "Using": ["Serilog.Sinks.Console","Serilog.Sinks.File","Serilog.Enrichers.Environment","Serilog.Enrichers.Thread","Serilog.Enrichers.Process","Serilog.Exceptions"],
      "MinimumLevel": { "Default": "Information",
        "Override": { "Microsoft.AspNetCore": "Warning",
          "Microsoft.AspNetCore.Hosting.Diagnostics": "Error",
          "Microsoft.EntityFrameworkCore.Database.Command": "Warning",
          "System.Net.Http.HttpClient": "Warning" } },
      "WriteTo": [
        { "Name": "Console" },
        { "Name": "File", "Args": { "path": "logs/log-.json", "rollingInterval": "Day",
          "rollOnFileSizeLimit": true, "fileSizeLimitBytes": 104857600, "retainedFileCountLimit": 14,
          "formatter": "Serilog.Formatting.Compact.CompactJsonFormatter, Serilog.Formatting.Compact" } },
        { "Name": "Seq", "Args": { "serverUrl": "http://localhost:5341" } }
      ],
      "Enrich": ["FromLogContext","WithMachineName","WithProcessId","WithThreadId","WithExceptionDetails"],
      "Properties": { "Application": "SmeAccounting" } } }
  ```
  - `Override` for EF `.Database.Command` to Warning = don't drown in SQL; keep `Microsoft.Hosting.Lifetime` at Information.
  - In Production remove Seq unless self-hosted; roll to file + (optionally) `Serilog.Sinks.Grafana.Loki` / `Elastic.Serilog.Sinks` / OTLP.
  - Prefer **CompactJsonFormatter** (newline-delimited JSON, parseable by jq/seq/Loki) over text templates for files.
  - Use `WriteTo.Async(a => a.File(...))` in prod; correlated logging with Serilog auto-captures `TraceId/SpanId`.
  - Request logging: `UseSerilogRequestLogging(o => { o.EnrichDiagnosticContext = (dc, http) => { dc.Set("UserId", http.User?.FindFirst("sub")); }; })` to attach user identity — essential for audit-grade queries.

### Health checks

- Packages (in-box): `Microsoft.AspNetCore.Diagnostics.HealthChecks`; EF check: `Microsoft.Extensions.Diagnostics.HealthChecks.EntityFrameworkCore` (10.0.x); MariaDB ping check: **`AspNetCore.HealthChecks.MySql` 9.0.0** (Xabaril, prefers `MySqlDataSource` from DI so it shares the app's pool; defaults to a MySQL "ping" packet — pass `healthQuery: "SELECT 1;"` to keep the classic behavior).
- Registration:
  ```csharp
  builder.Services.AddHealthChecks()
      .AddMySql(healthQuery: "SELECT 1;", name: "mariadb",
                failureStatus: HealthStatus.Unhealthy, tags: ["db","ready"])
      .AddDbContextCheck<SmeAccountingDbContext>("ef-core", tags: ["db","ready"])
      .AddCheck<DiskSpaceHealthCheck>("disk", tags: ["live","ready"]);
  ```
- **Endpoint split — liveness vs readiness** (esp. for orchestrators; single on-premise instance still benefits):
  ```csharp
  app.MapHealthChecks("/health/live", new HealthCheckOptions {
      Predicate = _ => false,                     // no DB — process alive
      ResultStatusCodes = { [HealthStatus.Healthy]=200,[HealthStatus.Degraded]=200,[HealthStatus.Unhealthy]=503 } })
      .ShortCircuit();                            // skips middleware for high-frequency probes
  app.MapHealthChecks("/health/ready", new HealthCheckOptions {
      Predicate = c => c.Tags.Contains("ready"),
      ResponseWriter = WriteJsonResponse })
      .RequireHost("localhost","127.0.0.1");      // protect probe endpoint from WAN
  ```
  - Keep DB probe lightweight (`SELECT 1` / `CanConnectAsync`); **don't** run `MigrateAsync` inside a passive health check. Use `Degraded` for slow-but-serving dependencies.
  - JSON `ResponseWriter` → easier for operators/dashboards; optional `HealthChecks.UI` for a local dashboard (`AspNetCore.HealthChecks.UI` + `UI.InMemoryStorage` + `UI.Client`).

### Backup / restore (MariaDB + app)

- **Logical** (`mariadb-dump`, ≤10-50GB, portable, reviewable) — recommended default for this app size:
  ```bash
  # /usr/local/sbin/smeacct-backup.sh  (cron: 15 3 * * *)
  #!/usr/bin/env bash
  set -euo pipefail; umask 077
  BACKUP_DIR=/srv/backups/smeacct; DB=smeacct
  CREDS=/etc/smeacct-db-backup.cnf          # mode 600, [client] user=backup password=***
  STAMP=$(date +%F); TMP=$(mktemp --suffix=.sql.gz "$BACKUP_DIR/.$DB-$STAMP.XXXXXX")
  install -d -m 700 -o smeacct "$BACKUP_DIR"
  mariadb-dump --defaults-extra-file="$CREDS" \
      --single-transaction --routines --triggers --events --hex-blob "$DB" \
      | gzip > "$TMP"
  mv -f "$TMP" "$BACKUP_DIR/$DB-$STAMP.sql.gz"               # atomic publish, no partial file
  find "$BACKUP_DIR" -name "$DB-*.sql.gz" -mtime +14 -delete # retention
  # optional: push gzip to offsite (rsync/scp/S3-compatible)
  ```
  - Backup user needs `SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER` (+`PROCESS, RELOAD` for `--single-transaction` on some versions); use `.my.cnf`/`--defaults-extra-file` (mode 600) — **never** password on the command line (`ps` exposure).
  - **Restore** (do NOT pipe into live DB): `gunzip -c backup.sql.gz | mariadb -e "CREATE DATABASE smeacct_restored" && mariadb smeacct_restored < dump` → verify `SHOW TABLES; SELECT COUNT(*)` → swap.
  - **Test restores quarterly** (RTO/RPO drill) — "backup you can't restore isn't a backup." 3-2-1 rule; keep an offsite copy.
  - >10-50GB / tighter RPO: `mariabackup --backup/--prepare/--copy-back` hot physical snapshots + **binary logs** (`log_bin`, `binlog_format=ROW`, `expire_logs_days=21`) for point-in-time recovery. Percona XtraBackup is NOT supported on MariaDB; mariabackup replaces it.
- **Application backup** alongside DB: `keys/` (Data Protection keyring)`, `uploads/`, `appsettings.Production.json`, code deploy artifact of the *previous* version (rollback target). Same 3-2-1 and retention policy; document restore runbook in `deploy/`.

### Deployment / publish strategy

- Decision matrix: | mode | cmd | when | runtime required? | roll-forward to latest runtime patch? |
  |---|---|---|---|---|
  | Framework-dependent (FDD) | `dotnet publish -c Release` | **default** for managed host (IIS/Nginx with runtime installed) | yes | yes (auto-rolled) |
  | Self-contained (SCD) | `dotnet publish -c Release -r linux-x64 --self-contained true` | pin exact runtime band / host without runtime | no | no |
  | Single-file | add `-p:PublishSingleFile=true` | console/lambda-like; startup extracts | no | no |
  | Native AOT | `-p:PublishAot=true` | ultra-fast startup, size Q: AOT-unsafe reflection; **avoid for MediatR/FluentValidation/EF reflection-heavy stack** | no | no |
  | ReadyToRun | `-p:PublishReadyToRun=true` | optional cold-start win (measured) | either | either |
  | Container | `-t:PublishContainer` | when Docker-based deploy | image | base-image bump |
  - **Recommendation for this project** (single on-premise vps/IIS): publish **FDD per-RID** (`-r linux-x64` or `win-x64`) unless the customer box can't get the .NET 10 runtime (then SCD). Install the Hosting Bundle on Windows servers.
- **Publish profiles** (`.pubxml`, e.g. `Properties/PublishProfiles/linux-x64.pubxml`): encode `RuntimeIdentifier=linux-x64`, `SelfContained=false`, `PublishReadyToRun=false`, output path → CI calls `dotnet publish -p:PublishProfile=...`. Add FOLDER publish targets for both Windows and Linux from one solution.
- **Zero-downtime Linux upgrade path** (no k8s needed — simple release swap):
  1. migrate first (idempotent SQL or bundle), 2. rsync new build to `/srv/sme-acct/releases/{sha}`, 3. `ln -sfn releases/{sha} current`, 4. `systemctl restart sme-acct` (or `kill -HUP` on the dotnet just to reload — no, full restart required for assembly updates), 5. smoke test `/health/ready`. Keep previous symlink for instant rollback. Windows: IIS **Overlapped Recycle** + Web Deploy; app pool recycling keeps sessions (only if Data Protection key ring persisted). Blue-green via two app pools.
- **Upgrade path (framework)**: run EF migration script before flipping binaries; keep one release artifact = code + expected schema version; never auto-migrate on app start in production ({Multi-instance}) — migrate explicitly in deploy step.

### EF Core migrations + seed (MariaDB)

- Reconfirm Researcher 2's 4 strategies; extend with in-PR on-premise flow: **CI generates `--idempotent` SQL script + migration bundle artifact** (see workflow above); deploy = run bundle/SQL → start app. EF 9+ throws `PendingModelChangeException` on model-migration mismatch — catch in CI (`dotnet ef migrations has-pending-model-changes`).
- **Separate Migrations project**: keep `SmeAccounting.Infrastructure` clean; design-time factory (`IDesignTimeDbContextFactory`) wired to MariaDB via Pomelo (explicit `MariaDbServerVersion`) so tooling + bundles work headless.
- **Seed strategy — two mechanisms, different purposes**:
  - **`UseSeeding`/`UseAsyncSeeding`** (EF 9+, recommended general seeder) — runs on `Migrate()`/`EnsureCreated()`/CLI `database update`; lock-protected; must be idempotent (existence-check first); **implement BOTH overloads** (CLI calls sync, runtime calls async). Use for: Circular 133 COA seed (needs FKs/graph inserts), default roles (Admin/ChiefAccountant/Accountant/Viewer/Auditor), default admin user (hashed password), demo/`Development`-only data, FS template rows that depend on DB state.
  - **`HasData` (renamed "model-managed data")** — small, fixed, deterministic reference with hard-coded keys that get `InsertData`/`UpdateData`/`DeleteData` baked into migrations. Use for: iso currency rows, voucher-template lookup codes. Do **not** use for password-hashed users, GUID/time-dependent data, or anything a customer edits in production (a later code edit becomes a destructive migration).
  - **Gotcha**: removing a `HasData` block generates `DeleteData` in the next migration — dangerous on already-seeded prod; edit the migration to drop `DeleteData` (option B) if FKs point at the seed.
  - Production seeding should be a one-shot deploy step (bundle executes it), not app-start seeding (avoids write-permission + concurrency needs).

### .NET 10 / ASP.NET Core 10 specific notes

- **Minimal API validation is now built-in** (`builder.Services.AddValidation()` + DataAnnotations; `DisableValidation([])` per endpoint; record types supported; ProblemDetails integration). But project already decided MVC for Sneat-compatible admin UI — use MVC views for the accounting UI; minimal API style is available for e.g. health endpoints or a future e-invoice API surface.
- **OpenAPI 3.1** default (`AddOpenApi()`), YAML export (`MapOpenApi("/openapi/v1.yaml", OpenApiFormat.Yaml)`), webhooks — nice for a future e-invoice/e-reporting API.
- **Identity in .NET 10**: passkeys (WebAuthn/FIDO2) built-in `IdentityPasskeyOptions` (primary factor only — attestation not validated); **Identity API endpoints** (`MapIdentityApi<T>` — cookies via `useCookies=true` or **opaque bearer** tokens → NOT JWT, single-app only). Auth **metrics** for sign-ins/challenges/challenges; cookie-auth on API endpoints now returns proper `401`/`403` (no 302 redirect) — simplifies the MVC+API mix.
- **Auth decision for this project** (per cross-cutting requirements): MVC cookie auth + Identity with RBAC (5 standard roles, policy-based authorization, branch-scoped access). Add claims-type safe readers with C# 14 extension members (`ClaimsPrincipalExtensions`). Antiforgery tokens on all state-changing forms (`[ValidateAntiForgeryToken]` / `form tag-helper` auto-antiforgery) — cookie CSRF protection non-negotiable.
- Misc .NET 10 deploy-relevant: `dotnet tool exec`/`dnx` (no need to `dotnet tool install` in CI — use `dotnet tool restore` + `dotnet dnx<...>` in SDK image), `--test-runner MTP` on `dotnet new xunit`, `-a $TARGETARCH` container builds, `.NET 8+` `app`/`APP_UID` user.

### References (new, 2026-verified)

| Topic | Source |
|---|---|
| Container images for .NET 10 (Ubuntu default, chiseled, tags) | [dotnet-docker disc 6801](https://github.com/dotnet/dotnet-docker/discussions/6801), [ubuntu-chiseled.md](https://github.com/dotnet/dotnet-docker/blob/main/documentation/ubuntu-chiseled.md) |
| PublishContainer / containerization reference | [containerization reference](https://learn.microsoft.com/dotnet/core/containers/), `dotnet publish` docs |
| Framework-dependent vs self-contained vs AOT (image math) | [startdebugging.net 2026-09](https://startdebugging.net/2026/09/framework-dependent-vs-self-contained-vs-native-aot-for-a-dotnet-11-container-image/) |
| .NET host & deploy overview / publish modes | [learn.microsoft.com aspnet core host-and-deploy](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/?view=aspnetcore-10.0), [.NET application publishing overview](https://learn.microsoft.com/en-us/dotnet/core/deploying/) |
| Kestrel reverse-proxy guidance, ForwardedHeaders | [when-to-use-a-reverse-proxy](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/servers/kestrel/when-to-use-a-reverse-proxy?view=aspnetcore-10.0), [proxy-load-balancer](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/proxy-load-balancer), [anthonysimmon guide](https://anthonysimmon.com/securely-reverse-proxy-aspnet-core-web-apps/) |
| Caddy auto-HTTPS reverse proxy | [caddy.guide reverse_proxy](https://caddy.guide/docs/caddyfile/directives/reverse_proxy), [Nginx vs Caddy vs Traefik 2026](https://anhtu.dev/nginx-vs-caddy-vs-traefik-picking-the-right-reverse-proxy-for-2026-1105) |
| Serilog two-stage bootstrap / sinks config | [serilog-aspnetcore repo](https://github.com/serilog/serilog-aspnetcore), [AnhTu structured logging .NET 10](https://anhtu.dev/structured-logging-serilog-dotnet-10-message-template-correlation-id-seq-production-2026-2178), [codewithmukesh Serilog .NET 10](https://codewithmukesh.com/blog/structured-logging-with-serilog-in-aspnet-core/) |
| HealthChecks in ASP.NET Core 10 (official docs) | [health-checks docs](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks?view=aspnetcore-10.0) |
| AspNetCore.HealthChecks.MySql 9.0.0 (ping probe) | [nuget.org](https://www.nuget.org/packages/AspNetCore.HealthChecks.MySql) |
| MariaDB backup/restore (mariadb-dump, mariabackup, 3-2-1) | [mariadb-dump docs](https://mariadb.com/docs/server/clients-and-utilities/backup-restore-and-import-clients/mariadb-dump), [backup overview](https://mariadb.com/docs/server/server-usage/backup-and-restore/backup-and-restore-overview), [automate cron backups](https://www.simplified.guide/mysql-mariadb/database-backup-automate-cron) |
| GitHub Actions .NET template / setup-dotnet | [Building and testing .NET](https://docs.github.com/en/actions/tutorials/build-and-test-code/net), [actions/setup-dotnet](https://github.com/actions/setup-dotnet) |
| MariaDB healthcheck.sh | [mariadb.com docs](https://mariadb.com/docs/server/server-management/automated-mariadb-deployment-and-administration/docker-and-mariadb/using-healthcheck-sh) |
| CPM (Directory.Packages.props) | [learn.microsoft.com CPM](https://learn.microsoft.com/en-us/nuget/consume-packages/central-package-management), [migrate-to-CPM 2026](https://startdebugging.net/2026/08/migrate-a-dotnet-solution-to-central-package-management-with-directory-packages-props/) |
| Directory.Build.props/.targets organization | [dotnet/skills directory-build-organization](https://github.com/dotnet/skills/blob/main/plugins/dotnet-msbuild/skills/directory-build-organization/SKILL.md) |
| Data Protection keys (file system, DPAPI, IIS persistence) | [key-storage-providers docs](https://learn.microsoft.com/en-us/aspnet/core/security/data-protection/implementation/key-storage-providers?view=aspnetcore-9.0), [key encryption at rest](https://learn.microsoft.com/en-us/aspnet/core/security/data-protection/implementation/key-encryption-at-rest), [persist keys on IIS](https://www.aspnix.com/posts/persist-data-protection-keys-for-aspnet-core-on-iis) |
| EF Core data seeding (UseSeeding vs HasData) | [learn.microsoft.com data-seeding](https://learn.microsoft.com/en-us/ef/core/modeling/data-seeding), [HasData vs UseSeeding 2026](https://startdebugging.net/2026/06/hasdata-vs-useseeding-for-seeding-data-in-ef-core-11/) |
| .NET 10 ASP.NET Core release notes (validation, passkeys, metrics, cookie auth) | [What's new in ASP.NET Core .NET 10](https://learn.microsoft.com/en-us/aspnet/core/release-notes/aspnetcore-10.0?view=aspnetcore-10.0) |

### Synthesis / recommendations for executor

1. Create solution as `.slnx` + `global.json` + `Directory.Build.props` (nullable/warnings-as-errors/treat) + `Directory.Packages.props` (CPM) + `NuGet.config` (single source, mapped). Lay out `src/`, `tests/`, `docs/`, `scripts/`, `deploy/` per above.
2. CI: one workflow — restore `--locked-mode` → build → `dotnet test` (MTP, xUnit v3) → integration tests against `mariadb:11.4` service → generate migration bundle + `--idempotent` SQL as artifacts → (main only) `PublishContainer`.
3. Docker: 3-stage Dockerfile → `aspnet:10.0-noble-chiseled`, non-root, `HEALTHCHECK`/compose-level, pin version tags; compose = app + mariadb w/ `utf8mb4_unicode_ci` command args + healthchecks + volumes for keyring/uploads.
4. Deploy package: FDD `linux-x64`/`win-x64` publish profiles; systemd `EnvironmentFile` for secrets; Nginx (LAN/self-signed) or Caddy (public domain auto-TLS); ForwardedHeaders with KnownProxies; Data Protection `PersistKeysToFileSystem` + `SetApplicationName` on Linux/Docker, DPAPI on Windows.
5. Logging: Serilog two-stage bootstrap, `appsettings.json` config, rolling CompactJsonFormatter file (14d/100MB) + Seq in dev, overrides for EF/SQL noise, request-logging with UserId enrichment.
6. Health: `/health/live` (no deps) + `/health/ready` (MySql `SELECT 1` + `AddDbContextCheck` + disk), JSON writer, `RequireHost`.
7. Backup: `scripts/` mariadb-dump cron script (single-transaction, gzip, 14d retention, 0600 creds) + app keyring/uploads backup + quarterly restore drill + documented runbook.
8. Migrations/seeds (Pomelo 9 / EF 9): bundle-first deploy; `UseSeeding`+`UseAsyncSeeding` (both impls, idempotent) for COA/roles/admin; `HasData` only for tiny static lookups; quote Circular 133 COA seed as EFR's `UseSeeding` graph-insert use case.
9. Auth in .NET 10: cookie Identity (not `MapIdentityApi`) for MVC; 401-vs-redirect behavior now correct for mixed UI+API; C#14 claims extension members; passkeys future-rama (MVP uses passwords).

## Task-Specific Research — Task 1 [G1] — Solution Skeleton & Build Conventions

> Researcher 6. Verified locally against installed SDK + 2026-09 web sources. Everything here was checked on the actual machine (SDK 10.0.401) unless marked [web].

### 1. Installed SDK / runtime (verified locally)

- **SDK: `10.0.401`** (only one installed — `/root/.dotnet/sdk/10.0.401`). `dotnet --version` → `10.0.401`. `dotnet --list-sdks` → exactly one entry.
- global.json must pin `"version": "10.0.401"` + `"rollForward": "latestFeature"` (matches installed band; CI `10.0.x` resolves here).
- Runtime band: .NET 10 latest patch shipping in 10.0.401 (build works against net10.0 — see §3).

### 2. `dotnet new sln` — slnx confirmed (verified locally)

- Command: `dotnet new sln -n TestSln` → produces **`TestSln.slnx`** by default (SDK 10 default). `-f|--format sln|slnx` exists to override. Default: `slnx`.
- **Exact slnx XML format** (bare template output):
  ```xml
  <Solution>
  </Solution>
  ```
  After `dotnet sln TestSln.slnx add Foo/Foo.csproj`:
  ```xml
  <Solution>
    <Project Path="Foo/Foo.csproj" />
  </Solution>
  ```
  Folder grouping (for src/ tests/ org) uses nested `<Folder Name="/src/">` container. `dotnet sln SmeAccounting.slnx list` works and lists every project.
- All project references via `dotnet sln SmeAccounting.slnx add` — no `{GUID}` noise, clean diffs.

### 3. TFMs / LangVersion (verified locally + [web])

- `net10.0` is the only framework option in the SDK 10 templates (`dotnet new xunit -f net10.0` default) — **confirmed builds**: `dotnet build` of a net10.0 classlib succeeded on this box.
- **C# 14 is the default LangVersion for net10.0** (automatically, no `<LangVersion>` needed). [web] `latest` = installed-compiler-latest → non-reproducible across machines; MS docs actively warn against `latest` and recommend omitting for net10.0 (default C# 14) or pinning `14.0`. Plan asks for `LangVersion latest`: **recommend override to `14.0`** for reproducibility (same value today, stable tomorrow).
- C# 14 extension members (claims reads, MEMORY line) available on net10.0 — confirmed supported.

### 4. `dotnet new xunit --test-runner MTP` — **NOT available in SDK 10.0.401**

- Verified locally: `dotnet new xunit --test-runner MTP` → `Error: Invalid option(s): --test-runner`. The `--test-runner` flag does **not** exist on `dotnet new` in this SDK (neither on `xunit` nor `classlib`). The built-in `xunit` template produces **xUnit 2.9.3 + VSTest** (Microsoft.NET.Test.Sdk 17.14.1 + xunit.runner.visualstudio 3.1.4 + coverlet.collector 6.0.4) — NOT xUnit v3/MTP.
- Correct .NET 10 native-MTP path [web — devblogs "dotnet test with MTP", xunit.net MTP docs, rufer.be HOWTO]:
  1. **global.json**: `"test": { "runner": "Microsoft.Testing.Platform" }` (this is what replaces `--test-runner MTP`).
  2. Test project: `xunit.v3` package + `<OutputType>Exe</OutputType>` (MTP tests are self-executing apps). Run with `dotnet test` (no `--` separator; xUnit filter flags differ from VSTest — `--filter-class/--filter-method/--filter-trait/--filter-query`, not `--filter`).
- Alternative: `dotnet new install xunit.v3.templates` → `dotnet new xunit3` (generates the MTP-ready csproj + global.json). [web]
- **MTP restriction**: with native MTP enabled via global.json, **every** test project in the solution must be MTP (no mixed VSTest+MTP) — applies to Task 1's 6 test projects.
- Suggested test-project csproj shape (from .NET 10 MTP migration):
  ```xml
  <Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
      <TargetFramework>net10.0</TargetFramework>
      <OutputType>Exe</OutputType>
      <IsPackable>false</IsPackable>
    </PropertyGroup>
    <ItemGroup>
      <PackageReference Include="xunit.v3" />
      <!-- optional: Microsoft.Testing.Extensions.CodeCoverage 18.10.0 / TrxReport 2.3.3 / coverlet.MTP 10.0.1 -->
    </ItemGroup>
  </Project>
  ```
- `dotnet test --test-runner MTP` on the *command line* is replaced by native MTP mode (global.json), so CI invocation becomes plain `dotnet test` (plan text "`dotnet test --test-runner MTP`" should be updated to native MTP — or keep the flag, which still works? **No**: with native mode, extra args like `--test-runner` are forwarded differently; safest is native mode + plain `dotnet test`).

### 5. Converted-to-CPM package versions (latest stable, verified 2026-09)

| Package | Version | Verified | Notes |
|---|---|---|---|
| **MediatR** | **12.5.0** ⚠️ | 2026-07-02 | **LICENSE CONFLICT** — v13.0.0+ (2025-07-02) moved to dual RPL-1.5/commercial (Lucky Penny Software); latest 14.2.0 requires license key (`MEDIATR_LICENSE_KEY` env / `cfg.LicenseKey`; runtime = log warning only). **12.5.0 is the last Apache-2.0 release**, API-compatible with plan's 12.4.1. Executor: pin 12.5.0 for foundation (OSS), note decision for later (14.2.0 + Community license if >$5M revenue). |
| FluentValidation | 12.1.1 | 2025-12-03 | Apache-2.0; net8.0+ min |
| FluentValidation.DependencyInjectionExtensions | 12.1.1 | 2025-12-03 | matches core |
| Pomelo.EntityFrameworkCore.MySql | **9.0.0** | locked | EF Core 9.x; depends on MySqlConnector (auto) |
| Serilog.AspNetCore | **10.0.0** | 2025-11-28 | bundles Serilog core + Console + File + Settings.Configuration; version tracks Hosting (10.x = net10 build) |
| Serilog.Sinks.Seq | 9.0.0 | [web R5] | dev-only sink |
| Serilog.Sinks.Async | 1.5.0 (latest stable) | [web R5 note] | prod file-write async |
| Serilog.Formatting.Compact | 2.0.0 | (bundled dep of AspNetCore) | CompactJsonFormatter |
| Serilog.Enrichers.Environment | 3.0.1 (latest) | [web R5 note] | WithMachineName |
| Serilog.Enrichers.Thread / Process | 3.1.0 (latest) | [web R5 note] | |
| Serilog.Exceptions | 8.4.0 (latest) | [web R5 note] | WithExceptionDetails |
| xunit.v3 | **4.0.0** | 2026-08-14 | pulls xunit.v3.mtp-v2 + xunit.v3.assert + xunit.analyzers 2.0.0. Conservative alt: 3.2.2. |
| NSubstitute | **6.2.0** | 2026-08-11 | net8.0/ns2.0; Analyzers package optional (`NSubstitute.Analyzers.CSharp`) |
| AwesomeAssertions | **9.6.0** | 2026-08-20 | Apache-2.0 FluentAssertions fork; namespace `AwesomeAssertions` (NOT FluentAssertions — Task 6 uses its `.Should()`) |
| NetArchTest.Rules | **1.3.2** | 2021-05-23 | dev-dormant, latest confirmed; MIT |
| Microsoft.AspNetCore.Mvc.Testing | **10.0.11** | 2026-08-11 | net10.0 band latest stable (11.0 previews exist — skip) |
| Testcontainers.MariaDb | **4.15.0** (alt 4.14.0) | 2026-09-06 | 4.15.0 brand-new; 4.14.0 battle-tested — executor may pin 4.14.0 |
| Testcontainers.XunitV3 | **4.15.0** | 2026-09-06 | depends `xunit.v3.ext.core >= 3.2.0` → OK with xunit.v3 4.0.0 |
| Respawn | **7.0.0** | 2025-11-30 | .NET 10 tests, infer DbAdapter from connection; MariaDB/MySql supported |
| AspNetCore.HealthChecks.MySql | **9.0.0** | locked | Xabaril; `healthQuery: "SELECT 1;"` for classic ping |
| Microsoft.Extensions.Diagnostics.HealthChecks.EntityFrameworkCore | 10.0.x | [web R5] | for `AddDbContextCheck` |

Executor should resolve exact pins for Serilog enricher family at restore if any version above differs from latest (all are stable-latest as of research).

### 6. CPM (Central Package Management) exact syntax [web — MS CPM docs + verified]

- **Directory.Packages.props** (repo root):
  ```xml
  <Project>
    <PropertyGroup>
      <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
      <CentralPackageTransitivePinningEnabled>true</CentralPackageTransitivePinningEnabled>
    </PropertyGroup>
    <ItemGroup>
      <PackageVersion Include="MediatR" Version="12.5.0" />
      <PackageVersion Include="Pomelo.EntityFrameworkCore.MySql" Version="9.0.0" />
      <!-- ... -->
      <GlobalPackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers" Version="10.0.0" />
    </ItemGroup>
  </Project>
  ```
- Projects carry **versionless** `<PackageReference Include="MediatR" />`. `VersionOverride` attribute on a PackageReference overrides central version *when* `CentralPackageVersionOverrideEnabled` = true (default true) — executor keeps default unless plan wants drift impossible.
- **`CentralPackageTransitivePinningEnabled=true`** — verified [web]: lifts vulnerable/critical transitive deps to top-level automatically. **No downgrade allowed** (NU1109). Trivial: any transitive package added as `<PackageVersion>` gets pinned solution-wide, detected during `dotnet restore`.
- `ManagePackageVersionsCentrally` can live in Directory.Build.props OR Directory.Packages.props; canonical NuGet guidance = Directory.Packages.props. SDK 10 `dotnet package add/update` edits Directory.Packages.props automatically (is CPM-aware).
- Pitfall re-affirmed: do NOT put `<PackageVersion>` items in Directory.Build.props expecting CPM to read them — CPM reads only `Directory.Packages.props` files for central versions (transitive-pinning docs show Directory.Build.props usage as an override trick, not canonical).

### 7. NuGet.config — source mapping syntax [web — MS package-source-mapping + verified template]

- `dotnet new nugetconfig` emits a **lowercase `nuget.config`** file (GitHub-style name) — repo-root canonical name is `NuGet.config` (case-insensitive resolution; keep `NuGet.config` for MS guidance).
  Template content:
  ```xml
  <?xml version="1.0" encoding="utf-8"?>
  <configuration>
    <packageSources>
      <clear />
      <add key="nuget" value="https://api.nuget.org/v3/index.json" />
    </packageSources>
  </configuration>
  ```
- Single-source + mapping (dependency-confusion defense — plan requirement):
  ```xml
  <configuration>
    <packageSources>
      <clear />
      <add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
    </packageSources>
    <packageSourceMapping>
      <packageSource key="nuget.org">
        <package pattern="*" />
      </packageSource>
    </packageSourceMapping>
  </configuration>
  ```
- Rules: `pattern` = prefix (ends `*`, `*` = catch-all default source) or exact ID. Most-specific match wins. **Mapping is exhaustive**: every package (direct AND transitive) must match a pattern or restore fails (NU1107/NU1108) — with only nuget.org + `*` this is trivially satisfied.
- Optional hardening: repo-local `globalPackagesFolder` via `<config><add key="globalPackagesFolder" value="..." />` so mapping is never bypassed via a pre-populated global cache. Not required for Task 1; flag for CI task.

### 8. MSBuild evaluation-order / props-targets split (re-affirmed for plan)

- Order: `Directory.Build.props` → SDK `.props` → `csproj` → SDK `.targets` → `Directory.Build.targets`.
- TFM is **empty during `.props` evaluation** on single-TFM projects → `$(TargetFramework)` conditions in `.props` silently no-op. The plan's rule is correct: properties/items defaults in `.props`; TFM-conditioned `<Target>`/late logic in `.targets`.
- net10.0 is single-TFM everywhere so `Directory.Build.targets` stays nearly empty (placeholder for future cross-TFM).
- **Artifacts path**: `--artifacts-path artifacts` works per-invocation; to make it default for all projects put in Directory.Build.props:
  ```xml
  <PropertyGroup>
    <UseArtifactsOutput>true</UseArtifactsOutput>
    <ArtifactsPath>$(MSBuildThisFileDirectory)artifacts</ArtifactsPath>
  </PropertyGroup>
  ```
  (SDK 8+ built-in; verified mechanism, value string must be absolute — `$(MSBuildThisFileDirectory)artifacts` gives repo-root-absolute.)
- Restore-lock: `dotnet restore --use-lock-file` once → commit `packages.lock.json` everywhere; then `dotnet restore --locked-mode` (fails if lock is stale). Plan's Task-1 verify `dotnet restore --locked-mode` exits 0 is viable. (Potential gotcha: with MTP native-mode global.json at root, restore from a subfolder still resolves)

### 9. PackageReference graph constraint (compiler-enforced)

- Plan: Domain/SharedKernel → zero packages; Application → Domain+SharedKernel; Infrastructure → Application+Domain+SharedKernel; Api → Application+Infrastructure; test projects → their target only.
- Enforcement: csproj ProjectReference-only (verified `dotnet build` refuses undeclared references); NetArchTest check arrives Task 6. Domain/SharedKernel must hold **zero** `<PackageReference>` (not even analyzers — `GlobalPackageReference` is applied to all projects via Directory.Packages.props unless excluded: exclude via `<GlobalPackageReference Remove="..." Condition="'$(MSBuildProjectName)'=='SmeAccounting.Domain'" />` if NetAnalyzers must skip those layers — recommend keeping analyzers on Domain for quality, they're compile-time only, no runtime/dependency leak into Domain's assembly graph. Semantics: GlobalPackageReference adds the analyzer to the project build but does NOT grow the assembly references of Domain — no EFCore/MediatR leak into Domain output).
- Verify with `dotnet sln SmeAccounting.slnx list` + grep of each csproj for `<ProjectReference`/`<PackageReference`.

### 10. Decisions & flags for executor

1. **MediatR license**: pin **12.5.0** (last Apache-2.0) — API same as plan's 12.4.1. Rationale: foundation must be OSS-clean for commercial on-premise resale; upgrade to 14.2.0+ tail-later via a single CPM line bump if/when Community license obtained. This is a deviation from "latest" that Task 1 must record.
2. **MTP**: global.json gets `"test": { "runner": "Microsoft.Testing.Platform" }`; test projects = xunit.v3 + `<OutputType>Exe</OutputType>`. The plan's `dotnet new xunit --test-runner MTP` is **not possible** on SDK 10.0.401 — executor writes csproj manually (or installs xunit.v3.templates). CI `--test-runner MTP` args replaced by native MTP.
3. **LangVersion**: use `14.0` (not `latest`) for reproducibility (net10.0 defaults to C#14 anyway).
4. **global.json** both keys: `sdk` (`10.0.401` + latestFeature) AND `test.runner`. Add `allowPrerelease:false` unless needed.
5. **AspNetCore.HealthChecks.MySql 9.0.0** stays (locked per R5) even though Xabaril 9.0 predates .NET 10 — compatible net8.0 min.
6. **Testcontainers** version: pin one constant e.g. 4.14.0 or 4.15.0 for both MariaDb + XunitV3 + (Task 6 adds core). 4.15.0 is 5 days old — recommend 4.14.0 for stability, then bump in CI task.

### 11. References (Task-1 specific)

| Topic | Source |
|---|---|
| MTP native mode .NET 10 (global.json test.runner) | [learn.microsoft.com migrating to MTP](https://learn.microsoft.com/en-us/dotnet/core/testing/migrating-vstest-microsoft-testing-platform), [devblogs dotnet-test-with-mtp](https://devblogs.microsoft.com/dotnet/dotnet-test-with-mtp/) |
| xUnit v3 + MTP (package selection, OutputType Exe) | [xunit.net MTP getting-started](https://xunit.net/docs/getting-started/v3/microsoft-testing-platform), [rufer.be migration HOWTO](https://blog.rufer.be/2026/08/20/howto-successfully-migrate-a-net-10-test-project-from-vstest-to-microsoft-testing-platform-mtp/) |
| xUnit v3 4.0.0 release | [xunit.net releases](https://xunit.net/releases/) |
| CPM + transitive pinning | [learn.microsoft.com CPM](https://learn.microsoft.com/en-us/nuget/consume-packages/central-package-management) |
| MediatR license change | [jbogard announce](https://www.jimmybogard.com/automapper-and-mediatr-commercial-editions-launch-today/), [MediatR repo](https://github.com/LuckyPennySoftware/MediatR) |
| Package source mapping | [learn.microsoft.com package-source-mapping](https://learn.microsoft.com/en-us/nuget/consume-packages/package-source-mapping) |
| C# 14 default LangVersion | [learn.microsoft.com language-versioning](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/language-versioning) |
| slnx format | CLI-verified locally; [dotnet-new-sdk-templates](https://github.com/dotnet/docs/blob/main/docs/core/tools/dotnet-new-sdk-templates.md) |
| Testcontainers 4.15.0 releases | [testcontainers-dotnet releases](https://github.com/testcontainers/testcontainers-dotnet/releases) |

### 12. Package pins — direct nuget.org flatcontainer verification (Researcher 7, queried 2026-09-11)

All versions below re-verified live against `https://api.nuget.org/v3-flatcontainer/{id}/index.json` (latest *stable*, prerelease excluded). **Deltas vs Researcher 6 are flagged** — executor should take these as the pins.

| Package | Latest stable (nuget 2026-09-11) | Change vs R6 | Pin for Task 1 |
|---|---|---|---|
| MediatR | 14.2.0 | — | **12.5.0** (last Apache-2.0; see license note) |
| FluentValidation | 12.1.1 | none | 12.1.1 |
| FluentValidation.DependencyInjectionExtensions | 12.1.1 | none | 12.1.1 |
| Pomelo.EntityFrameworkCore.MySql | 9.0.0 | none (locked) | 9.0.0 |
| Serilog.AspNetCore | 10.0.0 | none (19.0.1 is -dev) | 10.0.0 |
| Serilog.Sinks.Seq | **9.1.0** | ⚠ R6 said 9.0.0 | 9.1.0 |
| Serilog.Sinks.Async | **2.1.0** | ⚠ R6 said 1.5.0 | 2.1.0 |
| Serilog.Formatting.Compact | **3.0.0** | ⚠ R6 said 2.0.0 | 3.0.0 |
| Serilog.Enrichers.Environment | 3.0.1 | none | 3.0.1 |
| Serilog.Enrichers.Thread | **4.0.0** | ⚠ R6 said 3.1.0 | 4.0.0 |
| Serilog.Enrichers.Process | **3.0.0** | ⚠ R6 said 3.1.0 (does 3.1.0 not exist) | 3.0.0 |
| Serilog.Exceptions | 8.4.0 | none | 8.4.0 |
| xunit.v3 | 4.0.0 | none | 4.0.0 |
| NSubstitute | 6.2.0 | none | 6.2.0 |
| AwesomeAssertions | 9.6.0 | none | 9.6.0 |
| NetArchTest.Rules | 1.3.2 | none (14 versions, dormant) | 1.3.2 pinned |
| Microsoft.AspNetCore.Mvc.Testing | **10.0.12** | ⚠ R6 said 10.0.11 | 10.0.12 |
| Testcontainers.MariaDb | 4.15.0 | none | 4.15.0 (or 4.14.0 per R6 stability rec) |
| Testcontainers.XunitV3 | 4.15.0 | none | same constant as MariaDb |
| Respawn | 7.0.0 | none | 7.0.0 |
| AspNetCore.HealthChecks.MySql | 9.0.0 | none (locked) | 9.0.0 |
| Microsoft.Extensions.Diagnostics.HealthChecks.EntityFrameworkCore | **10.0.12** | ⚠ R6 left unpinned | 10.0.12 |
| Microsoft.Extensions.Diagnostics.HealthChecks | 10.0.12 | (new entry) | 10.0.12 |

**MediatR license re-confirmed [web]**: v13.0.0 (2025-07-02) moved to dual **RPL-1.5 / Lucky Penny commercial** ("Requiring license key" in release notes; `cfg.LicenseKey = ...`). FAQ: earlier versions remain under their original Apache-2.0/MIT. **12.5.0 = last Apache-2.0** — pin it (R6 decision #1 stands; keep Community-license upgrade path documented).

**MTP transitive chain (verified from nuspecs in local package cache)**: `xunit.v3 4.0.0 → xunit.v3.mtp-v2 4.0.0 → xunit.v3.core.mtp-v2 → { Microsoft.Testing.Platform 2.3.3, Microsoft.Testing.Platform.MSBuild 2.3.3, Microsoft.Testing.Extensions.Telemetry 2.3.3, TrxReport.Abstractions 2.3.3, xunit.v3.runner.inproc.console, xunit.v3.extensibility.core }`. ⇒ **No explicit MTP/Testing.Platform PackageReference needed**; don't add them to Directory.Packages.props unless you want transitive-pinning to hard-pin 2.3.3.

### 13. packages.lock.json + CPM + `--locked-mode` — verified locally (Researcher 7)

- Lock files are **per-project** (`packages.lock.json` beside each csproj), format **v2**, entries `Direct`/`Transitive` with `contentHash` (verified content above).
- Flow: `dotnet restore --use-lock-file` once → commit → subsequently `dotnet restore --locked-mode` re-validates. Verified `--locked-mode` exit **0** on a consistent graph.
- **NU1004 drift-gate**: adding/changing *any* PackageReference without regenerating the lock file makes `--locked-mode` FAIL with exit 1: *"The packages lock file is inconsistent with the project dependencies so restore can't be run in locked mode"*. Exactly the Task-1 Verify gate. (Message suggests `--force-evaluate`, but regen via `--use-lock-file` is the committed path.)
- **NU1008**: `<PackageReference Include="X" Version="…" />` (versioned attr) is forbidden under CPM even if the same version appears in Directory.Packages.props.
- **NU1010**: versionless `<PackageReference Include="X" />` with no matching `<PackageVersion Include="X">` in Directory.Packages.props → error. Every referenced package needs a central entry (drop old/reused-only-locally packages to keep the props-file tight).
- **Gotcha**: every project in the `.slnx` must have its lock file committed — adding a project without one fails *that project's* restore under `--locked-mode` (restore continues per-project; solution-level exit reflects the failure).
- No CPM/lock incompatibility with MTP test projects observed: lock files cover the MTP transitive chain fine.

### 14. `--artifacts-path` / `UseArtifactsOutput` — verified locally

- CLI: `dotnet build --artifacts-path <path>` (also accepted by `dotnet restore`) works; it's a global MSBuild property so it **overrides** Directory.Build.props for that invocation (verified: props said `artifacts/`, CLI produced `artifacts2/`).
- Directory.Build.props (make it the default):
  ```xml
  <PropertyGroup>
    <UseArtifactsOutput>true</UseArtifactsOutput>
    <!-- optional — defaults to repo-root 'artifacts' when UseArtifactsOutput=true:
    <ArtifactsPath>$(MSBuildThisFileDirectory)artifacts</ArtifactsPath> -->
  </PropertyGroup>
  ```
  Verified: `UseArtifactsOutput=true` alone (no ArtifactsPath) yields repo-root `artifacts/` — the default is already `$(MSBuildThisFileDirectory)artifacts`. The explicit ArtifactsPath in R6 §8 is fine but redundant.
- Layout: `{ArtifactsPath}/bin/{Project}/{Configuration}/…` and `{ArtifactsPath}/obj/{Project}/{Configuration}/…` (single globally-organized output; verified tree).
- A **relative** CLI path resolves against the working directory of the command (verified: run from repo root → dir created at repo root, not inside the project).
- Works with WTE + latest-recommended analysis; no interference between props-default and CLI-override (subsequent plain `dotnet build` returns to props value).

### 15. .editorconfig for .NET 10 — verified locally + [web]

- SDK 10 ships `dotnet new editorconfig` → 389-line canonical file. Defaults: `indent_style = space`; C# `indent_size = 4`, `tab_width = 4`; XML/JSON/props/targets/slnx `indent_size = 2`; `dotnet_sort_system_directives_first`; `dotnet_separate_import_directive_groups`; **`csharp_style_namespace_declarations = file_scoped:suggestion`** already in the template; **no diagnostic-severity overrides** included.
- **`<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>` is the on/off switch** for IDE style rules at build time. Verified: with it, block-scoped namespace + `file_scoped:error` fails the build with **IDE0161**; without it the same code builds clean (rule is IDE-only). Task-1 requires it (or file-scoped namespaces are cosmetic) — put it in Directory.Build.props.
- Raise the style severity in `.editorconfig`: `csharp_style_namespace_declarations = file_scoped:warning` (or `:error`) if a non-negotiable gate is wanted.
- **CA1716 gotcha** (fires under `AnalysisLevel latest-recommended` + WTE): namespace segment `Lib` is a reserved word → build error. Real Task-1 roots all verified clean: `SmeAccounting.{Domain, Application, Infrastructure, Api, SharedKernel}` build with 0 warnings. Rule of thumb: avoid reserved-word segments (`Lib`, `Module`, `Static`, `Class`, …).
- Task-1 Verify "zero warnings" implications: keep WTE + latest-recommended; add EnforceCodeStyleInBuild; CA1716 only bites exotic namespaces.

### 16. `dotnet new xunit` on SDK 10.0.401 — re-verified

- `dotnet new xunit --help` shows template options only `-f net10.0`, `--enable-pack`, `--no-restore`. **No `--test-runner` option** (R6 correct).
- Default template emits **xUnit 2.9.3 + VSTest**: `Microsoft.NET.Test.Sdk 17.14.1`, `xunit.runner.visualstudio 3.1.4`, `coverlet.collector 6.0.4`, plus `<Using Include="Xunit"/>` and `<IsPackable>false</IsPackable>`.
- **Mixed-mode hard block (verified)**: with native MTP in global.json, `dotnet test Skeleton.slnx` refuses to run ANY project if one uses VSTest:
  > `global.json defines test runner to be Microsoft.Testing.Platform. All projects must use that test runner. The following test projects are using VSTest test runner: LegacyTests.csproj`
  (exit 1). ⇒ **All 6 Task-1 test projects must be xUnit v3 (MTP)**; do not scaffold any with the default template. (The NETSDK1188 locale warnings seen during that mixed build disappear in a pure-MTP graph — 0 in the clean run.)
- Options: hand-write the csproj (§19) or `dotnet new install xunit.v3.templates` → `dotnet new xunit3`.

### 17. global.json — exact syntax verified

```json
{
  "sdk": {
    "version": "10.0.401",
    "rollForward": "latestFeature",
    "allowPrerelease": false
  },
  "test": {
    "runner": "Microsoft.Testing.Platform"
  }
}
```
- Both keys validated live on SDK 10.0.401 (`dotnet --version` → `10.0.401`; `test.runner` honored by `dotnet test`).
- `test.runner` officially available since **.NET 10.0 SDK** [learn.microsoft global-json]; values `VSTest` (default, can be omitted) or `Microsoft.Testing.Platform`. `allowPrerelease` lives under `sdk`, not `test`.
- **MTP-mode `dotnet test` syntax changes** [web — learn.microsoft dotnet-test + migrating-vstest]: solution passed as `--solution`, project as `--project`, dll as `--test-modules <dll>`; `--` separator optional; TRX/reporting requires installing `Microsoft.Testing.Extensions.TrxReport`/CodeCoverage (not auto). **Legacy .NET 8/9 MTP props `TestingPlatformDotnetTestSupport`, `TestingPlatformCaptureOutput`, `TestingPlatformShowTestsFailure` are NO LONGER REQUIRED — do not set them.** Plain `dotnet test` (per R5 CI) is correct.

### 18. Empty project creation: `dotnet new classlib` vs manual csproj — verified

- `dotnet new classlib` emits `<TargetFramework>net10.0</TargetFramework>` + `<ImplicitUsings>enable</ImplicitUsings>` + `<Nullable>enable</Nullable>` **and a Class1.cs to delete**. In a repo where Directory.Build.props already carries all three, this is redundant duplication (both are equivalent at restore/build time).
- Manual empty csproj — the cleanest skeleton here:
  ```xml
  <Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
      <RootNamespace>SmeAccounting.Domain</RootNamespace>
    </PropertyGroup>
  </Project>
  ```
  No TFM/Nullable duplication, no Class1.cs, same enforced dependency graph.
- Recommendation for Task 1: **manual csproj** for all src/ + tests/ projects (reserve `dotnet new classlib` for non-props contexts). Both are equal to `dotnet sln add` (slnx uses `<Project Path>`; verified format earlier).

### 19. xUnit v3 → MTP output: exact required csproj properties — verified against package .targets

From `xunit.v3.core.mtp-v2/4.0.0/buildTransitive/xunit.v3.core.mtp-v2.targets` (authoritative, local):
- **`<OutputType>Exe</OutputType>` REQUIRED** — pkg errors at build if missing: *"xUnit.net v3 test projects must be executable (set project property '<OutputType>Exe</OutputType>')"*.
- **`<UseAppHost>true</UseAppHost>` REQUIRED** for .NETCoreApp — same targets error if `UseAppHost != true` (comes free with Exe; just don't set `UseAppHost=false` anywhere, e.g. publish profiles).
- xunit.v3 **auto-generates the `Main` entry point** into `obj/` (XunitGenerateEntryPoint MSBuild task), defaults PDB `portable`.
- **`UseMicrosoftTestingPlatformRunner`** — optional; only consumed by xunit's entry-point generator (affects the generated Main), defaults to MTP runner. **`MicrosoftTestingPlatformVersion`** — legacy .NET 8/9-era MTP-MSBuild opt-in; grep of MTP.MSBuild 2.3.3 props shows it is gone; **do not set**. The .NET 10 native-mode docs explicitly say the old `TestingPlatform*` properties "are no longer required".
- Minimum battle-tested test csproj (built + ran clean on this machine, 0 warnings):
  ```xml
  <Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
      <OutputType>Exe</OutputType>
      <IsPackable>false</IsPackable>
    </PropertyGroup>
    <ItemGroup>
      <PackageReference Include="xunit.v3" />
      <PackageReference Include="NSubstitute" />
      <PackageReference Include="AwesomeAssertions" />
      <ProjectReference Include="..\..\tests\SmeAccounting.X.Tests\to-target.csproj" />
    </ItemGroup>
    <ItemGroup>
      <Using Include="Xunit" />
    </ItemGroup>
  </Project>
  ```
- **`<Using Include="Xunit" />` required** — xunit.v3 does NOT inject global usings (the default template does; a hand-written csproj must).

### 20. NetArchTest.Rules — re-verified on nuget
1.3.2 is latest (14 versions total; dormant since 2021, MIT, netstandard2.0). Pin stands. Architecture rules land Task 6.

### 21. References (Researcher 7 additions)

| Topic | Source |
|---|---|
| global.json `test.runner` (since .NET 10 SDK) | [learn.microsoft global-json](https://learn.microsoft.com/en-us/dotnet/core/tools/global-json) |
| dotnet test MTP mode / argument mapping / obsolete MTP props | [learn.microsoft dotnet-test](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-test), [migrating-vstest-mtp](https://learn.microsoft.com/en-us/dotnet/core/testing/migrating-vstest-microsoft-testing-platform), [MTP intro](https://learn.microsoft.com/en-us/dotnet/core/testing/microsoft-testing-platform-intro) |
| MediatR 13.0.0 dual license + license key | [MediatR v13.0.0 release](https://github.com/LuckyPennySoftware/MediatR/releases/tag/v13.0.0), [jbogard announce](https://www.jimmybogard.com/automapper-and-mediatr-commercial-editions-launch-today/), [mediatr.io FAQ](https://mediatr.io/) |
| xunit.v3 MTP build requirements | [xunit.net MTP getting-started](https://xunit.net/docs/getting-started/v3/microsoft-testing-platform) |
| CPM error codes (NU1008/NU1010/NU1004) | [learn.microsoft CPM](https://learn.microsoft.com/en-us/nuget/consume-packages/central-package-management) |
| artifacts output layout | [learn.microsoft build-properties / ArtifactsPath](https://learn.microsoft.com/en-us/dotnet/core/project-sdk/msbuild-props#artifactsoutputlayout) |

## Task-Specific Research — Task 2 [G2] — Core Architecture: Clean Architecture + Modular Monolith Kernel

> Researcher 8. Everything below marked **[local]** was verified by compiling/running on this machine (SDK **10.0.401**, net10.0, LangVersion 14.0, CPM pin set from Task 1). Web sources checked 2026-09-11. Plan text referenced as PLAN §Task 2.

### 1. C# 14 extension members — VERIFIED **[local]**

Available at **`LangVersion 14.0`** (no `preview` needed) on SDK 10.0.401. Repo already pins `14.0` in Directory.Build.props — Task 4's `ClaimsPrincipal` extension member will compile as-is. Exact working syntax (compiled + ran, 0 warnings):

```csharp
using System.Security.Claims;

public static class ClaimsPrincipalExtensions
{
    extension (ClaimsPrincipal claims)              // NO access modifier on the block
    {
        public Guid? UserId =>                      // instance member (NOT static)
            claims.FindFirst("sub") is { } c && Guid.TryParse(c.Value, out var id) ? id : null;
        public bool IsRole(string role) => claims.IsInRole(role);
    }
}
// usage: claimsPrincipal.UserId  (instance syntax)
```

Syntax rules proven by compiler errors:
- Block form: `extension (T param) { ... }` inside a `public static class`; declaring modifier on the block is an error (CS0106).
- The receiver param is declared **without** `this` — `extension (this T x)` is an error (`this` not available, CS0027).
- Members that reference the receiver value must be **instance** members; `static` members cannot access the extension parameter (CS9347).
- `static` members *are* allowed in the block but can't read the receiver — for claims the members above are instance.
- Access uses normal `using` scoping of the containing static class (same rule as classic extension methods).

If the executor prefers zero-new-syntax, classic `public static Guid? GetUserId(this ClaimsPrincipal cp)` works identically — but the new-block form is verified available, so Task 4's "C#14 claims extension members" plan line is realisable. Keep `LangVersion 14.0`.

### 2. MediatR 12.5.0 — registration API VERIFIED **[local]**

Test project referenced **only** `<PackageReference Include="MediatR" Version="12.5.0"/>` (+FluentValidation) — `AddMediatR` was not a separate package. **v12 merged DI registration into the main `MediatR` package** (the old `MediatR.Extensions.Microsoft.DependencyInjection` is obsolete). All compiled + ran:

```csharp
services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssembly(typeof(ApplicationMarker).Assembly);
    cfg.RegisterServicesFromAssemblyContaining<ApplicationMarker>();
    cfg.Lifetime = ServiceLifetime.Scoped;
});
```

Facts for the executor:
- `IServiceCollection`/`AddMediatR` resolve **transitively** from MediatR 12.5.0's `Microsoft.Extensions.DependencyInjection.Abstractions` dep — base Application needs only the one `MediatR` PackageReference. (`BuildServiceProvider()` needs the full DI-container package, but that's Api's Web-SDK job / test-project business, not classlib Application.)
- `IPublisher`/`INotification` live in MediatR too — available for the Task-5 domain-event dispatcher without new packages.
- MediatR 12.5.0 is already pinned in Directory.Packages.props (Task 1). No CPM change.
- No `LicenseKey` API in 12.x (that's 13+/14.x) — no license noise.

### 3. FluentValidation 12.1.1 pipeline behaviour — VERIFIED **[local]**

The canonical MediatR `IPipelineBehavior` validation behaviour compiles + runs against FluentValidation 12.1.1:

```csharp
public sealed class ValidationBehaviour<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    private readonly IEnumerable<IValidator<TRequest>> _validators;
    public ValidationBehaviour(IEnumerable<IValidator<TRequest>> validators) => _validators = validators;

    public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        if (_validators.Any())
        {
            var context = new ValidationContext<TRequest>(request);
            var errors = await Task.WhenAll(_validators.Select(v => v.ValidateAsync(context, ct)));
            var failures = errors.SelectMany(r => r.Errors).Where(f => f is not null).ToList();
            if (failures.Count != 0)
                throw new ValidationException(failures);   // ctor(IEnumerable<ValidationFailure>) exists
        }
        return await next();
    }
}
```

Verified specifically:
- `ValidationException(IEnumerable<ValidationFailure>)` ctor present. `ValidationFailure` is in **`FluentValidation.Results`** namespace (needs `using FluentValidation.Results;`).
- `AddValidatorsFromAssembly(asm, ServiceLifetime.Scoped)` + `AddValidatorsFromAssemblyContaining<T>()` from `FluentValidation.DependencyInjectionExtensions` 12.1.1 work, scoped lifetime honored (`GetRequiredService<IValidator<T>>()` returned the scanner-resolved `AbstractValidator`).
- `{PropertyName}` placeholder resolves (test validator produced `"Name ..."` roles from `RuleFor(x => x.Name).NotEmpty().WithMessage("{PropertyName} bắt buộc")`) — vi-VN messages (plan Task 5) work via `WithMessage` + resx.
- The behaviour class should filter **null** failures (`f is not null`) — FluentValidation 12 can yield null entries (Milan's canonical version keeps this guard) — cheaper than a guard-clause pre-check of `request`.

Where it lives (PLAN): base `SmeAccounting.Application`, registered in `AddApplication()`:
```csharp
public static IServiceCollection AddApplication(this IServiceCollection services) => services
    .AddMediatR(cfg => { cfg.RegisterServicesFromAssemblyContaining<ApplicationMarker>(); })
    .AddValidatorsFromAssembly(typeof(ApplicationMarker).Assembly, ServiceLifetime.Scoped)
    .AddTransient(typeof(IPipelineBehavior<,>), typeof(ValidationBehaviour<,>));
```

### 4. MVC structure in Api — VERIFIED **[local]**

`dotnet new mvc` on SDK 10.0.401 generates `Controllers/`, `Views/` (`Home`, `Shared`), `Models/`, `wwwroot/lib/{bootstrap,jquery,jquery-validation}` — MVC template fully present; plan assumption Q4 (MVC over Razor Pages) is sound. .NET 10 MVC Program.cs shape:

```csharp
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllersWithViews();      // MVC (NOT AddRazorPages)

var app = builder.Build();
app.UseExceptionHandler("/Home/Error");           // Production switch — Task 5
app.UseHsts(); app.UseHttpsRedirection(); app.UseRouting(); app.UseAuthorization();
app.MapStaticAssets();                            // .NET 10 replaces UseStaticFiles for app assets
app.MapControllerRoute(name: "default", pattern: "{controller=Home}/{action=Index}/{id?}").WithStaticAssets();
app.Run();
```

Task-2 Program.cs stays top-level statements (current file is already 5-line top-level); executor adds `AddControllersWithViews()` + `AddApplication()` + `AddInfrastructure()` + module registration, scaffolds `Controllers/` + `Views/` (+ `Views/Shared/_ViewImports.cshtml`, `_ViewStart.cshtml`; a trivial `HomeController`/`Index.cshtml` is optional and makes the route smoke-testable). Serilog two-stage bootstrap body stays **Task 5** (Api does **not** take Serilog + other T5 packages yet — Task 2 Api csproj may grow only ProjectReferences, no new packages needed).

Genuine ASP.NET Core 10 note: `MapStaticAssets()` is the recommended static-asset analysis pipeline (supersedes `UseStaticFiles` default wiring); keep it for the Bootsrap/LibMan assets that land in Task 4/5.

### 5. SharedKernel — concrete design (with reasoning)

All of these live in `SmeAccounting.SharedKernel` (zero PackageReference — verified constraint from Task 1, keep it that way). Suggested folder layout: `Primitives/` (BaseEntity, ValueObject, typed markers), `Results/`, `Events/`, `Abstractions/` (providers, persistence contracts).

**BaseEntity** — id + event ledger, no EF awareness:
```csharp
public abstract class BaseEntity
{
    protected BaseEntity() => Id = Guid.NewGuid();
    public Guid Id { get; protected set; }
    private readonly List<IDomainEvent> _domainEvents = [];
    public IReadOnlyCollection<IDomainEvent> DomainEvents => _domainEvents.AsReadOnly();
    protected void RaiseDomainEvent(IDomainEvent @event) => _domainEvents.Add(@event);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
```
Decision: **`Guid` PKs** (`Guid.NewGuid()` on construction, EF `ValueGeneratedOnAdd` fine in Task 3). Typed-ID value objects (kgrzybek-style `EntityInt32Id`) are a deliberate **non-goal at foundation** — over-engineering for one shared-DbContext SME app; revisit only if a module shows real need.

**Capability interfaces** — declared as contracts (concrete entities pick what they implement; avoids C# no-mixin hierarchy wall). This is the plan's "IAuditable/ISoftDeletable/ICompanyScoped" set — **not** EF attributes, persistence-ignorant:
```csharp
public interface IAuditable
{
    DateTime CreatedAtUtc { get; set; }
    Guid? CreatedBy { get; set; }
    DateTime? UpdatedAtUtc { get; set; }
    Guid? UpdatedBy { get; set; }
}
public interface ISoftDeletable
{
    bool IsDeleted { get; set; }
    DateTime? DeletedAtUtc { get; set; }
    Guid? DeletedBy { get; set; }
}
public interface ICompanyScoped
{
    Guid CompanyId { get; set; }        // OQ-2 mitigation: tenant-ready field now, single-tenant MVP
}
```
- Names use the `*AtUtc` suffix choice (matches `IDateTimeProvider.UtcNow`); executor may keep RESEARCH §8's snake names at the DB layer (Task 3 naming decision) — the **C# property names** are what these interfaces fix. The `UpdatedBy`/`DeletedBy` nullable GUid* match `ICurrentUserProvider.UserId` being `Guid?`.
- `CompanyScopedEntity : BaseEntity, ICompanyScoped` optional intermediate for the common case → just add `CompanyId` property; `BaseEntity` itself does **not** implement the capability interfaces (mixins-pragmatism).
- Task 3 applies these via EF model conventions (detect interface implementations) + global query filter `!IsDeleted`.

**ValueObject** — Ardalis-style, with the WTE gotchas pre-flagged:
```csharp
public abstract class ValueObject : IEquatable<ValueObject>
{
    protected abstract IEnumerable<object> GetAtomicValues();
    public override bool Equals(object? obj) => obj is ValueObject other && Equals(other);
    public bool Equals(ValueObject? other) => other is not null && ValuesAreEqual(other);
    private bool ValuesAreEqual(ValueObject other) => GetAtomicValues().SequenceEqual(other.GetAtomicValues());
    public override int GetHashCode() => GetAtomicValues().Aggregate(17, (acc, v) => acc * 31 + (v?.GetHashCode() ?? 0));
    public static bool operator ==(ValueObject a, ValueObject b) => a is null ? b is null : a.Equals(b);
    public static bool operator !=(ValueObject a, ValueObject b) => !(a == b);
}
```
WTE traps: implement `IEquatable<ValueObject>`+`GetHashCode` with `==`/`!=` together (CS0660/CS0661 + CA1815/CA2225 otherwise fail the build under `TreatWarningsAsErrors` + `latest-recommended`). Consider `record`-based value objects instead for most cases (C# records give atomic equality free); keep `ValueObject` base only where behavior/encapsulated invariants demand it. `SmartEnum` — defer (OQ-4/5 outside foundation).

**Result<T>/error types — DECISION: custom in SharedKernel, not Ardalis.Result/FluentResults/ErrorOr.** Plan literally places `Result<T>`/error types in SharedKernel, and SharedKernel must stay zero-package (Task 1 gate) — so **custom, no package**. Milan-2026 style, minimal:
```csharp
public sealed record Error(string Code, string Description)
{
    public static readonly Error None = new(string.Empty, string.Empty);
}
public class Result
{
    protected Result(bool isSuccess, Error error) { IsSuccess = isSuccess; Error = error; }
    public bool IsSuccess { get; }
    public bool IsFailure => !IsSuccess;
    public Error Error { get; }
    public static Result Success() => new(true, Error.None);
    public static Result Failure(Error error) => new(false, error);
    public static implicit operator Result(Error error) => Failure(error);
}
public sealed class Result<T> : Result
{
    private readonly T? _value;
    private Result(T value) : base(true, Error.None) => _value = value;
    private Result(Error e) : base(false, e) => _value = default;
    public T Value => IsSuccess ? _value! : throw new InvalidOperationException("Accessing Value of failed Result");
    public static Result<T> Success(T value) => new(value);
    public static new Result<T> Failure(Error error) => new(error);
    public static implicit operator Result<T>(T value) => Success(value);
    public static implicit operator Result<T>(Error error) => Failure(error);
}
```
Considerations behind the call:
- Ardalis.Result is MIT and battle-tested, but brings `ResultStatus`+HTTP-mapping machinery an MVC app doesn't need, and costs SharedKernel its zero-package property. FluentResults/ErrorOr are heavier ergonomics (sweeping of all `IEnumerable<T>` ctor overloads etc.). None justified for one SME app's foundation.
- **Flow convention to record in docs/architecture.md**: input validation → FluentValidation pipeline throws `ValidationException` (400 ProblemDetails in Task 5); expected business-rule failures → `Result.Failure(Error)`; truly exceptional/unexpected paths → exceptions → 500. Result used by MediatR handlers returning `Result<Something>`/`Result` (`IRequest<TResponse>` no-constraint — verified; `IReturns` untouched), controllers translate to ActionResult/ProblemDetails (Task 5).

**ICurrentUserProvider + IDateTimeProvider — minimal**:
```csharp
public interface ICurrentUserProvider
{
    Guid? UserId { get; }
    bool IsAuthenticated { get; }
}
public interface IDateTimeProvider { DateTime UtcNow { get; } }
```
- No ASP.NET types leak into SharedKernel (pure contract). Rich claim reads (roles/permissions/branches) done via the Task-4 `ClaimsPrincipal` C#14 extension members in the **Api/Infrastructure** HTTP layer, not here.
- `ICurrentUserProvider` impl = `HttpContext.User` (Task 5, or Task 4 auth does it); `IDateTimeProvider` impl = `SystemClock`-style `DateTime.UtcNow` (Infrastructure, Task 5), registered Singleton. Both **Scoped/Singleton** registration noted; EF interceptors in Task 3 may consume both to stamp audit fields.

**IDomainEvent + in-process dispatch seam (foundation, no external bus)**:
```csharp
public interface IDomainEvent { DateTime OccurredAtUtc { get; } }
public interface IDomainEventsDispatcher
{
    Task DispatchAsync(IEnumerable<IDomainEvent> domainEvents, CancellationToken ct = default);
}
```
- `BaseEntity` collects events (`RaiseDomainEvent`/`ClearDomainEvents` above).
- Task 5 implements the dispatcher over **MediatR `IPublisher`** with a generic wrapper notification (`DomainEventNotification<IDomainEvent>` carrying the event; handlers typed `IDomainEventsHandler<TDomainEvent : IDomainEvent>`), i.e. the kgrzybek MediatorModule + Milan dispatcher pattern. Only the **seam interface** is defined now — satisfies "in-process dispatch seam (no external event bus for foundation)". **No outbox** in foundation (Milan: outbox is for cannot-lose side effects; defer).
- Should SharedKernel's `IDomainEvent` implement MediatR `INotification`? **No** — that would drag MediatR into SharedKernel (license + package gate). The wrapper pattern in Application/Infrastructure keeps SharedKernel clean.

**Repository + IUnitOfWork — minimal (avoid over-engineering)**:
```csharp
public interface IUnitOfWork { Task<int> SaveChangesAsync(CancellationToken ct = default); }

public interface IRepository<T> where T : BaseEntity
{
    Task<T?> GetByIdAsync(Guid id, CancellationToken ct = default);
    Task<List<T>> ListAsync(CancellationToken ct = default);
    Task AddAsync(T entity, CancellationToken ct = default);
    void Update(T entity);
    void Remove(T entity);
}
```
- Rationale: EF `DbContext` already *is* repository+UoW; `IUnitOfWork` exists purely so Application/Domain code depends on a contract, not EF. One shared DbContext ⇒ one shared transaction scope (plan constraint §7). **No specification pattern, no `IReadRepository` split, no paged/query-signature inventory at foundation** — those become over-engineering until a real query need exists (plan's own guardrail). Generic repo implementation lands in Infrastructure Task 3.

### 6. Module registration pattern — `IModule` + `AddModule()`

Reference patterns inspected: kgrzybek/modular-monolith-with-ddd real shape = per-module static `{Module}Startup.Initialize(connectionString, ...)` with Autofac modules inside (composition root calls each `Initialize` explicitly — **no reflection scan, no IModule interface**); deadislove/dotnet-ModularMonolith-template and NET-Architecture-Templates/ModularMonolith use an **`IModule` interface + reflection scan** (`services.AddModules()`); Milan Jovanović 2026 guide recommends **explicit registration, no reflection magic**; CodeMaze `IModule` = `RegisterModule(IServiceCollection)` + `MapEndpoints` returns `IEndpointRouteBuilder`.

**Recommendation for this loop (matches PLAN's "IModule + AddModule() extension method", foundation-grade):**

Host `IModule` in **base `SmeAccounting.Application`**, NOT SharedKernel — `IModule` needs `IServiceCollection` (an `Microsoft.Extensions.DependencyInjection.Abstractions` type ⇒ package dep), which fails SharedKernel's zero-package gate. Base Application already gets DI abstractions transitively via MediatR 12.5.0 (verified §2).

```csharp
// SmeAccounting.Application
public interface IModule { IServiceCollection AddModule(IServiceCollection services); }
```
```csharp
// each Modules/{M}/Infrastructure — both the interface impl AND a static extension:
public sealed class IdentityModule : IModule
{
    public IServiceCollection AddModule(IServiceCollection services)
    {
        // Task ≥3: EF entity configs, MediatR handlers for the module, etc.
        services.AddTransient<ISomething, Something>();
        return services;
    }
}
public static class IdentityModuleExtensions
{
    public static IServiceCollection AddIdentityModule(this IServiceCollection services)
        => new IdentityModule().AddModule(services);
}
```
```csharp
// Api — explicit registry loop (compile-safe, greppable, trims clean, no reflection):
public static IServiceCollection AddModules(this IServiceCollection services, IEnumerable<IModule> modules)
{
    foreach (var module in modules) module.AddModule(services);
    return services;
}
// Program.cs:
var modules = new IModule[] { new IdentityModule(), new AuthorizationModule(), /*...all 12...*/ };
builder.Services.AddModules(modules);
```
- 12 modules (PLAN §2A/2D MVP): Identity, Authorization, Organization, MasterData, Audit, ChartOfAccounts, AccountingPeriod, Journal, Posting, GeneralLedger, Tax, FinancialReporting.
- Explicit array beats reflection scan for 12 modules — avoids `Assembly.GetTypes()` surprises, is Locate-able, and keeps trim-safety (irrelevant at foundation but free). Keep `AddModule()` extension name so each module is also individually callable in tests.
- **kgrzybek's `{Module}Startup.Initialize(connectionString,...)` autofac flavor is heavier than foundation needs** — noted, not adopted.

### 7. Project graph for the 12 module triads (36 new projects)

```
src/Modules/{Module}/
  {Module}.Domain/            SmeAccounting.Modules.{Module}.Domain        refs: SmeAccounting.Domain, SmeAccounting.SharedKernel      packages: NONE
  {Module}.Application/       SmeAccounting.Modules.{Module}.Application   refs: + SmeAccounting.Application, + local .Domain            packages: MediatR (explicit, CPM-pinned)
  {Module}.Infrastructure/    SmeAccounting.Modules.{Module}.Infrastructure refs: + local .Application (+ transitives)                    packages: NONE (EF arrives Task 3)
Api                          += ProjectReferences to all 12 × .Infrastructure (module registration loop)
```
- **No module→module ProjectReference** (compiler-enforced — the Task-1 style dependency rule extends to modules; arch tests Task 6).
- Namespace `SmeAccounting.Modules.{Module}.{Layer}` — **verified clean** under CA1716 + `latest-recommended` + WTE + EnforceCodeStyleInBuild **[local test]**: both `Modules` and even singular `Module` segments build 0-warning in repo-equivalent props. (R7's CA1716 finding was specifically segment `Lib`.) Pluralified `Modules` remains the safe convention anyway.
- Module.Domain referencing shared `SmeAccounting.Domain` is intentional: base Domain is the shared-domain-contract anchor and the arithmetic/logic home that has zero deps; module Domains add bounded-context entities. Base Domain's exact contents are executor's call (may stay near-empty now; `CompanyId`-scoped common entities could live there later).
- Api **does not** need MediatR/FluentValidation PackageReferences — `AddApplication()` (in Application assembly) owns registration; Api already references Application+Infrastructure (Task 1 graph). New Api additions are ProjectReferences to the 12 module Infrastructure projects only.
- **CPM/lock impact**: adding PackageReferences (MediatR to 12 module Applications + base Application gets MediatR/FV) trips **NU1004 under `--locked-mode`** until locks regenerate. Step for executor after scaffolding: `dotnet restore --use-lock-file` at solution level → verify `dotnet restore --locked-mode` exit 0 → `git add` all **new** `packages.lock.json` (36 module projects get one each) + the touched ones (Application; Api only if Api project refs changed count as lock-affecting — they don't; PackageReference-only changes do) and commit. Task 1 precedent: every slnx project needs its own committed lock file.
- `.slnx` gains 36 `<Project Path="src/Modules/..."/>` entries; folder auto-grouping keeps `src/` top-level intact (no new Folder elements needed; `dotnet sln add` handles it).
- Keep `Directory.Build.props` untouched (net10.0 etc. applies to all new projects automatically).

### 8. Program.cs (Api) Task-2 skeleton + MVC folders

```csharp
var builder = WebApplication.CreateBuilder(args);   // Task 5 wraps in Serilog two-stage bootstrap (try/catch/finally)

builder.Services.AddControllersWithViews();
builder.Services.AddApplication();                  // MediatR 12.5.0 + FV 12.1.1 pipeline (base Application)
builder.Services.AddInfrastructure();               // providers/DB skeleton (Task 5 real content)
builder.Services.AddModules(new IModule[] { /* 12 module instances */ });

var app = builder.Build();
app.MapStaticAssets();
app.MapControllerRoute(name: "default", pattern: "{controller=Home}/{action=Index}/{id?}").WithStaticAssets();
app.UseAuthorization();                             // requires UseAuthentication; Task 4 wires identity
app.Run();
```
Folders: `Controllers/`, `Views/`, `Views/Shared/` (with `_ViewImports.cshtml` + `_ViewStart.cshtml`). Optional stub `HomeController` + `Views/Home/Index.cshtml` so route mapping is exercised; **no business logic** (plan §16.2 — controllers delegate to MediatR later, none yet).

### 9. Decisions for executor (numbered)

1. **Extension members** — use C#14 block syntax (verified §1) for Task 4 claims; keep `LangVersion 14.0`.
2. **Result** — custom `Error`/`Result`/`Result<T>` in SharedKernel; no Ardalis/ErrorOr/FluentResults package (§5). Record the flow convention (FV throws for input; Result for expected failures; exceptions for exceptional) in docs/architecture.md.
3. **IDs** — `Guid` everywhere incl. `CompanyId`; no typed-ID objects at foundation.
4. **IModule host** — base `SmeAccounting.Application` (DI-abstraction package constraint keeps it out of SharedKernel); explicit 12-module array registration in Api, plus per-module static `Add{Module}Module()` extension (§6).
5. **Capability interfaces** — `IAuditable`/`ISoftDeletable`/`ICompanyScoped` as persistence-ignorant contracts; `BaseEntity` does not implement them; Task 3 EF conventions read them (§5).
6. **Naming** — module namespaces `SmeAccounting.Modules.{Module}.{Layer}` (verified CA1716-clean); module folder paths under `src/Modules/{Module}/{Domain|Application|Infrastructure}/`.
7. **MVC** — `AddControllersWithViews()` + `MapStaticAssets()` + default route; no `AddRazorPages`.
8. **Lock files** — regenerate via `dotnet restore --use-lock-file` after package additions; commit 36 new module lock files; verify `--locked-mode`.
9. **No outbox, no spec pattern, no typed-IDs** at foundation — all flagged as deliberate minimisation (plan's "avoid over-engineering — foundation level").

### 10. Risks / gotchas (Task-2 specific)

- **CS0660/CS0661/CA1815/CA2225** under `TreatWarningsAsErrors` when writing `ValueObject` operators — implement `IEquatable<T>`+`GetHashCode` consistent with `==`/`!=` or the build fails; or prefer C# `record` value objects (§5).
- **NU1004 drift-gate** — first `--locked-mode` build after adding PackageReferences fails; expected, regenerate locks (above).
- **CA2214 (DoNotCallOverridableMethodsInConstructors)** — `BaseEntity` ctor must not call virtual members (can't: `Id = Guid.NewGuid()` is fine); keep event list field init non-virtual.
- **SharedKernel/Domain zero-package re-audit** — adding `MediatR` to module Applications is fine (Application layer); do **not** let any Domain/SharedKernel project acquire a PackageReference (Task 6 NetArchTest re-checks).
- **Module count** = 3×12+5 base+6 tests = 47 projects in the slnx — `dotnet build`/test times grow; normal for this architecture, no action.
- **`ValidationFailure` namespace** — `FluentValidation.Results` (not root) — reference in the behaviour class (§3) or `using FluentValidation.Results;` is the compile fix.

### 11. References (Task 2 additions)

| Topic | Source |
|---|---|
| Domain events dispatcher (in-process, no library; strongly-typed wrapper) | [milanjovanovic.tech building-a-custom-domain-events-dispatcher](https://milanjovanovic.tech/blog/building-a-custom-domain-events-dispatcher-in-dotnet) |
| Modular monolith complete guide 2026 (boundaries, shared kernel, explicit registration) | [milanjovanovic.tech modular-monolith-architecture-dotnet](https://milanjovanovic.tech/blog/modular-monolith-architecture-dotnet) |
| kgrzybek modular monolith primer/integration styles (module→module via events, never project refs) | [kamilgrzybek.com modular-monolith-primer](https://www.kamilgrzybek.com/blog/posts/modular-monolith-primer), [integration-styles](https://www.kamilgrzybek.com/blog/posts/modular-monolith-integration-styles) |
| kgrzybek actual registration shape (per-module `{Module}Startup.Initialize`) | [github.com/kgrzybek/modular-monolith-with-ddd](https://github.com/kgrzybek/modular-monolith-with-ddd) (cloned + inspected) |
| Result pattern (Error record + Result/Result<T>, Milan 2026) | [milanjovanovic.tech functional-error-handling-result-pattern](https://www.milanjovanovic.tech/blog/functional-error-handling-in-dotnet-with-the-result-pattern) |
| Ardalis.Result (rejected: package dep + HTTP-mapping for MVC app) | [github.com/ardalis/Result](https://github.com/ardalis/Result) |
| ErrorOr vs Result comparisons | [antondevtips.com how-to-replace-exceptions-with-result-pattern](https://antondevtips.com/blog/how-to-replace-exceptions-with-result-pattern-in-dotnet) |
| MVC in .NET 10 ([local] `dotnet new mvc` verified) | [aspnetcore-docs view=aspnetcore-10.0](https://learn.microsoft.com/en-us/aspnet/core/?view=aspnetcore-10.0) |
| MediatR 12x DI API ([local] compiled; merged DI in main package) | [github.com/LuckyPennySoftware/MediatR](https://github.com/LuckyPennySoftware/MediatR) |
| FluentValidation 12 ([local] pipeline + `ValidationException`) | [docs.fluentvalidation.net](https://docs.fluentvalidation.net/) |

### 12. Per-module minimal content matrix (Researcher 9, complement to R8 §5-§7)

R8 shipped the module *mechanics* (triad graph, IModule, registration). This subsection fixes what each of the 12 MVP module triads legitimately holds **at foundation** — empty structure, no entities, no fake CRUD, no invented rules. Verified end-to-end in a scratch build (see §17) — graph compiled 0-warning / 0-error, module handler dispatched through the Api-equivalent host.

**Foundation scaffolding per module (the ONLY code allowed in any module triad at Task 2):**
- **Domain**: zero `.cs` files. Namespace `SmeAccounting.Modules.{M}.Domain` reserved; csproj references base `SmeAccounting.Domain` + `SmeAccounting.SharedKernel`. Empty classlib builds 0-warning (Task 1 precedent).
- **Application**: optional single marker `public abstract class {M}ApplicationMarker { }` (recommended — gives `RegisterServicesFromAssemblyContaining<{M}ApplicationMarker>()` a concrete target next task + greppable module identity); zero business types. MediatR PackageReference.
- **Infrastructure**: is the only layer with real scaffold code — `{M}Module : IModule` + static `Add{M}Module()` extension (R8 §6). `AddModule` body currently: `services.AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<{M}ApplicationMarker>())`. No EF, no DbContext, no packages (see §13).

**What each module's Domain is *known* for (identified, NOT designed — boundaries + future ownership only), per RESEARCH §2A/2D/§5/§6:**

| # | Module | Known aggregates/state from accounting domain (NOT designed) | Known boundary facts (no code) | Real content lands |
|---|--------|-----------------------------------------------------------------|--------------------------------|--------------------|
| 1 | Identity | User, Role, UserClaim, UserLogin (ASP.NET Identity types) | Cookie auth, 5 standard roles | Task 4 |
| 2 | Authorization | Permission catalog (`Permissions.*` constants), RolePermission | Policy-based RBAC, branch-scoped access | Task 4 |
| 3 | Organization | Company, Branch, Department | Single company/tenant; branches share COA/currency/fiscal year | Task 3 (Company/Branch per plan) |
| 4 | MasterData | Customer, Vendor, Currency, ExchangeRate | VND mandatory default; daily buy/sell/transfer rates | Task 3 (iso currencies seed only) |
| 5 | Audit | AuditLogEntry (append-only; NOT soft-deleted) | OQ-7 = entity-level before/after snapshot (Task 3); consumes domain events later | Task 3 |
| 6 | ChartOfAccounts | Account (code/name/type/level, hierarchy) | 49 Level-1 (Circular 133); open extension — nothing hardcoded | Task 3 (Account + COA seed) |
| 7 | AccountingPeriod | FiscalYear, AccountingPeriod (Open/Closed) | Closed-period posting lock is a Posting invariant | later |
| 8 | Journal | JournalEntry (+ lines), balance invariant, draft→approved→posted, voucher ref | `SUM(debits)==SUM(credits)` enforced at domain level | later |
| 9 | Posting | posting service; balances **derived, never stored** | Ledger entries immutable; corrections via reversal only | later |
| 10 | GeneralLedger | derived account balances; trial balance; ledger queries | — | later |
| 11 | Tax | tax codes, VAT calc, accounts 133/3331, Form 01/GTGT | VAT 10/5/0/8% rates | later |
| 12 | FinancialReporting | FS templates B01/02/03-DN (regulatory indices, versioned) | 90-day annual FS deadline | later |

**Explicitly NOT scaffolded at foundation:** no entity classes in module Domains, no EF configurations, no commands/queries/validators/handlers, no fake CRUD endpoints, no invented accounting rules. Module Domains stay empty so no premature design leaks into EF (Task 3 owns entity modeling + naming + audit fields per its own verify list).

### 13. Infrastructure split — central `SmeAccounting.Infrastructure` vs 12 module Infrastructures

**DB schema is owned centrally, one shared `SmeAccountingDbContext` in `SmeAccounting.Infrastructure`** (plan Task 3 + MEMORY: "DB schema owned by Infrastructure; migrations `--project Infrastructure --startup-project Api`"). This resolves the "does each module get its own EF-config partial?" question: **no** — module Infrastructures hold zero EF/schema/DbContext code at foundation.

| Concern | Central `SmeAccounting.Infrastructure` | Module `{M}.Infrastructure` |
|---|---|---|
| DbContext + all `IEntityTypeConfiguration<T>` (grouped `Persistence/Configurations/Modules/{M}/` for discoverability) | ✅ | ❌ |
| EF migrations (`InitialCreate` etc.) + `IDesignTimeDbContextFactory` | ✅ | ❌ |
| Seeding (`UseSeeding`/`UseAsyncSeeding`, `HasData`) | ✅ | ❌ |
| `IUnitOfWork` / `IRepository<T>` implementations over the shared DbContext | ✅ (recommended — module Infra stays thin; if instead a module needs its own repo impl, its Infra adds a ref to central Infra, never the reverse) | ⚠ optional later |
| `ICurrentUserProvider`, `IDateTimeProvider` impls | ✅ (Task 5) | ❌ |
| DI composition: `IModule` + `Add{M}Module()`; per-module MediatR assembly registration | ❌ | ✅ |
| Domain-event dispatch wiring (`SaveChangesInterceptor`, MediatR `IPublisher` wrapper) | ✅ (Task 5) | ❌ |

**Entity-placement decision (gates Task 3, flag for executor — plan text vs clean architecture):** Task-3 plan literally lists `Company`/`Branch`/`Account`/`AuditLogEntry` as entities created "Inside `SmeAccounting.Infrastructure`". Two readings:
- **(A) plan-literal** — EF entity classes live in central Infrastructure now. Simple, matches plan text; debt: entities sit outside their bounded contexts, must be lifted into module Domains (Organization/ChartOfAccounts/Audit) later.
- **(B) module-Domain-first (recommended)** — each entity authored in its owning module Domain at Task 3 (`Company`/`Branch`→Organization, `Account`→ChartOfAccounts, `AuditLogEntry`→Audit); central Infrastructure adds ProjectReferences to those 3 module Domains so the **single shared DbContext still models them**; migrations + seeding stay central. Cost: 3 ProjectReferences; benefit: entities live in their context from day 1, matches RESEARCH §2A/2D ownership, no later refactor.

Recommendation: **(B)**. Either way the foundation (Task 2) leaves module Domains empty and central Infrastructure untouched; Task 3 executor confirms within that task's scope. kgrzybek-style per-module DbContext/migrations **rejected** for foundation — conflicts with the single-shared-DbContext decision and Task-3 CI migration path (`--project Infrastructure`).

### 14. Domain events — in-process dispatch seam, minimal design (foundation, no outbox)

R8 §5 fixed the SharedKernel seam (`IDomainEvent`, `BaseEntity.RaiseDomainEvent`/`ClearDomainEvents`, `IDomainEventsDispatcher`). This subsection pins the dispatch mechanics so Task 3/5 wire it without guesswork:

```csharp
// SharedKernel.Events — optional DRY convenience base (verified compiles 0-warning):
public interface IDomainEvent { DateTime OccurredAtUtc { get; } }
public abstract record DomainEvent(DateTime OccurredAtUtc) : IDomainEvent;   // entities: sealed record XEvent(...) : DomainEvent(now)

// Task 5, base Application — the strongly-typed MediatR wrapper:
public record DomainEventNotification<TDomainEvent>(TDomainEvent DomainEvent) : INotification
    where TDomainEvent : IDomainEvent;

// Task 5, central Infrastructure — seam implementation (no outbox):
public sealed class DomainEventsDispatcher : IDomainEventsDispatcher
{
    private readonly IPublisher _publisher;
    public async Task DispatchAsync(IEnumerable<IDomainEvent> events, CancellationToken ct)
    {
        foreach (var e in events)
            await _publisher.Publish(new DomainEventNotification<IDomainEvent>(e), ct);
    }
}
```

Foundation decisions (all deliberate minimisation):
1. **Dispatch trigger = after commit, single owner.** Task 5 registers a `SaveChangesInterceptor` (central Infrastructure) that: collects `DomainEvents` from tracked `BaseEntity` aggregates → `ClearDomainEvents()` → `await base.SaveChangesAsync(...)` → `DispatchAsync(collected)`. Do **not** also dispatch from the `IUnitOfWork` implementation — one owner, no double-fire. Re-entrancy: because the ledger is cleared post-dispatch, a second `SaveChangesAsync` in the same scope no-ops events.
2. **Why after commit:** handlers observe persisted aggregates; a failed handler can't roll back the aggregate's save. Trade-off, documented: handler failure after commit leaves the event "lost" (no transactional outbox). Acceptable at foundation (single-box, in-process, accounting domain events are rare); Task 5/7 revisit with retry/monitoring and recorded `ObservedAt`. Milan's guidance on outbox deferred.
3. **Wrapper over MediatR, not `IDomainEvent : INotification`** — keeps SharedKernel zero-package/license-clean (R8). Handlers are plain `INotificationHandler<DomainEventNotification<T>>` registered via `AddMediatR` assembly scan (module Applications register theirs via module Infra, §15).
4. Cross-module awareness: a module can only now-discover other modules' events if the event **type** is reachable (module → module refs prohibited). Rules for when this bites: keep cross-module events in Module.Application of the raising module and let the consumer reference Contracts-only (or central base Application for genuinely cross-cutting events like audit). Not exercised at foundation — recorded so Task 5 doesn't invent a bus.

### 15. Composition root — exact patterns + the Api-module-reference question (RESOLVED)

All patterns below **verified locally**, full 12-module graph compiled + ran (SDK 10.0.401, `LangVersion 14.0`, `TreatWarningsAsErrors` + `latest-recommended` + `EnforceCodeStyleInBuild`).

**Base Application — `AddApplication()`** (base `SmeAccounting.Application/DependencyInjection.cs` static class; now gains its 3 PackageReferences, all already CPM-pinned — **no Directory.Packages.props change**):

```csharp
using FluentValidation;
using MediatR;
using Microsoft.Extensions.DependencyInjection;

namespace SmeAccounting.Application;

public abstract class ApplicationMarker { }

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services) => services
        .AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssemblyContaining<ApplicationMarker>();
            cfg.Lifetime = ServiceLifetime.Scoped;                 // verified: DI merged in MediatR main pkg
        })
        .AddValidatorsFromAssembly(typeof(ApplicationMarker).Assembly, ServiceLifetime.Scoped)
        .AddTransient(typeof(IPipelineBehavior<,>), typeof(ValidationBehaviour<,>));
}
```

**Base Infrastructure — `AddInfrastructure()`**: empty body `=> services;` today; providers/DbContext/persistence land Task 3/5.

**Module Infrastructure — `{M}Module` + `Add{M}Module()`** (R8 §6), with the AddModule body now registering its own Application assembly (verified `AddMediatR` is safe to call 13 times — base + 12 modules; handles accumulate, core services dedupe):

```csharp
public sealed class JournalModule : IModule
{
    public IServiceCollection AddModule(IServiceCollection services) => services
        .AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<JournalApplicationMarker>());
}
public static class JournalModuleExtensions
{
    public static IServiceCollection AddJournalModule(this IServiceCollection services)
        => new JournalModule().AddModule(services);
}
```

**→ RESOLVED: Api references each module Application AND Infrastructure — NOT Infrastructure-only.** R8 §7's graph ("Api refs only 12× module Infra") is registration-complete but **typing-broken**: MVC controllers must construct typed `IRequest<T>` commands, and command types live in module Application. Api referencing module Infra alone leaves those types invisible (proven in scratch: the host needed `using SmeAccounting.Modules.Journal.Application` to `Send(new PingQuery())`). Final Api wiring: base `SmeAccounting.Application` + base `SmeAccounting.Infrastructure` + **12×(module Application + module Infrastructure)** = 24 module ProjectReferences. Clean-architecture-consistent (Api → Application + Infrastructure per Task-1 rule), zero reflection, zero extra packages.

**Api `AddModules` helper** — must live in a namespace (CA1050, §17):

```csharp
// SmeAccounting.Api/ModulesAddExtensions.cs
namespace SmeAccounting.Api;
public static class ModulesAddExtensions
{
    public static IServiceCollection AddModules(this IServiceCollection services, IEnumerable<IModule> modules)
    {
        foreach (var m in modules) m.AddModule(services);
        return services;
    }
}
```

**Program.cs order** (R8 §8, with modules): `AddControllersWithViews()` → `builder.Services.AddApplication()` → `.AddInfrastructure()` → `.AddModules([new IdentityModule(), new AuthorizationModule(), … new FinancialReportingModule()])`. Explicit array, no reflection (`Assembly.GetTypes()` scanning rejected per R8 §6).

### 16. Project reference wiring table + naming + slnx (36 new projects, verified)

**Naming convention** (matches Task-1 manual-csproj style, all verified CA1716-clean + 0-warning):
- Project file == AssemblyName == RootNamespace == `SmeAccounting.Modules.{M}.{Layer}` (csproj sets `RootNamespace` + `AssemblyName` explicitly, per existing Task-1 csprojs).
- Folder: `src/Modules/{M}/{Domain|Application|Infrastructure}/` (12 module names, PascalCase, all safe — incl. `MasterData`, `ChartOfAccounts`, `AccountingPeriod`, `FinancialReporting`, `GeneralLedger`).

**Wiring table (36 projects + Api additions; the three-layer rule extends to every module):**

| Project (36) | ProjectReference (→) | PackageReference |
|---|---|---|
| `{M}.Domain` (×12) | `SmeAccounting.Domain`, `SmeAccounting.SharedKernel` | **none** |
| `{M}.Application` (×12) | `SmeAccounting.Application`, `SmeAccounting.SharedKernel`, own `{M}.Domain` | `MediatR` (pinned 12.5.0) |
| `{M}.Infrastructure` (×12) | own `{M}.Application` | **none** |
| `SmeAccounting.Api` (adds) | + 12×`{M}.Application` + 12×`{M}.Infrastructure` (on top of existing base App+Infra) | none new |
| `SmeAccounting.Application` (base, gains) | unchanged (Domain, SharedKernel) | + `MediatR`, `FluentValidation`, `FluentValidation.DependencyInjectionExtensions` (all already CPM-pinned 12.5.0 / 12.1.1 / 12.1.1) |

- **No module→module ProjectReference** (verified in scratch: every module ref points only at `..\Application\`/`..\Domain\` within its own module). Compiler-enforced isolation; Arch tests in Task 6 re-check.
- **Central Infrastructure**: unchanged at Task 2 (no module refs; Task 3 may add the Option-B module-Domain refs per §13).
- Project count after Task 2: 5 base src + 36 module + 6 tests = **47** in the slnx (matches R8).
- **`.slnx`**: `dotnet sln add` appends **flat** `<Project Path>` entries — it does NOT auto-create Folder elements (verified). Executor: `dotnet sln SmeAccounting.slnx add src/Modules/*/*/*.csproj` (or per-project), then hand-edit slnx to group like the existing `/src/`/`/tests/` folders, e.g.:
  ```xml
  <Folder Name="/src/Modules/">
    <Folder Name="/src/Modules/Journal/">
      <Project Path="src/Modules/Journal/Domain/SmeAccounting.Modules.Journal.Domain.csproj" />
      <Project Path="src/Modules/Journal/Application/SmeAccounting.Modules.Journal.Application.csproj" />
      <Project Path="src/Modules/Journal/Infrastructure/SmeAccounting.Modules.Journal.Infrastructure.csproj" />
    </Folder>
    <!-- … 11 more modules … -->
  </Folder>
  ```
- **Lock files**: 36 new `packages.lock.json` (module Apps carry MediatR + its transitive chain; Domains remain `net10.0: {}`; Infras carry MediatR transitives) + base `SmeAccounting.Application` lock regenerated (new packages). Api lock untouched (project refs don't affect package locks). Executor flow: scaffold → `dotnet restore --use-lock-file` → verify `dotnet restore --locked-mode` exit 0 → commit (NU1004 expected on the first locked build if locks aren't regenerated first).

### 17. NEW local findings — WTE analyzer traps in the R8 designs (must fix during Task 2)

Five rules fire under `TreatWarningsAsErrors` + `AnalysisLevel latest-recommended` + `EnforceCodeStyleInBuild` (all reproduced in scratch, SDK 10.0.401):

1. **CA1716 — the planned `Error` record name FAILS the build.** `public sealed record Error(...)` triggers *"Rename type Error so that it no longer conflicts with the reserved language keyword"* (VB `Error`). R8 §5's `Result` design as written **does not compile under WTE**. Fix (verified): rename to **`Failure`** — `Failure(string Code, string Description)`; property `Result.Failure`, static `Result.Failure(...)` rename to `Fail(...)` (avoids `Failure`/`Failure` name-collision noise; compiled clean). Alternatives if a different name is preferred: `AppError`, `DomainError` — executor picks one and records in docs/architecture.md.
2. **CA1000 — no static members on generic types.** `Result<T>.Success`/`Result<T>.Failure` static factories error. Verified fix: `.editorconfig` → `dotnet_diagnostic.CA1000.severity = none` (whole-solution; this rule is a style-guard and the factory pattern is intentional). Alternative: `[SuppressMessage]` on `Result<T>` only. Keep static factories `Create`/`Fail` (implicit conversions preserved).
3. **CA1725 — override parameter names must match the interface.** `IPipelineBehavior<TRequest,TResponse>.Handle(..., CancellationToken cancellationToken)` and `IRequestHandler<,>.Handle(..., CancellationToken cancellationToken)`: naming the parameter `ct` is a build error. Use `cancellationToken` in the FV behaviour **and in every future MediatR handler** (R8 §3 sample needs the rename).
4. **CA2016 — forward the token.** `return await next(cancellationToken);` (passing nothing to `next()` errors).
5. **CA1050 — no global types.** Helper extension classes next to `Program.cs` top-level statements must be **namespaced** (`namespace SmeAccounting.Api;`), CS8803 forbids namespace-after-top-level-statements so put helpers in their own file.

Re-verified clean after fixes: SharedKernel `Result/Failure/Result<T>`, `ValidationBehaviour` with canonical param names, module markers, `IModule` host in base Application, Composition root dispatch. Zero warnings across the whole 12-module graph.

### 18. References (Researcher 9 additions)

| Topic | Source |
|---|---|
| CA1716 reserved-keyword type names (Error → failure) | [learn.microsoft CA1716](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca1716) |
| CA1000 static members on generic types (suppress via editorconfig) | [learn.microsoft CA1000](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca1000), [learn.microsoft code-analysis-identifiers](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/configuration-options) |
| CA1725 parameter-name matches base, CA2016 forward CancellationToken | [learn.microsoft CA1725](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca1725), [CA2016](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca2016) |
| CA1050 declare types in namespaces | [learn.microsoft CA1050](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca1050) |
| EF `SaveChangesInterceptor` + domain-events-after-commit pattern | [milanjovanovic.tech building-a-custom-domain-events-dispatcher-in-dotnet](https://milanjovanovic.tech/blog/building-a-custom-domain-events-dispatcher-in-dotnet) |
| slnx folder elements (flat `dotnet sln add`, manual Folder nesting — [local]) | [learn.microsoft dotnet new sln / slnx](https://learn.microsoft.com/dotnet/core/tools/dotnet-sln), SDK 10.0.401 CLI-verified |
| MediatR 12.5.0 multi-`AddMediatR` registration (scoped, dedupe — [local]) | [github.com/LuckyPennySoftware/MediatR](https://github.com/LuckyPennySoftware/MediatR) |
