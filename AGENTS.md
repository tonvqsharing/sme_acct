# AGENTS.md — SME Accounting

Vietnamese enterprise accounting web app. ASP.NET MVC + Clean Architecture + CQRS.

## Quick Commands

```bash
dotnet build SmeAccounting.sln                    # build all (TreatWarningsAsErrors=true)
dotnet test tests/SmeAccounting.ArchitectureTests/ # 22 architecture constraint tests
dotnet run --project src/SmeAccounting.Api/        # run app (Swagger at /swagger in dev)

# EF Core migrations
dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api
dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api
dotnet ef migrations list --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api
```

No linting, codegen, or migration steps. Build is the primary verification.

## Architecture

```
Api (MVC) → Application (CQRS) → Domain (pure) ← Infrastructure (EF Core)
```

**Dependency direction is enforced by 22 NetArchTest tests.** Violations break the build.

- **Domain** — Zero NuGet refs. Entities, value objects, events, port interfaces. No infrastructure, no HTTP.
- **Application** — MediatR commands/queries, FluentValidation, DTOs. References Domain only.
- **Infrastructure** — EF Core (PostgreSQL), repository implementations, adapter stubs. References Application + Domain.
- **Api** — ASP.NET MVC controllers (thin: MediatR dispatch only). References Application + Infrastructure (composition root).

Controllers must never reference `SmeAccounting.Domain.Entities` or `SmeAccounting.Domain.Repositories`.

## Database

PostgreSQL 16.14 via EF Core on Windows host (`172.21.208.1`).
Connection string in `appsettings.json` under `ConnectionStrings:DefaultConnection`.
Default: `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`.

Connect from Kali: `PGPASSWORD=123456 psql -h 172.21.208.1 -U dev -d sme_acct_dev`

Snake-case table/column naming (`EFCore.NamingConventions`). `xmin` concurrency tokens on all entities.

## Domain Model

Accounting Core entities: Account, AccountGroup, JournalEntry, JournalEntryLine, FiscalYear, FiscalPeriod, PostingReference.

Port interfaces in `Domain/Ports/`: IAccountRepository, IJournalEntryRepository, IUnitOfWork, IForeignExchangeRateProvider, IAuditLogger, IPostingService, IClock.

## Regulatory

VAS (Vietnamese Accounting Standards) and Circular 99/2025/TT-BTC compliance is a core design constraint.
Regulatory docs in `docs/` (if present). Architecture decisions in ADRs.

## Code Style

- C# 13, nullable enabled, implicit usings, `var` preferred
- Private fields: `_camelCase` (enforced by .editorconfig)
- 4-space indent, LF line endings, 2-space for csproj/json/yaml
- FluentValidation for command validation (auto-pipeline via `ValidationBehavior`)
- Records for DTOs and value objects
