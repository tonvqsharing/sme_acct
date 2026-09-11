# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
### Stack (locked)
- **net10.0 / ASP.NET Core 10 / EF Core 9.0.0 via Pomelo.EntityFrameworkCore.MySql 9.0.0 / MariaDB 10.11 LTS / utf8mb4_unicode_ci / Clean Architecture Modular Monolith / MVC** (assumption Q4, 12 MVP modules).
- **DB schema owned by Infrastructure TFSP module; EF migrations idempotent SQL + migration bundle artifact (CI-generated); PendingModelChangeException sync check on startup.**
- **Domain**: Circular 133 has 49 Level-1 accounts (111-911, open extension policy); double-entry with balanced transactions and derived balances; VAS 10 FX rules; 90-day annual FS deadline.
- **Open TODOs** (10 Qs): naming convention, tenant ID field, assertion lib, period automation, inventory costing, rate API, audit granularity, workflow engine, report versioning, seed data scope — executor must resolve during planning.

### EF Core seeding
- **EF Core 9**: UseSeeding+UseAsyncSeeding (implement BOTH sync+async, idempotent) for Circular 133 COA / roles / admin user; HasData only for tiny static lookups — removing HasData emits DeleteData (edit it out on seeded prod).

### Auth
- **MVC cookie auth + ASP.NET Identity RBAC** (5 roles, policy-based, branch-scoped). Not MapIdentityApi (JWT/opaque). .NET 10 cookie auth returns 401 not redirect; C#14 claims extension members available.

### Observability & ops
- **Serilog two-stage bootstrap; CompactJsonFormatter file sink; Seq in dev only; request-logging enriches UserId.**
- **Data Protection**: Linux/Docker must PersistKeysToFileSystem to a persistent dir + SetApplicationName; DPAPI on Windows; never delete keys (breaks existing cookies).
- **Health checks**: /health/live (no deps) + /health/ready (MySql SELECT 1 + EF AddDbContextCheck + disk), ShortCircuit + RequireHost; never MigrateAsync in health check.
- **Reverse proxy**: Nginx (LAN/self-signed) or Caddy (public domain auto-HTTPS); ForwardedHeaders needs KnownProxies hardening (env shortcut lacks it).
- **Deploy**: FDD per-RID publish; SCD only if host lacks runtime; zero-downtime symlink swap + systemctl restart; migrate before deploy.
- **Containers**: .NET 10 chiseled runtime = aspnet:10.0-noble-chiseled (Ubuntu default, UID 1654, port 8080) — framework-dependent by default. PublishContainer alt. NO native AOT for this stack.
- **Backup**: mariadb-dump single-transaction gzip, 0600 creds file, atomic mv, 14d retention, 3-2-1, quarterly restore drill; mariabackup + binlog ROW for >50GB.
- **CI**: checkout@v6/setup-dotnet@v4/cache@v4; --locked-mode with committed packages.lock.json; mariadb:11.4 Docker service + healthcheck.sh --innodb_initialized; test-runner MTP; xUnit v3; Testcontainers for MariaDB integration tests; dotnet tool restore (no install) in SDK image.

### Build & style gotchas
- **.slnx; Directory.Build.props (properties/items) vs .targets (TFM-conditioned targets); CPM Directory.Packages.props; NuGet.config source mapping.**
- **NETSDK1188** (Microsoft.Testing.Platform 2.3.3 ships `ru`/`cs`/`zh-*` locale resources .NET rejects) fires as error under TreatWarningsAsErrors → suppress via `<NoWarn>$(NoWarn);NETSDK1188</NoWarn>` in Directory.Build.props.
- **IDE0005 build trap**: IDE0005 (unused usings) at build time REQUIRES GenerateDocumentationFile=true (Roslyn #41640 — hard CSC error "EnableGenerateDocumentationFile"). Keep GenerateDocumentationFile=false; set IDE0005=suggestion; the file-scoped-namespace gate (IDE0161 via `csharp_style_namespace_declarations=file_scoped:error` + EnforceCodeStyleInBuild) is the working style gate.
- **CA1716**: `Error` record name FAILS build (reserved VB keyword) → rename to `Failure` (+ `Fail(...)` factory; `Result.Failure` prop). `SmeAccounting.Modules.{Module}.{Layer}` clean under WTE.
- **CA1000**: `Result<T>.Success/Failure` static factories on generic → suppress via `.editorconfig` `dotnet_diagnostic.CA1000.severity = none`.
- **CA1725**: MediatR override params must be named `cancellationToken` (not `ct`).
- **CA2016**: `next(cancellationToken)` — pass token explicitly.
- **CA1050**: helpers by Program.cs need own namespaced file.
- **CS0108**: `Result<T>.Fail(...)` covariant factory hides base `Result.Fail(...)` → must add `new` keyword (return-type-only hiding is error under WTE).

### Package pins & tools (live-verified on nuget.org, executor T1)
- **All 23 CPM pins verified**: MediatR **12.5.0** (last Apache-2.0; 13+ RPL-1.5 commercial), Pomelo 9.0.0, FluentValidation 12.1.1, Serilog.AspNetCore 10.0.0, Serilog.Sinks.Seq 9.1.0 / Sinks.Async 2.1.0 / Formatting.Compact 3.0.0 / Enrichers.Thread 4.0.0 / Enrichers.Process 3.0.0, Mvc.Testing 10.0.12, HealthChecks.EFCore 10.0.12 / HealthChecks.MySql 9.0.0, Testcontainers.MariaDb + Testcontainers.XunitV3 4.15.0, Respawn 7.0.0, NetArchTest.Rules 1.3.2, xunit.v3 4.0.0, NSubstitute 6.2.0, AwesomeAssertions 9.6.0.
- **Global tools installed**: dotnet-ef 10.0.12, Microsoft.Web.LibraryManager.Cli (LibMan) 3.0.114.

### FluentValidation details
- **FV 12.1.1 DI namespace (reflection-verified)**: `AddValidatorsFromAssembly[Containing]` is `ServiceCollectionExtensions` in namespace **`FluentValidation`** (NOT `FluentValidation.DependencyInjectionExtensions` — that namespace does not exist; CS0234/CS1061 trap). `using FluentValidation;` alone suffices.
- **ValidationFailure** lives in `FluentValidation.Results` namespace.
- `ValidationBehaviour<TRequest,TResponse> : IPipelineBehavior<,>` canonical shape: `Handle(request, next, cancellationToken)` (CA1725), `next(cancellationToken)` (CA2016), `Task.WhenAll` parallel validate, null-failure filter, `throw new ValidationException(failures)`.

### C# 14 / .NET 10 details
- **Extension members** work at `LangVersion 14.0` (no preview): `extension (ClaimsPrincipal claims) { public Guid? UserId => ...; }` — no block modifier, receiver w/o `this`, receiver-accessing members instance-only (static→CS9347).
- **MVC10**: `dotnet new mvc` → `AddControllersWithViews()` + `MapStaticAssets()` + `MapControllerRoute`.
- **IHttpContextAccessor**: `Microsoft.AspNetCore.Http.Abstractions` NuGet package is EOL (versions top at 2.3.13, netstandard2.0-era). Modern net10.0 approach: `<FrameworkReference Include="Microsoft.AspNetCore.App" />` in Infrastructure — no package, no CPM pin, no lock change.
- **wwwroot missing → runtime warn** `StaticFileMiddleware[16] The WebRootPath was not found` (benign, not build-blocking). Fix: `wwwroot/.gitkeep` in Api.

### Module architecture (Task 2, 2026-09-11)
- **12 MVP modules** (AccountingPeriod, Audit, Authorization, ChartOfAccounts, FinancialReporting, GeneralLedger, Identity, Journal, MasterData, Organization, Posting, Tax) × 3 layers = 36 module projects.
- **Module registry pattern**: `IModule` in base Application + per-module static `Add{Module}Module()` + explicit 12-module `AddModules([...])` in Api — no reflection, no scanning.
- **Api must reference module Application AND module Infrastructure** (24 refs) — controllers need typed `IRequest<T>` command types from module Application. NOT Infra-only.
- **AddMediatR safe 13×** (base + 12 modules, all Scoped) — assembly scans, service override no-op, container decides lifetime.
- **No module→module refs** — each module refs only own Domain/Application + base (Domain/SharedKernel/Application).
- **Infrastructure split**: DB/schema/migrations/seeding central in `SmeAccounting.Infrastructure` (single shared `SmeAccountingDbContext`); module Infra = IModule + DI only, zero EF.
- **Dependency graph enforced**: Domain/SharedKernel carry zero ProjectReference AND zero PackageReference; Application→Domain+SK; Infrastructure→Application+Domain+SK; Api→Application+Infrastructure+24 module refs.
- Module Domain folders: **0 .cs files** (empty structure, no invented business logic — boundaries in docs/architecture-notes.md only).

### SharedKernel / Result pattern
- **Result core**: `record Failure(string Code, string Description)`; `Result<T>` (Create/Fail with `new` CS0108 covariant-hide, `T? Value` throws on failed access, implicit conversions); `Result` non-generic variant for void.
- **ValueObject**: IEquatable + ==/!= operators (CS0660/0661/CA1815/CA2225-safe) or records.
- **Persistence-ignorant contracts**: `IAuditable`/`ISoftDeletable`/`ICompanyScoped` (CompanyId = OQ-2), `IDomainEvent` + `DomainEvent` record + `IDomainEventsDispatcher` seam (no MediatR/INotification leak into SK), `ICurrentUserProvider`, `IDateTimeProvider`, `IRepository<T>`, `IUnitOfWork`.
- **`IModule` host lives in base Application** (IServiceCollection transitive via MediatR DI — SharedKernel can't reference MediatR).

### Shell / scaffolding traps
- **zsh traps in module scaffolding**: (a) `modules` is a read-only zsh special variable — assignment dies; (b) `for m in $scalar` does NOT word-split in zsh (unlike bash) → single iteration, one dir literally named "Identity Authorization …". Use zsh array `mods=(Identity …)` or bash; verify with per-dir loop + csproj count.
- **`pkill -f SmeAccounting.Api` is self-matching footgun** — use kill-by-port or kill-by-PID.

### .slnx / solution quirks
- **`dotnet sln list` quirk (SDK 10.0.401)**: slnx folder-inside-folder nesting drops nested projects from `dotnet sln list` output (restore/build still resolve them). Fix: `/src/Modules/` must be TOP-LEVEL Folder sibling of `/src/` + `/tests/` (single-level nesting only) → list shows all 47. Pretty per-module sub-folder nesting does NOT survive `dotnet sln list`.
- `dotnet sln add` writes flat paths (no auto-folder nesting) → hand-add `<Folder Name="/src/Modules/{M}/">`.

### Lock files / CPM
- **47 total** (36 module + 5 base + 6 test). CentralPackageTransitivePinningEnabled spreads MediatR/FV transitively into test/Api locks (Api lock DID change — commit it).
- After package adds: `dotnet restore --use-lock-file` (NU1004) + commit all new lock files.
