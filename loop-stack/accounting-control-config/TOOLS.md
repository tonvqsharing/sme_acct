# TOOLS.md — Accounting Control Config Loop

**Scout run:** 2026-09-16

## .NET SDK

- Version: **10.0.401**
- Target Framework: `net10.0` (set in `Directory.Build.props`)
- C# Language Version: **13**
- Nullable: **enabled**
- Implicit Usings: **enabled**
- TreatWarningsAsErrors: **true** (build fails on any warning)

## Global Tools

| Tool | Version | Command |
|------|---------|---------|
| dotnet-ef | 10.0.12 | `dotnet-ef` |
| roslyn-language-server | 5.12.0 | LSP |

## EF Core Tools

- `dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- `dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- `dotnet ef migrations list --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`

## Solution Structure

```
SmeAccounting.sln
├── src/
│   ├── SmeAccounting.Domain/          (pure .NET class lib, zero NuGet)
│   ├── SmeAccounting.Application/     (CQRS handlers, validators)
│   ├── SmeAccounting.Infrastructure/  (EF Core, adapters)
│   └── SmeAccounting.Api/             (ASP.NET MVC, composition root)
└── tests/
    └── SmeAccounting.ArchitectureTests/ (22 NetArchTest constraints)
```

## NuGet Packages by Project

### SmeAccounting.Domain (zero NuGet refs)
- None. Pure class library.

### SmeAccounting.Application
- **MediatR** 14.2.0 — CQRS command/query dispatch
- **FluentValidation** 12.1.0 — command validation
- **FluentValidation.DependencyInjectionExtensions** 12.1.0 — auto-validation pipeline

### SmeAccounting.Infrastructure
- **Microsoft.EntityFrameworkCore** 10.0.4 — ORM
- **Npgsql.EntityFrameworkCore.PostgreSQL** 10.0.3 — PostgreSQL provider
- **Microsoft.Extensions.DependencyInjection** 10.0.12 — DI container
- **EFCore.NamingConventions** 10.0.* — snake_case table/column naming

### SmeAccounting.Api
- **Microsoft.EntityFrameworkCore.Design** 10.0.12 — EF migrations (Design-time only)
- **Swashbuckle.AspNetCore** 10.2.3 — Swagger/OpenAPI
- **FluentValidation** 12.1.0 (duplicate reference, for pipeline registration)
- **MediatR** 14.2.0 (duplicate reference, for handler registration)

### SmeAccounting.ArchitectureTests
- **NetArchTest.Rules** 1.3.2 — architecture constraint enforcement
- **xunit** 2.9.3 — test framework
- **xunit.runner.visualstudio** 3.1.4 — test runner
- **Microsoft.NET.Test.Sdk** 17.14.1 — test host
- **coverlet.collector** 6.0.4 — code coverage

## Domain Entities (16 total, after Task 2)

Account, AccountGroup, BaseEntity (abstract), Company, CostCenter, Currency, Department, DocumentNumberingSeries, ExchangeRate, FiscalPeriod, FiscalYear, JournalEntry, JournalEntryLine, PostingReference, Project, VoucherType

## Domain Ports (15 interfaces, after Task 2)

IAccountRepository, IAuditLogger, IClock, ICompanyRepository, ICostCenterRepository, ICurrencyRepository, IDepartmentRepository, IDocumentNumberingSeriesRepository, IExchangeRateRepository, IForeignExchangeRateProvider, IJournalEntryRepository, IPostingService, IProjectRepository, IUnitOfWork, IVoucherTypeRepository

## Code Style Rules (.editorconfig)

| Rule | Value |
|------|-------|
| Indent | 4 spaces (C#), 2 spaces (csproj/json/yaml) |
| Line endings | LF |
| Charset | UTF-8 |
| Trailing whitespace | trimmed |
| Final newline | inserted |
| `var` usage | preferred everywhere |
| Private fields | `_camelCase` (underscore prefix) |
| Braces | Allman style (new line before `{`) |
| Expression-bodied methods | single line only |
| Expression-bodied properties | preferred |
| Language keywords over framework types | enforced (warning) |

## Build Commands

```bash
dotnet build SmeAccounting.sln                    # build all
dotnet test tests/SmeAccounting.ArchitectureTests/ # run arch tests
dotnet run --project src/SmeAccounting.Api/        # run app
```

## Architecture Constraints (enforced by tests)

- Domain must NOT reference Application, Infrastructure, or Api
- Application must NOT reference Infrastructure or Api
- Infrastructure must NOT reference Api
- Controllers must NOT reference Domain.Entities or Domain.Repositories
- All dependency violations break the build

## ADRs (3 accepted)

1. **ADR-001: Clean Architecture** — dependency inversion, port/adapter pattern
2. **ADR-002: CQRS with MediatR** — commands/queries separation, FluentValidation pipeline
3. **ADR-003: Accounting Posting Seam** — IPostingService as domain service, event-driven posting flow

## Database

- PostgreSQL 16.14 on Windows host (172.21.208.1)
- Connection: `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`
- Snake-case naming via EFCore.NamingConventions
- `xmin` concurrency tokens on all entities

## Regulatory Context

- VAS (Vietnamese Accounting Standards)
- Circular 99/2025/TT-BTC compliance
- Circular 99 Art. 28(c): immutability and audit trail requirements
- No docs/ directory at repo root (docs are in loop-stack subdirectories)

## Key Patterns for Implementation

- **Commands**: Record type, IRequest<T>, FluentValidation validator
- **Queries**: Record type, IRequest<T>, return DTOs
- **Handlers**: IRequestHandler<TRequest, TResponse>
- **Pipeline**: ValidationBehavior (auto-validates before handler)
- **Port interfaces**: In Domain/Ports/, implemented in Infrastructure
- **Entities**: Inherit BaseEntity, use xmin concurrency tokens
- **Value objects**: Records in Domain
- **DTOs**: Records in Application layer
