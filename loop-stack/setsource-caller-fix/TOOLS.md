# Environment Tools

**Status:** REUSED FROM GLOBAL (cached 2026-09-21)

**Discovered:** 2026-09-16 (updated)

## .NET

| Tool | Version |
|------|---------|
| dotnet SDK | 10.0.401 |
| ASP.NET Core Runtime | 10.0.12 |
| .NET Runtime | 10.0.12 |

### dotnet templates (relevant)
- `webapi` — ASP.NET Core Web API
- `mvc` — ASP.NET Core MVC
- `classlib` — Class Library
- `xunit` / `mstest` / `nunit` — Test projects
- `sln` — Solution file
- `worker` — Worker Service
- `console` — Console App

### Global tools
| Package | Version | Command |
|---------|---------|---------|
| dotnet-ef | 10.0.12 | `dotnet-ef` |
| roslyn-language-server | 5.12.0-1.26426.8 | LSP |

## Dev Tools

| Tool | Version |
|------|---------|
| git | 2.51.0 |
| Node.js | v26.5.0 |
| npm | 11.17.0 |
| psql (PostgreSQL) | 18.4 |
| curl | 8.20.0 |
| python3 | 3.13.9 |
| OpenSSL | 3.5.4 |

## Not Available

- `nuget` CLI — not installed (use `dotnet nuget` or PackageReference)
- `make` — not installed
- `gcc` / `g++` — not installed
- `jq` — not installed
- `docker` — not installed

## Newly Discovered Resources (Online — Unconfirmed Local)

### Vietnamese Legal Databases (for Tax Research)
1. **congbao.chinhphu.vn** — Official Government Gazette — laws, decrees, circulars
2. **thuvienphapluat.vn** — Legal Library — comprehensive Vietnamese legal database
3. **luatvietnam.vn** — Legal information portal with translations
4. **vanban123.vn** — Legal document database

### Tax Reference Sources
1. **PwC Worldwide Tax Summaries** (taxsummaries.pwc.com) — Vietnam corporate tax rates
2. **Vietnam Briefing** (vietnam-briefing.com) — Tax guides for foreign investors
3. **EY Tax Updates** (ey.com) — Technical tax updates
4. **MISA SME Accounting** (sme.misa.vn) — Vietnamese accounting software with tax guidance

## NuGet Sources

- nuget.org (enabled): `https://api.nuget.org/v3/index.json`

## Project Config

- `Directory.Build.props` at repo root: net10.0, C# 13, nullable, implicit usings, warnings-as-errors
- `.editorconfig` present at repo root
- C# style: `var` preferred, `_camelCase` private fields, 4-space indent, LF endings, Allman braces
- Warnings-as-errors: enabled in build

## Project NuGet Packages

| Project | Key Packages |
|---------|-------------|
| Domain | (none — pure library) |
| Application | MediatR 14.2.0, FluentValidation 12.1.0 |
| Infrastructure | EF Core 10.0.4, Npgsql 10.0.3, EFCore.NamingConventions |
| Api | EF Core Design 10.0.12, Swashbuckle 10.2.3, MediatR, FluentValidation |
| ArchitectureTests | NetArchTest.Rules 1.3.2, xunit 2.9.3 |

## Key Architecture Constraints

- Clean Architecture: Domain <- Application <- Infrastructure, Api
- 22 NetArchTest rules enforce dependency direction
- Controllers must NOT reference Domain.Entities or Domain.Repositories
- CQRS with MediatR: commands, queries, handlers, pipeline behaviors
- FluentValidation for command validation (auto-pipeline)
- PostgreSQL with snake-case naming, xmin concurrency tokens

## Regulatory Context

- VAS (Vietnamese Accounting Standards)
- Circular 99/2025/TT-BTC compliance
- ADRs in loop-stack/vietnamese-acct-architecture_DONE/docs/architecture/

## Phase 3 — Tax Foundation (Existing Patterns to Follow)

### Existing Domain Entities (19 files)
Account, AccountGroup, JournalEntry, JournalEntryLine, FiscalYear, FiscalPeriod, PostingReference, Currency, ExchangeRate, PostingConfiguration, Company, Department, Project, CostCenter, VoucherType, DocumentNumberingSeries, TransactionReason, OpeningBalanceMapping, BaseEntity

### Existing Port Interfaces
Domain/Ports/: IAccountRepository, IJournalEntryRepository, IUnitOfWork, IForeignExchangeRateProvider, IAuditLogger, IPostingService, IClock

### Existing EF Configurations (Infrastructure/Persistence/Configurations/)
One `*Configuration.cs` per entity. Pattern: `EntityTypeBuilder<T>` with snake-case table names, xmin concurrency tokens, value object conversions.

### Existing Repositories (Infrastructure/Repositories/)
One `Ef*Repository.cs` per entity. Pattern: async CRUD, DbContext injection.

### Existing Migrations (4 total)
1. 20260916051341_InitialCreate
2. 20260916051520_FixAccountNameColumn
3. 20260916083803_AccountingFoundation
4. 20260917013843_Phase2AccountingControlConfig

### Key Patterns for Tax Entities
- **Domain entity**: record class, extends BaseEntity, xmin concurrency, value objects for enums
- **EF Configuration**: `IEntityTypeConfiguration<T>` → snake-case table, column types, FKs
- **Repository**: `Ef*Repository : IRepository<T>` async methods
- **Application**: MediatR command/query → handler → repository
- **Validation**: FluentValidation `AbstractValidator<T>` in same project as command
- **Migration**: `dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`

### G5 TaxPeriod — Key Pattern Notes
- TaxPeriod is NOT FiscalPeriod (different business concepts)
- 3 FKs: Company + FiscalPeriod + TaxType (all Restrict)
- 2 new enums: FilingFrequency (Monthly/Quarterly), TaxPeriodStatus (Open/Filed/Closed)
- Status workflow: Open → Filed (MarkFiled) → Closed (Close + event)
- Unique index: (CompanyId, FiscalPeriodId, TaxTypeId) — no Code property
- Two events: TaxPeriodCreated + TaxPeriodClosed

### Commands Reference

```bash
# Build
dotnet build SmeAccounting.sln

# Tests
dotnet test tests/SmeAccounting.ArchitectureTests/

# Run
dotnet run --project src/SmeAccounting.Api/

# EF Migrations
dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api
dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api
dotnet ef migrations list --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api

# Database (psql)
PGPASSWORD=123456 psql -h 172.21.208.1 -U dev -d sme_acct_dev
```

## Skills Relevant to Phase 3

| Skill | Use For |
|-------|---------|
| domain-modeling | Design tax domain entities, value objects, aggregate boundaries |
| ubiquitous-language | Establish Vietnamese tax terminology glossary |
| source-driven-development | Research correct VAS/Circular tax treatment before coding |
| test-driven-development | Write tests before implementation for all tax entities |
| tdd | Red-green-refactor cycle for tax logic |
| implement | Execute individual tax entity/feature tasks |
| incremental-implementation | Break tax foundation into small, reviewable chunks |
| code-review-and-quality | Review tax entity designs and implementations |
| doubt-driven-development | Verify tax compliance requirements before coding |
| documentation-and-adrs | Record tax domain decisions and regulatory mapping |
| planning-and-task-breakdown | Break tax foundation into implementable tasks |
| security-and-hardening | Validate tax input sanitization, prevent manipulation |

## CodeGraph

**Not available** — no `.codegraph/` directory in this project. Use grep/glob/read for code discovery.

## MCP Servers

| Server | Status |
|--------|--------|
| codegraph | Available (but no index for this project) |
