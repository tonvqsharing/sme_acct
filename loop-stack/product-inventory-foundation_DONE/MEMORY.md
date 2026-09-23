# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
- UOM implemented following Department pattern: Domain entity with CompanyId/Code/Name/Symbol/IsActive/Description, UomCreated event, IUomRepository port, EfUomRepository, UomConfiguration snake_case, unique index (CompanyId, Code), xmin concurrency.
- DbContext updated with DbSet<Uom> and Ignore<UomCreated>.
- DI registered IUomRepository → EfUomRepository.
- Application layer: CreateUomCommand, DeactivateUomCommand, GetUomQuery/GetUomsByCompanyQuery, handlers, UomDto, CreateUomCommandValidator.
- API controller UomController thin MediatR dispatch.
- Build succeeds 0 warnings, architecture tests 22/22 pass.
- EF migration AddUom created successfully.
- Consolidated UOM master-data pattern reusable for Product & Inventory Foundation: Company-scoped entity with Code/Name/Symbol/IsActive/Description, unique (CompanyId,Code) index, domain Created event, port with GetByCodeAsync/GetAllByCompanyAsync, EF snake_case config with xmin concurrency, DI registration, CQRS Create/Deactivate/Get with FluentValidation, thin MediatR API controller, migration succeeds, build 0 warnings, architecture tests 22/22 pass — same pattern applies to Item Category, Item/Product, Service Item, Warehouse, Valuation Policy, Adjustment Reason, Accounting Configuration.
