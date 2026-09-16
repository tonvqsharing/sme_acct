# Environment Tools

**Discovered:** 2026-09-16

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

- `.editorconfig` present at repo root
- C# style: `var` preferred, 4-space indent, LF endings
- Warnings-as-errors: enabled in build
