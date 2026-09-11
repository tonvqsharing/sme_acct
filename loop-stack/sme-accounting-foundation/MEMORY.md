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

### Package pins & tools (live-verified on nuget.org, executor T1)
- **All 23 CPM pins verified**: MediatR **12.5.0** (last Apache-2.0; 13+ RPL-1.5 commercial), Pomelo 9.0.0, FluentValidation 12.1.1, Serilog.AspNetCore 10.0.0, Serilog.Sinks.Seq 9.1.0 / Sinks.Async 2.1.0 / Formatting.Compact 3.0.0 / Enrichers.Thread 4.0.0 / Enrichers.Process 3.0.0, Mvc.Testing 10.0.12, HealthChecks.EFCore 10.0.12 / HealthChecks.MySql 9.0.0, Testcontainers.MariaDb + Testcontainers.XunitV3 4.15.0, Respawn 7.0.0, NetArchTest.Rules 1.3.2, xunit.v3 4.0.0, NSubstitute 6.2.0, AwesomeAssertions 9.6.0.
- **Global tools installed**: dotnet-ef 10.0.12, Microsoft.Web.LibraryManager.Cli (LibMan) 3.0.114.

### Task 1 delivered
- 11 empty projects, `.slnx` w/ src/ tests/ folders auto-grouped (no GUIDs), empty src classlibs build 0-warning, 6 xunit.v3 MTP test projects (OutputType Exe) each pass 1 smoke test; `--locked-mode` gates; artifacts/ at repo root (UseArtifactsOutput); packages.lock.json committed 11/11; Dependency graph enforced (Domain/SharedKernel zero refs; Application→Domain+SK; Infrastructure→App+Domain+SK; Api→App+Infra; tests→targets). Fix-ups recorded: NETSDK1188 NoWarn, IDE0005 GenerateDocumentationFile trap.