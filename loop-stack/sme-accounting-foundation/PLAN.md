# Loop Plan
## Mode
build
## Goal
Build production-ready project foundation and layout for Vietnamese SME Accounting Web Application. ASP.NET Core 10, MariaDB, Clean Architecture, Modular Monolith, on-premise. Foundation only — architecture, modules, projects, DB strategy, security, testing, deployment, docs.
## Stop Condition
all tasks in loop-stack/sme-accounting-foundation/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks

Sequential build loop — each task is one executor session. G1→G7 (distinct groups = strict sequential dependency; no conceptual parallelism: each task builds on the previous one's artifacts). Budget 20 turns.

Inputs: `RESEARCH.md` (all sections), loop+global `MEMORY.md`/`TOOLS.md`. Hard rule: FOUNDATION ONLY — scaffold architecture, no accounting engine, no business rules invention, no fake CRUD. Resolve open questions where they gate a task (OQ-1/2/3/7/10); defer the rest (OQ-4/5/6/8/9) out of scope for foundation.

---

### Task 1 [G1] — Solution Skeleton & Build Conventions ✅ DONE
**Pillar:** project layout. **Blocked by:** nothing. **Blocks:** all.

Status: VERIFIED_PASS 2026-09-11 (audit CLEAN, verifier VERIFIED_PASS). Committed 38 files.

Build-system foundation of the repo. Layout (per RESEARCH `## Environment & Integration` §Build Structure):
```
SmeAccounting.slnx
├── src/SmeAccounting.{Domain, Application, SharedKernel, Infrastructure, Api}/
├── src/Modules/                          (module skeletons created in Task 2)
├── tests/SmeAccounting.{Domain,Application,Infrastructure,Architecture,Security}.Tests/
├── docs/  deploy/  scripts/  .github/workflows/
├── global.json  NuGet.config  .editorconfig  .gitignore  .dockerignore
├── Directory.Build.props  Directory.Build.targets  Directory.Packages.props
```
Create:
- `.slnx` (slnx XML format, .NET 10 default), `global.json` pinning SDK 10.0.x (`rollForward: latestFeature`)
- `Directory.Build.props` — net10.0, Nullable, ImplicitUsings, LangVersion latest, `TreatWarningsAsErrors`, `AnalysisLevel latest-recommended`; **no TFM-conditional logic in .props** (moves to `.targets`)
- `Directory.Build.targets` — any TFM-conditioned targets only
- `Directory.Packages.props` — CPM: MediatR, FluentValidation(+DI ext), Pomelo.EntityFrameworkCore.MySql **9.0.0**, Serilog.AspNetCore(+enrichers, compact format, Seq), xUnit v3 + MTP runner, NSubstitute, AwesomeAssertions, NetArchTest.Rules **1.3.2** (pinned), Mvc.Testing, Testcontainers.MariaDb, Testcontainers.XunitV3, Respawn, AspNetCore.HealthChecks.MySql, EF Core (9.x, implicit via Pomelo). Enable CentralPackageTransitivePinningEnabled.
- `NuGet.config` — single nuget.org source + package source mapping (dependency-confusion defense)
- `.editorconfig` — file-scoped namespaces, analyzer severity overrides, line length
- `.gitignore` (artifacts/, bin/, obj/, .env), `.dockerignore`
- `--artifacts-path artifacts` build output
- Empty projects for all src/ + tests/ layers, wired by **project references ONLY** enforcing the dependency graph: Domain/SharedKernel → nothing; Application → Domain+SharedKernel; Infrastructure → Application+Domain+SharedKernel; Api → Application+Infrastructure (composition root); test projects → their targets. No module projects yet.
- xUnit v3 test projects via `dotnet new xunit --test-runner MTP`
- Commit `packages.lock.json`; restore must pass `--locked-mode`

**Verify:**
- `dotnet restore --locked-mode` exits 0
- `dotnet build -c Release` exits 0, zero warnings (warnings-as-errors active)
- `dotnet sln SmeAccounting.slnx list` shows every project
- csproj reference graph matches dependency rule (inspect: Domain has zero PackageReference, no test project references src it shouldn't)
- artifacts/ populated, NuGet.config maps all sources, lock files committed

**Sweeps:** none (trivial scaffolding).

---

### Task 2 [G2] — Core Architecture: Clean Architecture + Modular Monolith Kernel ✅ DONE
**Pillar:** architecture. **Blocked by:** Task 1. **Blocks:** Task 3, 4, 5.

Status: VERIFIED_PASS 2026-09-11 (audit CLEAN, verifier VERIFIED_PASS). 36 module projects + SharedKernel + composition root.

- `SmeAccounting.SharedKernel`: `BaseEntity`, `ValueObject`, `IAuditable` (Created/Updated; per RESEARCH §8 audit field set), `ISoftDeletable`, `ICompanyScoped` with `CompanyId` (OQ-2 mitigation — single-tenant now, tenant-ready field on key entities, cost ~zero), `IDomainEvent` + in-process dispatch seam, `ICurrentUserProvider`, `IDateTimeProvider`, `Result<T>`/error types, repository + `IUnitOfWork` abstractions. No EF attributes — persistence-ignorant.
- Module skeleton: **12 MVP modules** (RESEARCH §2A/2D) as `src/Modules/{Identity, Authorization, Organization, MasterData, Audit, ChartOfAccounts, AccountingPeriod, Journal, Posting, GeneralLedger, Tax, FinancialReporting}/{Domain,Application,Infrastructure}/` with a module-registration pattern (`IModule` + `AddModule()` extension method) — **empty structure, no business logic, no fake CRUD, no invented rules**.
- Composition root in Api: `AddApplication()` (MediatR + FluentValidation pipeline behaviour), `AddInfrastructure()`, module registration loop. MediatR + FV behaviour classes live in Application.
- Api structure: `Controllers/`, `Views/` (MVC per assumption Q4/lock in MEMORY), skeleton `Program.cs` (two-stage bootstrap scaffold, body in Task 5).
- Note architecture decisions in `docs/architecture.md` (full doc in Task 7) — dependency rules, module isolation, single shared DbContext, migration ownership (Infrastructure).

**Verify:**
- `dotnet build -c Release` exits 0
- Dependency rule holds at compile level: Domain/SharedKernel csproj carry no PackageReference; Application refs only Domain+SharedKernel; no module→module project references (compiler prevents)
- 12 MVP module triads exist as directories + empty projects with base registrations
- MediatR + FV pipeline behaviour registered (construction succeeds)
- Domain layer free of EF/Infrastructure usings

---

### Task 3 [G3] — Database Strategy & Persistence (MariaDB/EF Core)
**Pillar:** database. **Blocked by:** Task 2. **Blocks:** Task 4, 6.

Inside `SmeAccounting.Infrastructure` (schema owner per MEMORY; migrations generated with `--project Infrastructure --startup-project Api` exactly as RESEARCH CI shows):
- `SmeAccountingDbContext` + entity type configurations via model conventions
- Model-wide: `HasCharSet("utf8mb4").UseCollation("utf8mb4_unicode_ci")`, decimal default precision `18,2`, **DECIDE OQ-1** (snake_case vs PascalCase) and record it, audit fields + soft delete on all mutable entities, global query filter `!IsDeleted`
- Minimal foundation entities only, no accounting engine: `Company`/`Branch` (org skeleton, single-tenant + `CompanyId` per OQ-2), COA `Account` (code/name/type/level — supports Circular 133 open chart), `AuditLogEntry`. **No journal/ledger/posting logic.**
- Pomelo `UseMySql(..., new MariaDbServerVersion(10, 11, 0))` (explicit, never AutoDetect in prod), `EnableRetryOnFailure`, `DisableSensitiveDataLogging`
- `IDesignTimeDbContextFactory` for headless tooling/bundles
- Initial migration + idempotent SQL script regeneration
- Seeds — `UseSeeding` **and** `UseAsyncSeeding` (both, idempotent, existence-checked): Circular 133 COA (49 Level-1 + Level-2, resolve OQ-10: 133 default, structure permits 99/200 alternates), 5 default roles, default admin user (hashed password, env-driven), Development-only demo guard. `HasData` only for tiny static lookups (iso currencies). No `DeleteData` traps.
- Startup check: `PendingModelChangeException` synchronization check — **never** auto-migrate in Production
- Resolve + record OQ-7 (audit granularity = entity-level before/after snapshot for foundation)

**Verify:**
- Initial migration SQL generated; regenerated idempotent script applies cleanly (against local/dev MariaDB if server available; otherwise static SQL review), second run is no-op
- Generated SQL shows `utf8mb4_unicode_ci` on DB/tables, DECIMAL(18,2), decided naming convention, soft-delete query filter, audit columns on mutable tables
- COA seed yields 49 Level-1 accounts; re-seed idempotent (run twice, no duplicates/errors)
- Pending-model-change check passes
- Domain persists-ignorant: no EF attributes/annotations in Domain/SharedKernel

---

### Task 4 [G4] — Security + Identity Foundation
**Pillar:** security/auth. **Blocked by:** Task 3. **Blocks:** Task 5, 6.

- Identity module (real content here — this is the auth scaffold): ASP.NET Core Identity (User/Role/Claim) over the shared DbContext, **cookie authentication** (not `MapIdentityApi`/JWT — per MEMORY pe.)
- Minimal MVC Accounts: login/logout, forgot + reset password, failed-login lockout (threshold/duration config), account states (Active/Locked/Disabled), `[ValidateAntiForgeryToken]` on every POST form
- RBAC: permission catalog (`Permissions.*` constants), 5 standard roles (Admin, ChiefAccountant, Accountant, Viewer, Auditor) seeded, role-permission seeding hook, policy-based authorization (`AuthorizationHandler` + policies like `Permissions.Journal.Create`), branch-scoped access seam (branch claim), `.NET 10` cookie 401-vs-redirect semantics correct for MVC+API mix
- Security audit logging: auth events (login success/failure, lockout, password change/reset, role/permission assignment) → `AuditLogEntry` table **and** Serilog context
- Data Protection: `PersistKeysToFileSystem` + `SetApplicationName("SmeAccounting")` on Linux/Docker (persistent dir, configurable), `ProtectKeysWithDpapi` on Windows; document "never delete keys"
- Security headers middleware (nosniff, X-Frame-Options, HSTS w/ proxy), HTTPS redirect behind proxy
- `ClaimsPrincipal` extension member (C#14) for UserId/role/permission claims

**Verify:**
- Login/logout round-trip works (WebApplicationFactory or manual run)
- Authz behavior: unauthenticated → redirect (MVC)/401 (API); authorized role OK; wrong role/permission → 403
- Lockout triggers after configured failures; password reset flow executes
- Audit rows written for login success/failure/password change/role change; Serilog carries the event
- Data Protection keys directory created and persists across restart (cookie survives)
- Antiforgery token enforced on state-changing forms
- No secrets committed; passwords hashed

---

### Task 5 [G5] — Cross-Cutting Infrastructure
**Pillar:** cross-cutting platform. **Blocked by:** Task 4. **Blocks:** Task 6.

- Serilog two-stage bootstrap (`Program.cs`), config-driven sinks: CompactJsonFormatter rolling file (14d/100MB), Console, Seq dev-only; overrides for EF `.Database.Command`→Warning; `UseSerilogRequestLogging` with UserId enrichment
- Error handling: global exception middleware → ProblemDetails (API) + friendly MVC error views (404/500/403), no stack-trace leakage
- FluentValidation MediatR pipeline behaviour + **vi-VN localized validation messages** (resx)
- Localization: vi-VN resource files; Vietnamese number/currency/date formatting conventions (`. ` thousand separator, `,` decimal), vi-VN default
- Strongly-typed options: `ConnectionStrings`, `Serilog`, `Security`, `DataProtection`, `HealthChecks` sections; `IOptions` binding; secrets via user-secrets (dev)/env vars + 0600 EnvironmentFile (prod) — no committed values
- Wire `IDateTimeProvider` + `ICurrentUserProvider` implementations (Infrastructure)
- Health checks: `/health/live` (no deps, `ShortCircuit`) + `/health/ready` (MySql `SELECT 1`, `AddDbContextCheck`, disk), JSON writer, `RequireHost("localhost"...);` — never MigrateAsync in health check
- ForwardedHeaders with `KnownProxies` hardening (proxy IP), placed before auth/redirect
- `IFileStorage` seam → local on-premise path (scaffold only)

**Verify:**
- App starts; `/health/live` and `/health/ready` return 200/healthy with DB reachable
- Unhandled exception → friendly error page, no stack trace in body; ProblemDetails for API surface
- Validation failure returns vi-VN message from pipeline behaviour
- One structured log line per request incl. UserId; CompactJson file sink rolls
- Env-var config override works (e.g. connection string)
- Startup with DB down → clean fatal log, no hang (no MigrateAsync on startup in Production)

---

### Task 6 [G6] — Testing Structure
**Pillar:** testing. **Blocked by:** Task 5. **Blocks:** Task 7.

- Fill the Task-1 test projects: Domain.Tests, Application.Tests, Infrastructure.Tests (DB/integration), Architecture.Tests, Security.Tests, Web.Tests (WebApplicationFactory)
- xUnit v3 + MTP runner; NSubstitute; **DECIDE OQ-3** assertion lib → AwesomeAssertions (FA fork) or Shouldly, pick one, pin, use consistently, record rationale
- Architecture tests — NetArchTest.Rules 1.3.2 asserting RESEARCH §9 hard rules: Domain zero external deps; Application→Domain only; Infrastructure→App+Domain; Api→App+Infra; no circular deps; no business logic in controllers; no `static` domain methods; persistence-ignorant domain; no module→module references
- Unit: SharedKernel (BaseEntity, soft delete, audit, ValueObject, Result), FV validators, MediatR pipeline behaviour
- Security: policy verification (roles/permissions), lockout, antiforgery, authorization handlers
- DB/integration: `WebApplicationFactory` + Testcontainers.MariaDb + Respawn; **env-var connection-string override** so CI runs against `mariadb:11.4` service (skip container boot when Docker absent — document locally)
- DB tests: seed idempotency (COA 49 rows, roles, admin), audit fields written, soft-delete filter hides rows, utf8mb4 collation, PendingModelChange check test
- Per-project READMEs: how to run each test tier

**Verify:**
- `dotnet test -c Release` (MTP): all unit/application/security/architecture tests pass locally (no Docker required)
- Integration/DB test code present, CI-wired (env-var override); green against real MariaDB in Task 7 CI
- All 9+ architecture rules pass; assertion lib single-consistent
- Test projects restore/build with `--locked-mode`

---

### Task 7 [G7] — Docs, Deployment & CI
**Pillar:** docs + deployment + CI. **Blocked by:** Task 6. **Blocks:** goal acceptance.

- `docs/`: architecture.md (clean arch, modular monolith, dependency rules, conventions), modules.md (module map: 12 MVP + Phase-2 + future, ownership, sealed decisions OQ-1/2/3/7/10), database.md (naming, audit, soft delete, migration policy, seeds, backup), security.md (Identity, RBAC, Data Protection, headers, antiforgery), deployment.md (Linux Nginx+systemd, Windows IIS, Docker, secrets, zero-downtime swap, rollback), backup.md (runbook + restore drill), testing.md; root `README.md` (overview, quickstart, links all docs; **only** if docs were the deliverable — required here)
- `deploy/`: production Dockerfile (3-stage → `aspnet:10.0-noble-chiseled`, non-root UID 1654, `UseAppHost=false`, port 8080, DebugType eviction), `docker-compose.yml` (app + `mariadb:11.4` with `--character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci`, healthchecks, keyring+uploads volumes, `.env` secrets), systemd unit + `EnvironmentFile` (0600) template, Nginx conf + Caddyfile (auto-TLS), IIS `web.config` (in-process), FDD publish profiles (linux-x64/win-x64)
- `scripts/`: `ef-migrations` (bundle + `--idempotent` SQL; `has-pending-model-changes` gate), `backup` (mariadb-dump single-transaction gzip, 14d retention, 3-2-1, 0600 creds; app keyring/uploads), `restore`, `deploy` (migrate-first, symlink swap, systemctl restart, /health/ready smoke)
- CI `.github/workflows/ci.yml`: checkout@v6 + setup-dotnet@v4 + cache@v4; restore `--locked-mode`; build; `dotnet test --test-runner MTP`; integration/DB tests against `mariadb:11.4` service w/ env-var connection string; EF artifacts job (bundle + idempotent SQL upload); `PublishContainer` main-only
- Verify every doc matches what the code actually does (no invented claims)

**Verify:**
- All doc files present, cross-linked, match repo layout/code and resolved OQs
- Dockerfile + compose statically valid; `docker build` passes if Docker available (else review + CI)
- CI workflow YAML valid and green on push (integration tests hit real MariaDB here)
- Scripts executable + idempotent; backup script runbook matches implementation
- README quickstart reproduces local run (dev MariaDB + `dotnet run`)

---

## Pillar → Task Mapping
| Pillar | Task |
|--------|------|
| Project layout | T1 |
| Architecture (clean + modular monolith) | T2 |
| Database | T3 |
| Security/auth | T4 |
| Cross-cutting infra (config/logging/errors/validation/localization/health) | T5 |
| Testing | T6 |
| Deployment + docs + CI | T7 |
