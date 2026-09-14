# Architecture

## Overview

Clean Architecture + Modular Monolith for Vietnamese SME accounting. Single deployable unit with strict internal layering and module boundaries.

## Layer Dependency Rules

```
Api → Application → Domain → SharedKernel
  ↘ Infrastructure ↗
```

| Layer | Project | Can Reference |
|-------|---------|--------------|
| SharedKernel | `SmeAccounting.SharedKernel` | Nothing |
| Domain | `SmeAccounting.Domain` | SharedKernel |
| Application | `SmeAccounting.Application` | Domain, SharedKernel |
| Infrastructure | `SmeAccounting.Infrastructure` | Application, Domain, SharedKernel |
| Api | `SmeAccounting.Api` | Infrastructure, Application + all Modules |

Architectural tests enforce these rules in `tests/SmeAccounting.Architecture.Tests/ArchitectureTests.cs`.

## Project Layout

```
src/
├── SmeAccounting.SharedKernel/     # Primitives, Result<T>, IDomainEvent
├── SmeAccounting.Domain/           # Domain markers only (MVP)
├── SmeAccounting.Application/      # IModule, MediatR, FluentValidation
├── SmeAccounting.Infrastructure/   # EF Core, Identity, Serilog, Health
├── SmeAccounting.Api/              # ASP.NET Core host, Program.cs
└── Modules/
    ├── Identity/
    ├── Authorization/
    ├── Organization/
    ├── MasterData/
    ├── Audit/
    ├── ChartOfAccounts/
    ├── AccountingPeriod/
    ├── Journal/
    ├── Posting/
    ├── GeneralLedger/
    ├── Tax/
    └── FinancialReporting/
```

Each module has three sub-projects: `Domain/`, `Application/`, `Infrastructure/`.

## SharedKernel

`src/SmeAccounting.SharedKernel/` — zero-dependency primitives shared across all layers.

- `BaseEntity` — `long Id`, domain events collection
- `Result<T>` / `Result` — monad for operation outcomes (`Failure` record)
- `IDomainEvent` — marker with `OccurredAtUtc`
- `IAuditable` — `CreatedAtUtc`, `CreatedBy`, `UpdatedAtUtc`, `UpdatedBy`
- `ISoftDeletable` — `IsDeleted`, `DeletedAtUtc`, `DeletedBy`
- `ICompanyScoped` — `CompanyId` for tenant isolation
- `IRepository<T>`, `IUnitOfWork` — persistence abstractions
- `ICurrentUserProvider`, `IDateTimeProvider` — infrastructure seams

## Module System

### IModule Interface

`src/SmeAccounting.Application/IModule.cs`:
```csharp
public interface IModule
{
    IServiceCollection AddModule(IServiceCollection services);
}
```

### Composition Root

`src/SmeAccounting.Api/Program.cs` — discovers and registers all 12 modules:

```csharp
builder.Services.AddModules([
    new IdentityModule(),
    new AuthorizationModule(),
    new OrganizationModule(),
    // ... all 12 MVP modules
]);
```

`src/SmeAccounting.Api/ModulesAddExtensions.cs` — iterates `IModule` collection and calls `AddModule` on each.

### Module Internal Structure

Each module follows the same pattern:

```
Modules/{ModuleName}/
├── Domain/          # Entities, value objects, domain events
├── Application/     # CQRS handlers (MediatR), validators, DTOs
└── Infrastructure/  # Module class, EF configurations, extensions
```

Module registration example (`src/Modules/ChartOfAccounts/Infrastructure/ChartOfAccountsModule.cs`):

```csharp
public sealed class ChartOfAccountsModule : IModule
{
    public IServiceCollection AddModule(IServiceCollection services) => services
        .AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<ChartOfAccountsApplicationMarker>());
}
```

Extension method pattern: `Add{ModuleName}Module()` wraps the `IModule` for discoverability.

## Infrastructure DI Composition

`src/SmeAccounting.Infrastructure/DependencyInjection.cs` — `AddInfrastructure()` wires:

- **Persistence**: `SmeAccountingDbContext` with Npgsql (retry-on-failure, 30s timeout)
- **Identity**: ASP.NET Core Identity + RBAC (see Security)
- **Logging**: Serilog (console + rolling file, 14-day retention)
- **Health Checks**: PostgreSQL + EF Core checks
- **Localization**: vi-VN default, en-US secondary
- **Audit**: `AuditLoggingService`
- **Providers**: `SystemDateTimeProvider`, `HttpContextCurrentUserProvider`
- **Validation**: FluentValidation pipeline behavior
- **File Storage**: `LocalFileStorage`
- **Data Protection**: Persisted keys to filesystem
- **Forwarded Headers**: For reverse proxy support

## Request Pipeline

```
Request → ForwardedHeaders → RequestLocalization → GlobalExceptionHandler
       → Routing → Authorization → Controller → MediatR Pipeline
       → ValidationBehaviour → Handler → Response
```

- `GlobalExceptionMiddleware` (`src/SmeAccounting.Infrastructure/ErrorHandling/`) catches unhandled exceptions
- `ValidationBehaviour<TRequest, TResponse>` (`src/SmeAccounting.Application/Behaviours/ValidationBehaviour.cs`) runs FluentValidation before handlers
- Health endpoints bypass auth: `/health/live`, `/health/ready`

## Key Design Decisions

- **MediatR over in-process messaging**: Simpler for monolith; modules register their own handlers
- **Cookie auth over JWT**: Server-rendered MVC app, no SPA/mobile clients yet
- **bigint PKs over UUID**: 8 bytes vs 16, better B-tree performance, single-tenant (see ADR-001)
- **xmin concurrency tokens**: Native PostgreSQL optimistic concurrency (no application-managed version column)
- **snake_case DB naming**: Custom converter in `SmeAccountingDbContext` (Npgsql 9 lacks built-in convention)
