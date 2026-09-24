# AGENTS.md — SME Accounting

Vietnamese enterprise accounting web app. ASP.NET MVC + Clean Architecture + CQRS.
.NET 10 (`net10.0`, C# 13, nullable, `TreatWarningsAsErrors=true` — build must be warning-free).

## Quick Commands

```bash
dotnet build SmeAccounting.sln                     # build all (warnings = errors)
dotnet test tests/SmeAccounting.ArchitectureTests/ # 22 layer/purity/naming tests — run after any new file
dotnet test tests/SmeAccounting.BankTests/          # unit tests (fakes-based; NOT bank-specific despite the name)
dotnet test tests/SmeAccounting.BankTests/ --filter FullyQualifiedName~Uom  # focused subset
dotnet run --project src/SmeAccounting.Api/        # run app (Swagger at /swagger in dev)

# EF Core migrations (see "Database" — check-only canon)
dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api
dotnet ef migrations list --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api
```

No linting or codegen. Build + tests are the verification.

## Architecture

```
Api (MVC) → Application (CQRS) → Domain (pure) ← Infrastructure (EF Core)
```

Dependency direction enforced by 22 NetArchTest tests; violations break the build.

- **Domain** — Zero NuGet refs (`0 PackageReference`, arch-tested). Entities, value objects, events, port interfaces. No infrastructure, no HTTP.
- **Application** — MediatR handlers (internal, tested via `InternalsVisibleTo SmeAccounting.BankTests`), FluentValidation, DTOs. References Domain only.
- **Infrastructure** — EF Core (PostgreSQL), repository implementations. References Application + Domain.
- **Api** — Thin MVC controllers (MediatR dispatch only). Never reference `SmeAccounting.Domain.Entities` or `SmeAccounting.Domain.Repositories`.

## Adding an entity (vertical slice pattern)

Every feature lands as a full slice — never just an entity class:

```
entity → event → port interface → EF config → repository → command/handler/validator → query/DTO → controller → tests
```

Template to copy: the Item slice (`src/SmeAccounting.Domain/Entities/Item.cs`, `Persistence/Configurations/ItemConfiguration.cs`, `.../Repositories/EfItemRepository.cs`, `.../Application/Commands/CreateItemCommand.cs`, `.../Controllers/ItemController.cs`, `tests/SmeAccounting.BankTests/ItemAggregateTests.cs`).

Conventions (all arch-enforced or established pattern):
- Entity: private parameterless ctor (EF) + public ctor with `DomainException` guards; minimal domain events (e.g. `XxxCreated`); `Deactivate()` for soft-delete — no hard deletes.
- Config: `ToTable("snake_case")`, enums via `HasConversion<string>()`, `Property<uint>("xmin").IsRowVersion()`, all FKs `OnDelete(Restrict)` (never Cascade/SetNull).
- Repository: `AddAsync` + tracked `GetByIdAsync`/`GetByCodeAsync` + `AsNoTracking` `GetAllByCompanyAsync`. Updates happen via entity method + `SaveChanges` (xmin optimistic concurrency). No `Remove`.
- Command: `record XxxCommand(long CompanyId, ...)` — **CompanyId first**. FluentValidation validator (string lengths 20/200/500). No AutoMapper — manual Map to DTO records.
- Wiring — exactly 3 edits: DbContext `DbSet<T>` **and** `modelBuilder.Ignore<Event>()` (both mandatory), DI `AddScoped` (re-read shared files before editing).
- Tests: xunit Facts in `tests/SmeAccounting.BankTests/`, List-backed fakes in `Fakes.cs`, `Id = 5` before deactivate tests (`using SmeAccounting.Application.Handlers;` for internal handlers).

## Database

PostgreSQL 16.14 via EF Core on Windows host (`172.21.208.1`).
Connection string in `appsettings.json` under `ConnectionStrings:DefaultConnection`.
Default: `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`.

Connect from Kali: `PGPASSWORD=123456 psql -h 172.21.208.1 -U dev -d sme_acct_dev`

Migration canon (established, do not deviate):
- **Check-only**: never run `dotnet ef database update` without explicit user approval. DB migrations are applied manually, not at app startup — the dev DB can be **ahead of git**.
- One consolidated migration per feature; review generated SQL (snake_case, xmin, Restrict FKs, indexes) before applying.
- Nullable column added to an existing table: `AddColumn` nullable with **NO defaultValue**; constructor param goes **LAST** (existing callsites keep compiling).
- Link entities: partial unique index via `HasFilter("\"is_active\"")`; uniqueness is `(CompanyId, Code)` or `(CompanyId, FK...)` composite.
- All foreign keys `Restrict`; no cascades. Money `decimal(18,2)`, conversion factors `decimal(18,6)`. Never `float` for money/quantity.
- Snake-case naming (`EFCore.NamingConventions`); `xmin` concurrency tokens everywhere.

## Company isolation & authorization

- **No `[Authorize]` anywhere**; `AddAuthentication("PlaceholderScheme")` with no handler. Endpoints are NOT protected — never assume they are.
- No EF global query filter (`HasQueryFilter` count = 0). Company isolation is explicit: `CompanyId` in every command + `Where(e => e.CompanyId == companyId)` in repository queries + unique `(CompanyId, Code)` indexes.
- Every new master-data entity is company-scoped and follows this. Do not invent tenancy/filters.

## Existing entities — search before creating

Already exist (with full slices + migrations + live tables): Account(+Group), Currency, TaxType/TaxRate/TaxRule/TaxTreatment/TaxAccountingMapping/TaxAuthority/TaxExemptionReason, JournalEntry(+Line), PostingConfiguration/PostingReference, Company/Membership/User/Role, Supplier/Customer (+Group), **Item, ItemCategory (self-ref ParentId), ServiceItem, Uom, UomConversion, Warehouse, InventoryValuationPolicy, InventoryAccountingConfiguration (4 Account FKs), InventoryAdjustmentReason, SupplierItem (Supplier↔Item link, no price fields)**, Bank/BankBranch/BankAccount, PaymentMethod, FiscalYear/FiscalPeriod, OpeningBalance*, CostCenter, Department, Project, Employee.

Grep `Domain/Entities/` + migrations before creating any new entity — duplicate concepts break the build culture and the goal spec.

Known limitation (documented, don't silently "fix"): `InventoryValuationPolicy.ValuationMethod` = `{FIFO, LIFO, WeightedAverage}` — LIFO is NOT permitted under operative VN regulation (Circular 200/2014, 133/2016, 99/2025) and permitted SpecificIdentification is absent from the enum. Enum is stored as string; treat as known limitation.

## Regulatory

VAS (Vietnamese Accounting Standards) and Circular 99/2025/TT-BTC compliance is a core design constraint.
Circular 99/2025 replaces Circular 200 effective 2026-01-01. Operative inventory valuation methods: specific identification, weighted average, FIFO (no LIFO).
Regulatory docs in `docs/`. Architecture decisions in ADRs / `loop-stack/*_DONE/REPORT.md`.

## Error handling

No ProblemDetails, no custom exception middleware. FluentValidation `ValidationException` caught in controllers → ModelState. `DomainException` thrown from entity constructors/guards.

## Git & workflow

- **Never `git add -A`.** Working tree contains uncommitted business-partners WIP (CustomerGroup/SupplierGroup/SupplierItem + migration `20260924003244_AddPartnerGroupsAndSupplierItems`, ~69 files) — applied to DB, not in git yet. Stage only files belonging to your change.
- `main` branch only. Commit style: `feat:`/`fix:`/`test:`/`chore:` for code, `loop:` for loop-engineer state commits.
- `loop-stack/` holds loop-engineer state; `*_DONE/` dirs contain `REPORT.md`/`RESEARCH.md` with design decisions and reconciliation matrices — read before re-designing a domain area.
- Code discovery: codebase-memory-mcp (search_graph/trace_path) works; codegraph is configured but has **no index** in this repo (use grep/glob/Read).

## Code Style

- C# 13, nullable enabled, implicit usings, `var` preferred
- Private fields: `_camelCase` (enforced by .editorconfig)
- 4-space indent, LF line endings, 2-space for csproj/json/yaml
- FluentValidation for command validation (auto-pipeline via `ValidationBehavior`)
- Records for DTOs and value objects; `Money` value object via `OwnsOne`, decimal — never float for money or quantity