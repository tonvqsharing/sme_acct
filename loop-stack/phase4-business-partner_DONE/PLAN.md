# Loop Plan
## Mode
build
## Goal
Build Phase 4 Business Partner Foundation on top of Phases 1-3, establishing master-data domain contracts for customers, suppliers, employees, payment/credit terms with accounting/tax integration.
## Stop Condition
all tasks in loop-stack/phase4-business-partner/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks
- [x] [G1] Implement Domain layer contracts for Business Partner master data: create Customer, Supplier, Employee entities, PaymentTerm entity, related value objects, domain events (Created), and port interfaces ICustomerRepository, ISupplierRepository, IEmployeeRepository, IPaymentTermRepository in src/SmeAccounting.Domain/Entities/, ValueObjects/, Events/, Ports/ following CompanyId FK, IsActive soft delete, xmin concurrency, and DomainException validation patterns
- [x] [G2] Implement Infrastructure EF Core configurations and repositories: create *Configuration.cs for each entity in src/SmeAccounting.Infrastructure/Persistence/Configurations/ with snake_case table/column names, HasConversion<string>() for enums, Company FK Restrict, composite unique index (CompanyId, Code), xmin row version; implement Ef*Repository classes in src/SmeAccounting.Infrastructure/Repositories/ with async CRUD
- [x] [G2] Implement Application layer CQRS for Business Partner: create Create/Update/Get/List commands and queries, MediatR handlers, FluentValidation validators, and DTO records for Customer/Supplier/Employee/PaymentTerm in src/SmeAccounting.Application/Commands/, Queries/, Handlers/, DTOs/, Validators/ with ValidationBehavior pipeline
- [x] [G3] Implement API controllers and build verification: create thin MVC controllers in src/SmeAccounting.Api/Controllers/ dispatching MediatR, register services in DI composition root, generate EF migration via dotnet ef migrations add, run dotnet build SmeAccounting.sln and dotnet test tests/SmeAccounting.ArchitectureTests/ to verify Clean Architecture constraints and warnings-as-errors
