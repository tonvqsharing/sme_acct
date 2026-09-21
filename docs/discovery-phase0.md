# Phase 0 Discovery – Repository and Architecture

## Project Identity
- Repository root: `/home/projects/sme_acct`
- Solution: `SmeAccounting.sln`
- Projects:
  - `SmeAccounting.Domain` – src/SmeAccounting.Domain
  - `SmeAccounting.Application` – src/SmeAccounting.Application
  - `SmeAccounting.Infrastructure` – src/SmeAccounting.Infrastructure
  - `SmeAccounting.Api` – src/SmeAccounting.Api
  - `SmeAccounting.ArchitectureTests` – tests/SmeAccounting.ArchitectureTests
- Target framework: net10.0
- Database: PostgreSQL via EF Core, snake-case naming, xmin concurrency

## Architecture
Clean Architecture with CQRS + MediatR
- Domain pure, zero NuGet refs
- Application references Domain only
- Infrastructure implements Ports
- Api thin controllers

## Current State Classification

**Company**
- Company entity EXISTS with Name, TaxCode, Address, Phone, Email, FiscalYearStart, FunctionalCurrency
- Legal Representative / Chief Accountant MISSING
- CompanySetting singleton MISSING
- Report header integration MISSING

**Accounting**
- Chart of Accounts EXISTS
- Journal Entry EXISTS
- OpeningBalanceMapping EXISTS but OpeningBalanceEntry engine MISSING
- AR/AP entities EXISTS
- Inventory entities EXISTS
- Opening balance import/validation/reconciliation MISSING

**Security**
- User/Role/Permission MISSING
- ASP.NET Core Identity NOT present
- Authentication/Authorization MISSING

**UI**
- MVC controllers EXISTS
- Company Setup UI MISSING
- User Management UI MISSING
- Opening Balance UI MISSING

## Conflicts / Risks
- No authentication system – Identity integration required
- No company settings singleton – need design decision
- Opening balance mapping exists but insufficient for full engine

## Next Steps
Design specifications for CompanySetting, OpeningBalanceEntry, User/Role Management with Identity integration.
