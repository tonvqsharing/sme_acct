# Global Loop Memory
Shared across all loops in this project.
## Learnings

### Project Conventions
- **Target**: .NET 10 LTS (net10.0), ASP.NET Core 10, EF Core 9 (Pomelo provider for MariaDB)
- **Architecture**: Clean Architecture + Modular Monolith, 4-layer standard (Domain/Application/Infrastructure/Api)
- **CQRS**: MediatR for command/query separation
- **Validation**: FluentValidation as MediatR pipeline behavior
- **Database**: MariaDB 10.6+ LTS, on-premise deployment
- **Testing**: xUnit + NSubstitute + FluentAssertions + NetArchTest
- **Naming**: `SmeAccounting.*` namespace prefix

### Vietnamese Accounting Context
- SMEs use Thông tư 133/2016/TT-BTC (simplified accounting regime)
- Standard chart of accounts follows numbered system (111, 112, 131, 133, etc.)
- VAT tracking required (account 133 - Thuế GTGT được khấu trừ)
- VND functional currency with multi-currency support needed

### EF Core + MariaDB Warning
- Pomelo.EntityFrameworkCore.MySql 9.0.0 works with .NET 10 but uses EF Core 9.x
- EF Core 10 native support delayed (original maintainer inactive since late 2025)
- Microting fork has EF Core 10 preview — monitor but don't depend on yet

### Build & Toolchain (verified Task 1, sme-accounting-foundation)
- **Global tools now installed** (WSL2 Kali): dotnet-ef 10.0.12, Microsoft.Web.LibraryManager.Cli (LibMan) 3.0.114 via `dotnet tool install -g` — use `dotnet tool restore` (not install) inside CI/SDK images. Verify installs with `dotnet tool list -g`.
- **MTP test runner is selected via global.json** key `"test.runner": "Microsoft.Testing.Platform"` — NOT `--test-runner` (dotnet new xunit has no such flag). All test projects must use the same runner; **mixing VSTest + MTP hard-fails** ("All projects must use that test runner", exit 1).
- **xunit.v3 test projects require** `OutputType=Exe` + `UseAppHost` + `<Using Include="Xunit"/>`. No Microsoft.NET.Test.Sdk/runner.visualstudio/coverlet in lock files.
- **NETSDK1188**: Microsoft.Testing.Platform 2.3.3 ships locale resources (`ru`,`cs`,`zh-*`) .NET rejects → error under TreatWarningsAsErrors. Fix: `<NoWarn>$(NoWarn);NETSDK1188</NoWarn>` in Directory.Build.props.
- **IDE0005 trap**: building with unused-using-as-error requires `GenerateDocumentationFile=true` (Roslyn #41640, hard CSC error). Keep GenerateDocumentationFile=false, set IDE0005=suggestion; enforce style instead via `csharp_style_namespace_declarations=file_scoped:error` (IDE0161) + `<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>`.
- **CPM + locked mode**: `Directory.Packages.props` + `--locked-mode`. NU1004 (dependency drift, exit 1), NU1008 (versioned PackageReference under CPM forbidden → use versionless), NU1010 (versionless reference without central PackageVersion). **Every .slnx project must commit its own packages.lock.json**. `<CentralPackageTransitivePinningEnabled>true</...>` recommended.
- **.slnx format**: no GUIDs, folders auto-grouped from paths. `UseArtifactsOutput=true` → repo-root `artifacts/{bin,obj}/{Project}/{Config}/` (explicit ArtifactsPath redundant). `--artifacts-path` CLI overrides the .props global-prop.
- **CA1716** (Fluent API analyzer) flags namespace segment `Lib` — avoid it in real root namespaces. Empty classlibs (no .cs) build 0-warning under TreatWarningsAsErrors.
- **Dependency graph gate**: Domain/SharedKernel carry zero ProjectReference AND zero PackageReference; Application→Domain+SK; Infrastructure→Application+Domain+SK; Api→Application+Infrastructure; tests reference only their targets.
- **MediatR licensing**: 12.5.0 is last Apache-2.0; 13.0.0+ is RPL-1.5 (commercial restrictions) — pin 12.5.0. FluentAssertions went paid (2025) → AwesomeAssertions 9.6.0 fork.
- **.NET 10 chiseled containers**: `aspnet:10.0-noble-chiseled` (Ubuntu default, UID 1654, port 8080), framework-dependent by default; no native AOT for this stack.

### Modular Monolith Kernel (verified Task 2, sme-accounting-foundation)
- **Module registry pattern**: base `Application` exposes `IModule` + per-module `Add{Module}Module()` extension + explicit registry in `Api` (`AddModules([...])` — 12 explicit modules, **no reflection**). Composition root: `AddControllersWithViews → AddApplication → AddInfrastructure → AddModules → MapStaticAssets → MapControllerRoute`.
- **Api references module Application AND Infrastructure (24 refs)** — NOT Infra-only: controllers need typed `IRequest<T>` command types from module Application.
- **Multi-`AddMediatR` is safe** (13×, base + each module, all `Scoped`): assembly scans + service-override patterns are no-ops; container decides lifetimes. MediatR 12.5.0 DI merged into main package (no Extensions pkg); `RegisterServicesFromAssemblyContaining<T>()` + `Lifetime=Scoped`.
- **No module→module refs**; Domain/SharedKernel zero ProjectReference AND zero PackageReference. Module Infrastructure = `IModule` + DI only, zero EF; DB/migrations/seeding centralized in one `SmeAccounting.Infrastructure` + shared `SmeAccountingDbContext`.
- **Infrastructure needs IHttpContextAccessor**: `Microsoft.AspNetCore.Http.Abstractions` NuGet is EOL (top 2.3.13, netstandard2.0-era) → use `<FrameworkReference Include="Microsoft.AspNetCore.App" />` instead — no package, no CPM pin, no lock change. Applies to any lib project needing ASP.NET Core services in net10.0.

### FluentValidation + analyzer traps (verified Task 2)
- **FV DI extension namespace is `FluentValidation`**, NOT `FluentValidation.DependencyInjectionExtensions` (that namespace does not exist → CS0234/CS1061). `AddValidatorsFromAssembly(asm, ServiceLifetime.Scoped)` from `using FluentValidation;` alone.
- **`ValidationFailure` lives in `FluentValidation.Results`** (12.1.1).
- **CA1716**: type named `Error` fails build (reserved VB keyword) → name it `Failure`. Generic `Result<T>` static factories trip CA1000 → `.editorconfig` `dotnet_diagnostic.CA1000.severity = none`.
- **CS0108**: covariant factory `Result<T>.Fail(...)` hiding base `Result.Fail(...)` needs `new` keyword (return-type-only hiding is an error under WTE). No `new` needed for `Create`.
- **CA1725/CA2016**: MediatR `IPipelineBehavior.Handle` override params must be named `cancellationToken`; call `next(cancellationToken)` explicitly.
- **zsh traps** (module scaffolding): `modules` is a read-only zsh special variable; `for m in $scalar` does NOT word-split in zsh (creates one literal space-named dir). Use zsh arrays or bash.

### Identity Module — Application Layer (verified Task 2, build-identity-auth)
- **Permission authorization types belong in Application** (not Infrastructure): `PermissionRequirement`, `PermissionAuthorizationHandler`, `PermissionPolicyProvider`, `ClaimsPrincipalExtensions`, `Permissions` — all depend only on `Microsoft.AspNetCore.Authorization` + `System.Security.Claims`, no Infrastructure deps.
- **FrameworkReference pattern for Authorization**: any net10.0 lib using `IAuthorizationPolicyProvider`, `AuthorizationHandler<T>`, or `AuthorizationPolicyBuilder` needs `<FrameworkReference Include="Microsoft.AspNetCore.App" />` — same pattern as IHttpContextAccessor.
- **PermissionPolicyProvider** intercepts `"Permission:{name}"` policy strings → creates `PermissionRequirement` on the fly. Fallback: `DefaultAuthorizationPolicyProvider`.
- **PermissionAuthorizationHandler** grants access if user has required permission OR `Users.ManageRoles` (admin bypass).

### Identity Module — Infrastructure Layer (verified Task 3, build-identity-auth)
- **IdentityDbContext** extends `IdentityDbContext<ApplicationUser, ApplicationRole, long>` — snake_case table/column naming via `OnModelCreating` loop over `builder.Model.GetEntityTypes()`.
- **IdentityDbContextFactory** implements `IDesignTimeDbContextFactory<IdentityDbContext>` with hardcoded Npgsql connection string — design-time only, `Microsoft.EntityFrameworkCore.Design` PackageReference must have `PrivateAssets="all"`.
- **EF Core package versions in Directory.Packages.props**: Identity.EFCore 10.0.12, EFCore 10.0.12, EFCore.Design 10.0.12, Npgsql.EFCore.PostgreSQL 10.0.3 — all versionless under CPM.
- **Build will fail** until Task 4 adds `ApplicationUser`/`ApplicationRole` — that's expected per plan; only those two CS0246 errors remain.

### Effective working patterns
- **Smoke-test pattern**: build → `dotnet sln list` (expect exact project count) → launch built dll directly → curl `/` expect 200 → kill-by-PID (NOT `pkill -f <name>` — self-matching footgun). `StaticFileMiddleware[16] WebRootPath not found` is benign env artifact when content-root ≠ Api dir; silence with `wwwroot/.gitkeep`.
