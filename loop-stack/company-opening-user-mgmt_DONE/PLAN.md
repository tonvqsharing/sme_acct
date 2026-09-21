# Loop Plan
## Mode
build
## Goal
Implement Company Settings, Opening Balances and Microsoft-first User Management for SmeAccounting
## Stop Condition
all tasks in loop-stack/company-opening-user-mgmt/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks
[x] [G1] Design CompanySettings domain model: CompanySetting entity with LegalRepresentative, ChiefAccountant, fiscal settings, JSON extension, BaseEntity, domain events, EF configuration scaffold per snake_case/xmin pattern
[x] [G1] Design Opening Balances domain engine: OpeningBalanceEntry aggregate, OpeningBalancePeriod, validation rules, posting integration with JournalEntry, domain events, EF configurations with FK Restrict to Company
[x] [G1] Design Microsoft-first User Management domain model: User, Role, UserRole, CompanyMembership entities, port interfaces IUsersRepository/IRoleRepository, validation, Clean Architecture constraints, no ASP.NET Identity domain coupling
[x] [G2] Implement CompanySettings Application + Infrastructure: MediatR commands/queries, FluentValidation validators, DTO records, handlers using IUnitOfWork, EF Repository EfCompanySettingRepository, DI registration
[x] [G2] Implement Opening Balances Application + Infrastructure: Create/Get/Validate OpeningBalanceEntry commands, FluentValidation, handlers, EF configurations, repositories, posting service integration
[x] [G2] Implement User Management Application + Infrastructure + Identity adapter: User/Role commands, ASP.NET Core Identity adapter in Infrastructure, Microsoft Sign-in integration points, ports, DI registration
[x] [G3] Apply EF migrations, seed initial roles/users, update Program.cs auth middleware, run dotnet build SmeAccounting.sln and dotnet test architecture tests to confirm 22 NetArchTest rules pass
