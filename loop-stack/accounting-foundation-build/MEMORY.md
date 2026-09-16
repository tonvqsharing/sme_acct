# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings

### T1 — Company Entity + Currency Promotion
- Currency VO record in `ValueObjects/Currency.cs` is NOT referenced anywhere as a type. Money uses `string Currency` not the VO. Safe to have both VO and entity with different namespaces
- Company entity validates fiscalYearStartMonth (1–12) and fiscalYearStartDay (1–28) in constructor. TaxCode regex validation deferred to FluentValidation layer
- Currency entity: Code validated as exactly 3 uppercase chars. Unique index on Code. Entity has Symbol, DecimalPlaces, IsDefault, IsActive
- Port interfaces: ICompanyRepository has GetByTaxCodeAsync; ICurrencyRepository has GetByCodeAsync (both unique in DB)
- Both EF configurations use unique indexes: companies.tax_code, currencies.code
- FK note: FiscalYear, FiscalPeriod, Account, AccountGroup, JournalEntry all need CompanyId FK — implemented in T2/T4/T5
- Company.FunctionalCurrencyCode is `string` not FK — matches Money VO pattern (Money stores currency as string too)
- Namespace: new Currency entity is `SmeAccounting.Domain.Entities.Currency` — different from `SmeAccounting.Domain.ValueObjects.Currency`
- Domain events raised in constructors: CompanyCreated and CurrencyCreated (matches AccountCreated pattern)
