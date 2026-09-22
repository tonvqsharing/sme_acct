# Loop Plan
## Mode
patch
## Goal
Implement PaymentMethod entity in SME Accounting following discovery-first TDD rules
## Stop Condition
all tasks in loop-stack/payment-method-slice/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks
- [x] [G1] Finalize PaymentMethod design (fields CompanyId/Code/Name/IsActive/Description + PaymentMethodType enum decision, constraints, no invented VAS list) — output to docs/PaymentMethod-Design-2026.md, using PaymentTerm template files + docs/Discovery-*-2026.md + global MEMORY T1/VoucherType patterns
- [ ] [G2] Implement PaymentMethod vertical slice via discovery-first TDD (Domain entity + ValueObjects enum + Created event + port, EF configuration + EfPaymentMethodRepository + Ignore-only DbContext wiring + DI AddScoped, Application CQRS commands/queries/handlers + FluentValidation validator + DTO, Api controller + viewmodel) — templates: PaymentTermConfiguration.cs, EfPaymentTermRepository.cs, CreatePaymentTermCommand/Handler/Validator; tools: dotnet SDK 10.0.401, MediatR 14.2.0, FluentValidation 12.1.0, EF Core 10.0.4 + Npgsql 10.0.3
- [ ] [G3] Verify PaymentMethod slice (dotnet build SmeAccounting.sln 0 warnings, dotnet test tests/SmeAccounting.ArchitectureTests/ 22/22 pass, BankTests regression pass, new PaymentMethod domain/validator/handler tests pass per BankTests minimal-test pattern, migration SQL check only after green build via dotnet-ef 10.0.12)
