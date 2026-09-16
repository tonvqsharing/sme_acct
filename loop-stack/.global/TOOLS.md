# Environment Tools

**Discovered:** 2026-09-16 (updated)

## .NET

| Tool | Version |
|------|---------|
| dotnet SDK | 10.0.401 |
| ASP.NET Core Runtime | 10.0.12 |
| .NET Runtime | 10.0.12 |

### dotnet templates (relevant)
- `webapi` — ASP.NET Core Web API
- `mvc` — ASP.NET Core MVC
- `classlib` — Class Library
- `xunit` / `mstest` / `nunit` — Test projects
- `sln` — Solution file
- `worker` — Worker Service
- `console` — Console App

### Global tools
| Package | Version | Command |
|---------|---------|---------|
| dotnet-ef | 10.0.12 | `dotnet-ef` |
| roslyn-language-server | 5.12.0-1.26426.8 | LSP |

## Dev Tools

| Tool | Version |
|------|---------|
| git | 2.51.0 |
| Node.js | v26.5.0 |
| npm | 11.17.0 |
| psql (PostgreSQL) | 18.4 |
| curl | 8.20.0 |
| python3 | 3.13.9 |
| OpenSSL | 3.5.4 |

## Not Available

- `nuget` CLI — not installed (use `dotnet nuget` or PackageReference)
- `make` — not installed
- `gcc` / `g++` — not installed
- `jq` — not installed
- `docker` — not installed

## NuGet Sources

- nuget.org (enabled): `https://api.nuget.org/v3/index.json`

## Project Config

- `Directory.Build.props` at repo root: net10.0, C# 13, nullable, implicit usings, warnings-as-errors
- `.editorconfig` present at repo root
- C# style: `var` preferred, `_camelCase` private fields, 4-space indent, LF endings, Allman braces
- Warnings-as-errors: enabled in build

## Project NuGet Packages

| Project | Key Packages |
|---------|-------------|
| Domain | (none — pure library) |
| Application | MediatR 14.2.0, FluentValidation 12.1.0 |
| Infrastructure | EF Core 10.0.4, Npgsql 10.0.3, EFCore.NamingConventions |
| Api | EF Core Design 10.0.12, Swashbuckle 10.2.3, MediatR, FluentValidation |
| ArchitectureTests | NetArchTest.Rules 1.3.2, xunit 2.9.3 |

## Key Architecture Constraints

- Clean Architecture: Domain <- Application <- Infrastructure, Api
- 22 NetArchTest rules enforce dependency direction
- Controllers must NOT reference Domain.Entities or Domain.Repositories
- CQRS with MediatR: commands, queries, handlers, pipeline behaviors
- FluentValidation for command validation (auto-pipeline)
- PostgreSQL with snake-case naming, xmin concurrency tokens

## Regulatory Context

- VAS (Vietnamese Accounting Standards)
- Circular 99/2025/TT-BTC compliance
- ADRs in loop-stack/vietnamese-acct-architecture_DONE/docs/architecture/
