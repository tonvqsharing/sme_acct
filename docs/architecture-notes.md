# Architecture Notes (placeholder)

> Extended in Task 7 (`docs/architecture.md`). Captures foundation-level architecture decisions made in Task 2, per RESEARCH R8/R9.

## Layers & Dependency Rules

| Layer | References (project refs) | Package refs |
|---|---|---|
| `SmeAccounting.Domain` | none | none |
| `SmeAccounting.SharedKernel` | none | none |
| `SmeAccounting.Application` | Domain, SharedKernel | MediatR 12.5.0, FluentValidation 12.1.1, FluentValidation.DependencyInjectionExtensions |
| `SmeAccounting.Infrastructure` | Application, Domain, SharedKernel | none (FrameworkReference `Microsoft.AspNetCore.App` for `IHttpContextAccessor`) |
| `SmeAccounting.Api` | Application, Infrastructure, 12×(module Application + module Infrastructure) | none new |

## Module Isolation

- 12 MVP module triads under `src/Modules/{Module}/{Domain,Application,Infrastructure}/`; namespace `SmeAccounting.Modules.{Module}.{Layer}`.
- **No module→module project references** — compiler-enforced; cross-module communication only via SharedKernel contracts / domain events (Task 5 wiring).
- Module Domain → base Domain + SharedKernel (zero packages). Module Application → base Application + SharedKernel + own Domain + MediatR. Module Infrastructure → own Application only (DI + `IModule`, zero EF, zero packages).

## Composition Root (Api)

- `AddControllersWithViews()` (MVC, not Razor Pages) + `MapStaticAssets()` + default controller route.
- `AddApplication()` — MediatR (`AddMediatR`, Scoped) + FluentValidation (`AddValidatorsFromAssembly`) + `ValidationBehaviour` pipeline.
- `AddInfrastructure()` — `AddHttpContextAccessor` + `IDateTimeProvider` (Singleton, system clock) + `ICurrentUserProvider` (Scoped, ClaimsPrincipal-based; Identity wired Task 4).
- `AddModules([…12 module instances…])` — **explicit registry, no reflection** (RESEARCH R8 §6/R9 §15). Api references **module Application AND module Infrastructure** (24 refs) — controllers need typed `IRequest<T>` from module Application (R9 correction of R8's Infra-only graph).
- `AddMediatR` called 13× (base + 12 modules) — verified safe, Scoped, dedupes core services.
- MediatR 12.5.0 DI merged into main package (no `MediatR.Extensions.Microsoft.DependencyInjection`).

## SharedKernel

- Persistence-ignorant: `BaseEntity` (Guid Id, domain-events ledger), `ValueObject`, `IAuditable`, `ISoftDeletable`, `ICompanyScoped` (`CompanyId`, OQ-2 mitigation), `IDomainEvent`/`DomainEvent`, `IDomainEventsDispatcher` seam (MediatR `IPublisher` wrapper in Task 5; **no outbox** at foundation), `ICurrentUserProvider`, `IDateTimeProvider`, custom `Failure`/`Result`/`Result<T>` (zero-package; **CA1000 suppressed** for static `Create`/`Fail`), minimal `IRepository<T>` + `IUnitOfWork`.
- `Failure` (not `Error`) — CA1716 reserved-keyword trap (R9 §17).

## Result Flow Convention

- Input validation → FluentValidation pipeline throws `ValidationException` (400 ProblemDetails in Task 5).
- Expected business-rule failures → `Result.Failure(...)` / `Result<T>.Fail(...)`.
- Exceptional/unexpected → exception → 500.
- Handlers return `Result<T>`; controllers translate to `ActionResult`/ProblemDetails (Task 5).

## Migrations & Schema Ownership

- **Single shared `SmeAccountingDbContext` owned by central `SmeAccounting.Infrastructure`** — EF configurations, migrations, seeds all central; module Infrastructures hold **zero EF**.
- Migrations generated `--project Infrastructure --startup-project Api`; idempotent SQL + bundle artifacts (Task 3 + CI).
- Entity placement (Task 3): **Option B (R9 §13)** — entities authored in owning module Domains (Company/Branch→Organization, Account→ChartOfAccounts, AuditLogEntry→Audit); central Infrastructure adds refs to those 3 module Domains so the shared DbContext still models them.

## Notes / Risks

- Lock files: 36 module projects + base Application + base Infrastructure regenerated after package adds (`dotnet restore --use-lock-file`); Api lock untouched (project refs only).
- WTE traps applied: CA1716 (`Failure`), CA1000 (.editorconfig), CA1725 (`cancellationToken` param names), CA2016 (`next(cancellationToken)`), CA1050 (namespaced helper `ModulesAddExtensions`).
- FrameworkReference note: `Microsoft.AspNetCore.Http.Abstractions` NuGet package is EOL (capped 2.3.13) → Infrastructure uses `<FrameworkReference Include="Microsoft.AspNetCore.App" />` instead.