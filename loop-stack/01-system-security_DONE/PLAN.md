# Loop Plan
## Mode
build
## Goal
Implement complete System / Security foundation for SmeAccounting: Company, CompanySetting, CompanyMembership, User, UserRole, Role, DocumentNumberingSeries, VoucherType, TransactionReason with Microsoft-first ASP.NET Core Identity integration, company isolation, audit, and concurrency-safe numbering
## Stop Condition
all tasks in loop-stack/01-system-security/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks
- [x] [G1] Design Company/CompanySetting domain entities, value objects, events, ports, and EF configurations with company isolation and VAS compliance
- [x] [G1] Design CompanyMembership/User/Role domain entities, events, ports, and repository contracts for multi-company membership and role assignment
- [x] [G1] Design DocumentNumberingSeries/VoucherType/TransactionReason domain entities, events, and concurrency-safe numbering logic
- [x] [G2] Implement Application layer commands/queries/handlers/validators/DTOs for Company, CompanySetting, Membership, Role, VoucherType, TransactionReason, DocumentNumberingSeries
- [x] [G2] Integrate Infrastructure Identity: Microsoft Entra adapter, IdentityUserAdapter mapping, DI registration, and authentication pipeline stubs
- [x] [G2] Create EF Core migrations and seeding scripts for system security tables with snake_case naming and xmin concurrency
- [x] [G3] Security review and tests: architecture tests, unit tests for domain validation, integration tests for repositories, and concurrency safety verification
