# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
- Domain entities follow pattern: private parameterless ctor for EF, public ctor validates CompanyId>0, Code/Name non-whitespace with DomainException, IsActive default true, AddDomainEvent with Id (0 at construction) and CompanyId, DateTimeOffset.UtcNow
- PaymentTermType enum added to Domain/ValueObjects/ with Net, DueOnReceipt, DaysAfterInvoice, EndOfMonth
- Customer/Supplier/Employee/PaymentTerm entities include optional contact fields (TaxCode, Address, Phone, Email) and soft delete via Deactivate()
- Supplier includes optional PaymentTermId and DefaultTaxTypeId FKs for tax integration
- Employee includes EmployeeNumber and HireDate (DateOnly?) for HR tracking
- Port interfaces use GetAllByCompanyAsync pattern consistent with TaxType, not GetAllAsync
- IEmployeeRepository adds GetByEmployeeNumberAsync for unique employee lookup
- All entities have private setters, no navigation properties to Company, FK configured in EF only
- Domain events minimal: EntityId + CompanyId + OccurredOn, matching DepartmentCreated pattern
- EF configurations already existed for Customer/Supplier/Employee/PaymentTerm with snake_case tables, composite unique (CompanyId, Code), xmin row version, Company FK Restrict, enum conversion for PaymentTermType
- Repositories implemented using _context.Set<T>() pattern since DbSet properties not added to SmeAccountingDbContext; async methods follow EfTaxTypeRepository pattern with AsNoTracking for GetAllByCompanyAsync
- OnModelCreating updated to ignore CustomerCreated, SupplierCreated, EmployeeCreated, PaymentTermCreated domain events to prevent EF mapping errors
- Build succeeds with 0 warnings 0 errors after repository implementation
- Application CQRS for Employee and PaymentTerm follows Customer/Supplier pattern: Create/Deactivate commands as records, FluentValidation validators with max lengths, DTO records, GetById and GetAllByCompany queries, internal sealed handlers injecting repository + IUnitOfWork, mapping enum to string in DTO
- EmployeeDto already existed; PaymentTermDto created with PaymentTermType as string
- CreateEmployeeCommand includes EmployeeNumber, TaxCode, Address, Phone, Email, HireDate, Description; validator enforces max lengths matching EF config
- CreatePaymentTermCommand includes PaymentTermType enum and nullable Days; validator checks IsInEnum and Days >=0
- Handlers use domain entity constructors, repository.AddAsync, unitOfWork.SaveChangesAsync for commands; queries map entities to DTOs without tracking
- Build succeeds with 0 warnings 0 errors after Application layer implementation
- API controllers created: CustomerController, SupplierController, EmployeeController, PaymentTermController in src/SmeAccounting.Api/Controllers/ with thin MediatR dispatch, ValidationException handling, RedirectToAction pattern
- ViewModels created: CreateCustomerViewModel, CreateSupplierViewModel, CreateEmployeeViewModel, CreatePaymentTermViewModel with DataAnnotations matching EF config max lengths
- DI registration added for ICustomerRepository, ISupplierRepository, IEmployeeRepository, IPaymentTermRepository in Infrastructure/DependencyInjection.cs
- EF migration BusinessPartnerFoundation generated via dotnet ef migrations add, pending migration for Customer/Supplier/Employee/PaymentTerm tables
- Build verified: dotnet build SmeAccounting.sln succeeds 0 warnings 0 errors
- Architecture tests verified: dotnet test tests/SmeAccounting.ArchitectureTests/ passes 22/22, Clean Architecture constraints maintained
