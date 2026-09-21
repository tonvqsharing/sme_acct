# Company / CompanySetting Domain Design Summary

Task: [G1] Design Company/CompanySetting domain entities, value objects, events, ports, and EF configurations with company isolation and VAS compliance

## Domain Entities

### Company
- File: src/SmeAccounting.Domain/Entities/Company.cs
- Extends BaseEntity
- Private parameterless ctor for EF
- Public ctor validates with DomainException:
  - Name, TaxCode, Address, FunctionalCurrencyCode required non-empty
  - FiscalYearStartMonth 1-12
  - FiscalYearStartDay 1-28
- Properties: Name, TaxCode, Address, Phone?, Email?, FiscalYearStartMonth, FiscalYearStartDay, FunctionalCurrencyCode, IsActive
- Raises CompanyCreated domain event on construction
- VAS compliance: TaxCode, Legal representative via CompanySetting, Fiscal year start, Functional currency

### CompanySetting
- File: src/SmeAccounting.Domain/Entities/CompanySetting.cs
- Extends BaseEntity
- Private parameterless ctor for EF
- Public ctor validates with DomainException:
  - CompanyId > 0
  - LegalRepresentativeName required
  - LegalRepresentativeTaxId required
  - FiscalYearStartMonth 1-12 if provided
- Properties: CompanyId, LegalRepresentativeName, LegalRepresentativeTaxId, ChiefAccountantName?, ChiefAccountantTaxId?, FiscalYearStartMonth?, Currency?, ReportingSettingsJson?
- Raises CompanySettingCreated domain event on construction
- VAS compliance: Legal representative/chief accountant tax IDs, fiscal year start, currency, reporting settings jsonb

## Value Objects
- No dedicated value objects for Company/CompanySetting currently; FunctionalCurrencyCode and Currency stored as string per Money VO pattern.
- Potential future value objects: TaxCode, FiscalYearStart

## Domain Events

### CompanyCreated
- File: src/SmeAccounting.Domain/Events/CompanyCreated.cs
- Properties: CompanyId
- Base DomainEvent provides OccurredOn

### CompanySettingCreated
- File: src/SmeAccounting.Domain/Events/CompanySettingCreated.cs
- Properties: SettingId, CompanyId
- Base provides OccurredOn
- Minimalism: entity ID + company ID + timestamp only

## Ports

### ICompanyRepository
- File: src/SmeAccounting.Domain/Ports/ICompanyRepository.cs
- Methods: GetByIdAsync, GetByTaxCodeAsync, GetAllAsync, AddAsync

### ICompanySettingRepository
- File: src/SmeAccounting.Domain/Ports/ICompanySettingRepository.cs
- Methods: GetByIdAsync, GetByCompanyIdAsync, AddAsync

## EF Configurations

### CompanyConfiguration
- File: src/SmeAccounting.Infrastructure/Persistence/Configurations/CompanyConfiguration.cs
- Table: companies
- Snake_case columns: name, tax_code, address, phone, email, fiscal_year_start_month, fiscal_year_start_day, functional_currency_code, is_active, id, xmin
- Unique index: tax_code
- Row version: xmin
- No FK

### CompanySettingConfiguration
- File: src/SmeAccounting.Infrastructure/Persistence/Configurations/CompanySettingConfiguration.cs
- Table: company_settings
- Snake_case columns: company_id, legal_representative_name, legal_representative_tax_id, chief_accountant_name, chief_accountant_tax_id, fiscal_year_start_month, currency, reporting_settings_json, id, xmin
- Unique index: company_id (1:1 per company)
- FK: HasOne<Company>().WithMany().HasForeignKey(CompanyId).OnDelete(DeleteBehavior.Restrict)
- Column type: reporting_settings_json jsonb
- Row version: xmin

## Company Isolation
- CompanySetting FK to Company with DeleteBehavior.Restrict
- Unique index on CompanyId ensures 1:1 setting per company
- No navigation properties exposed in domain entities
- Repositories filter by companyId where applicable

## VAS Compliance
- Circular 99/2025/TT-BTC requirements captured via:
  - Company TaxCode
  - CompanySetting Legal Representative TaxId, Chief Accountant TaxId
  - Fiscal year start month/day
  - Functional currency code
  - ReportingSettingsJson for VAS-specific reporting configuration

## Build Verification
- Domain project builds with 0 warnings
- Patterns enforced: BaseEntity, private parameterless ctor, public validating ctor with DomainException, domain events minimalism, EF snake_case/xmin/FK Restrict

Updated: 2026-09-21
