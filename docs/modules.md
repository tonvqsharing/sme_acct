# Module Map

## MVP Modules (Phase 1) — 12 Modules

| # | Module | Status | Purpose |
|---|--------|--------|---------|
| 1 | **Identity** | ✅ Scaffolded | User management, login, profile |
| 2 | **Authorization** | ✅ Scaffolded | Roles, permissions, access control |
| 3 | **Organization** | ✅ Scaffolded | Company, branch hierarchy |
| 4 | **MasterData** | ✅ Scaffolded | Chart of accounts, fiscal periods |
| 5 | **Audit** | ✅ Scaffolded | Audit trail, change tracking |
| 6 | **ChartOfAccounts** | ✅ Scaffolded | COA tree, account CRUD |
| 7 | **AccountingPeriod** | ✅ Scaffolded | Period open/close, year-end |
| 8 | **Journal** | ✅ Scaffolded | Journal entries, line items |
| 9 | **Posting** | ✅ Scaffolded | Post/unpost, GL updates |
| 10 | **GeneralLedger** | ✅ Scaffolded | GL queries, balances, trial balance |
| 11 | **Tax** | ✅ Scaffolded | VAT, CIT calculations |
| 12 | **FinancialReporting** | ✅ Scaffolded | Balance sheet, P&L, reports |

All 12 modules are registered in `src/SmeAccounting.Api/Program.cs`.

## Module Structure

Each module contains three projects:

```
Modules/{Name}/
├── Domain/                    # Entities, value objects, domain events
│   └── SmeAccounting.Modules.{Name}.Domain.csproj
├── Application/               # CQRS handlers, validators, DTOs, marker class
│   └── SmeAccounting.Modules.{Name}.Application.csproj
└── Infrastructure/            # IModule impl, EF configs, extensions
    └── SmeAccounting.Modules.{Name}.Infrastructure.csproj
```

- `Application` projects reference MediatR and FluentValidation
- `Infrastructure` projects implement `IModule` and register MediatR from their assembly
- `Domain` projects have zero external dependencies beyond SharedKernel

## Module Registration Pattern

```csharp
// Infrastructure/{Name}Module.cs
public sealed class {Name}Module : IModule
{
    public IServiceCollection AddModule(IServiceCollection services) => services
        .AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<{Name}ApplicationMarker>());
}

// Infrastructure/{Name}ModuleExtensions.cs
public static IServiceCollection Add{Name}Module(this IServiceCollection services)
    => new {Name}Module().AddModule(services);
```

## Isolation Rules

1. Modules communicate via MediatR — no direct assembly references between modules
2. Module `Domain/` must not reference `Infrastructure` (enforced by arch tests)
3. Cross-module entities accessed through shared `SmeAccountingDbContext` in MVP (future: module-specific DbContexts)
4. `Application` marker classes (`{Name}ApplicationMarker`) used as assembly anchors for MediatR registration

## Phase 2 Modules (Planned)

| Module | Purpose |
|--------|---------|
| **Inventory** | Stock tracking, warehouse management |
| **Payroll** | Salary, social insurance, PIT |
| **FixedAssets** | Asset register, depreciation |
| **Budgeting** | Budget planning, variance analysis |
| **Banking** | Bank reconciliation, payments |

## Future Modules (Roadmap)

| Module | Purpose |
|--------|---------|
| **MultiCurrency** | FX rates, currency conversion |
| **InterCompany** | Inter-company transactions, consolidation |
| **DocumentManagement** | Invoice/contract scanning, storage |
| **Workflow** | Approval workflows, routing |
| **Integration** | ERP connectors, bank APIs, tax authority integration |
| **Reporting** | Custom report builder, scheduled reports |
| **Notification** | Email/SMS notifications, reminders |

## Sealed Decisions

- **No inter-module project references** — enforced by architecture tests in `tests/SmeAccounting.Architecture.Tests/ArchitectureTests.cs`
- **Module marker pattern** — every module has a `*ApplicationMarker` class in its `Application` project
- **IModule registration** — all modules go through `AddModules()` in `Program.cs`, not individual extension methods
- **Shared DbContext** — `SmeAccountingDbContext` serves all modules for MVP; module-specific contexts are future work
