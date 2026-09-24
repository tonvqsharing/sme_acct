# Environment Tools — SME Accounting (Business Partners loop)

**Discovered:** 2026-09-23 (fresh rediscovery — global cache was stale)

## Tool Availability

| Tool | Version | Command |
|------|---------|---------|
| dotnet SDK | 10.0.401 | `dotnet` |
| .NET Runtime / ASP.NET Core | 10.0.12 | — |
| dotnet-ef (global tool) | 10.0.12 | `dotnet-ef` |
| roslyn-language-server | 5.12.0-1.26426.8 | LSP |
| git | 2.51.0 | `git` |
| curl | 8.20.0 | `curl` |
| node | v26.5.0 | `node` |
| npm | 11.17.0 | `npm` |
| python3 | 3.13.9 | `python3` |
| psql | 18.4 (client) | `psql` |
| PostgreSQL server | 16.14 (Windows host 172.21.208.1) | **REACHABLE** ✓ |

**DB check passed:** `PGPASSWORD=123456 psql -h 172.21.208.1 -U dev -d sme_acct_dev -c "select version();"` → PostgreSQL 16.14, exit 0.

## Not Available

- `docker` — not installed
- `nuget` CLI, `make`, `gcc`/`g++`, `jq` — not installed
- No dev server running (ports 5000–5100 scanned, none responding)
- **codegraph: NOT indexed** — no `.codegraph/` dir in repo. Use grep/glob/read for code discovery.

## MCP Servers (configured in ~/.config/opencode/opencode.jsonc)

| Server | Status | Use |
|--------|--------|-----|
| codegraph | configured, but **no index for this project** | skip — use grep/glob/read |
| playwright | configured, browser tools available | UI testing only (not needed for backend module) |
| headroom | configured, context compression | available |

## Skills (available via skill tool)

Domain/design: domain-modeling, ubiquitous-language, codebase-design, design-an-interface, grill-me, grilling, interview-me, idea-refine
Implementation: implement, incremental-implementation, tdd, test-driven-development, spec-driven-development, source-driven-development, karpathy-guidelines, planning-and-task-breakdown
Quality: code-review, code-review-and-quality, doubt-driven-development, debugging-and-error-recovery, diagnosing-bugs, security-and-hardening, performance-optimization
Docs: documentation-and-adrs, research, research-gate, to-spec, to-tickets, handoff, dev-standup
Loop orchestration: loop-engineer, using-agent-skills

## Project Structure

```
SmeAccounting.sln (6 projects)
├── src/SmeAccounting.Domain/          — pure, zero NuGet refs. Entities/, Ports/, Events/
├── src/SmeAccounting.Application/     — MediatR CQRS. Commands/, Queries/, Validators/, DTOs/, Behaviors/, Services/
├── src/SmeAccounting.Infrastructure/  — EF Core. Persistence/Configurations/, Repositories/, Migrations/
├── src/SmeAccounting.Api/             — MVC. Controllers/, ViewModels/, Views/, Program.cs
├── tests/SmeAccounting.ArchitectureTests/  — 22 NetArchTest rules
└── tests/SmeAccounting.BankTests/          — 72 tests (bank/posting domain)
```

Architecture: Api → Application → Domain ← Infrastructure. Dependency direction enforced by 22 NetArchTest rules (violations break build). Controllers must NOT reference Domain.Entities or Domain.Repositories.

## Build / Test / Migration Commands (all verified working)

```bash
# Build — VERIFIED: 0 warnings, 0 errors, ~11s
dotnet build SmeAccounting.sln

# Architecture tests — VERIFIED: 22/22 passed
dotnet test tests/SmeAccounting.ArchitectureTests/

# Bank tests — VERIFIED: 72/72 passed
dotnet test tests/SmeAccounting.BankTests/

# Run app (Swagger at /swagger in dev)
dotnet run --project src/SmeAccounting.Api/

# EF migrations — VERIFIED working (use --no-build, first run is slow ~2min)
dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api
dotnet ef migrations list --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api --no-build
dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api

# Database
PGPASSWORD=123456 psql -h 172.21.208.1 -U dev -d sme_acct_dev
```

**NOTE:** `dotnet ef migrations list` without `--no-build` timed out at 60s (rebuild + slow startup). With `--no-build` it completes. Budget ~2min for first ef invocation.

## Migrations (17 total, latest first)

```
20260922084832_PostingReferenceHarden
20260922073756_AddPaymentMethod
20260922062742_AddBankHierarchy
20260921052333_CompanyOpeningUserMgmt
20260921025725_AddInventoryAccountingConfiguration
20260921024242_AddInventoryValuationPolicyAndAdjustmentReason
20260921022726_AddItemAndServiceItem
20260921021609_AddUomConversion
20260921020956_AddWarehouse
20260921020615_AddItemCategory
20260917111153_AddUom
20260917092428_BusinessPartnerFoundation   ← Business Partners base already migrated
20260917045015_Phase3TaxFoundation
20260917013843_Phase2AccountingControlConfig
20260916083803_AccountingFoundation
20260916051520_FixAccountNameColumn
20260916051341_InitialCreate
```

## ⚠️ Business Partners module — ALREADY PARTIALLY BUILT

**Exists (full CQRS + EF + controller + migration):**
- Entities: `Customer`, `Supplier`, `Employee` (Domain/Entities/)
- Ports: `ICustomerRepository`, `ISupplierRepository`, `IEmployeeRepository`
- EF configs: `CustomerConfiguration.cs`, `SupplierConfiguration.cs`, `EmployeeConfiguration.cs`
- Repos: `EfCustomerRepository.cs`, `EfSupplierRepository.cs`, `EfEmployeeRepository.cs`
- Commands: `CreateCustomerCommand`, `CreateSupplierCommand`, `CreateEmployeeCommand`, `DeactivateCustomerCommand`, `DeactivateSupplierCommand`, `DeactivateEmployeeCommand`
- Queries: `GetCustomerQuery`, `GetCustomersByCompanyQuery`, `GetSupplierQuery`, `GetSuppliersByCompanyQuery`, `GetEmployeeQuery`, `GetEmployeesByCompanyQuery`
- Validators: `CreateCustomerCommandValidator`, `CreateSupplierCommandValidator`, `CreateEmployeeCommandValidator`
- Controllers: `CustomerController`, `SupplierController`, `EmployeeController`
- ViewModels: `CreateCustomerViewModel`, `CreateSupplierViewModel`, `CreateEmployeeViewModel`

**MISSING (per PLAN.md goal — grep confirmed zero matches in src/):**
- `CustomerGroup`, `SupplierGroup`, `SupplierItem` — no entity, no repo, no config, no command, no controller, no migration

**Pattern to follow for new entities** (from existing Customer/Supplier/Employee):
- Domain entity: class extends `BaseEntity`, xmin concurrency, value objects for enums
- EF config: `IEntityTypeConfiguration<T>` → snake-case table/columns, FKs
- Repo: `Ef*Repository : I*Repository` async CRUD, DbContext injection
- Application: MediatR command/query → handler → repo; FluentValidation `AbstractValidator<T>` in same project
- Controller: thin, MediatR dispatch only, no Domain refs
- Migration: `dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`

## Code Discovery Guidance

- **No codegraph index** — use Grep/Glob/Read tools directly
- Grep for symbols: `grep -rn "CustomerGroup" src/` (or Grep tool)
- Existing pattern reference: read `src/SmeAccounting.Domain/Entities/Customer.cs` + `CustomerConfiguration.cs` + `EfCustomerRepository.cs` + `CreateCustomerCommand.cs` + `CustomerController.cs` for the canonical 5-layer pattern

## API Credentials

- DB: `dev`/`123456` @ `172.21.208.1`/`sme_acct_dev` (in appsettings.json, plaintext)
- No other API keys/tokens found in env

## Newly Discovered Resources (Online — Unconfirmed Local)

(researcher-only section — empty until researchers append)

## Resource Usage Guide

```
dotnet build SmeAccounting.sln                    → build all (0 warn / 0 err baseline)
dotnet test tests/SmeAccounting.ArchitectureTests/ → 22/22 arch tests
dotnet test tests/SmeAccounting.BankTests/         → 72/72 bank tests
dotnet run --project src/SmeAccounting.Api/        → run app
dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api → new migration
dotnet ef migrations list --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api --no-build → list migrations
dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api → apply migrations
PGPASSWORD=123456 psql -h 172.21.208.1 -U dev -d sme_acct_dev → psql shell
grep/glob/read → code discovery (no codegraph index)
playwright browser tools → UI testing (configured)
```