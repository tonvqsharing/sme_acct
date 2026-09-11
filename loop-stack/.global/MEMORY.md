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
