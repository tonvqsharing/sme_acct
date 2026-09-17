# ADR-010: Tax Foundation Regulatory Traceability and Architecture Compliance

**Date:** 2026-09-17
**Status:** Accepted
**Context:** Phase 3 — Tax Foundation

## Context

Phase 3 builds Tax Foundation on top of Phase 1 (Accounting Foundation) and Phase 2 (Accounting Control & Posting Configuration). The foundation must be correct, configurable, traceable, and compliant with Vietnamese tax legislation without embedding tax rules into transaction modules.

## Regulatory Scope

The application targets Vietnamese enterprises using:

- **Circular 99/2025/TT-BTC** (effective 01/01/2026): accounting regime reference
- **Law No. 48/2024/QH15** (VAT Law, effective 01/07/2025)
- **Law No. 67/2025/QH15** (CIT Law, effective 01/10/2025)
- **Law No. 109/2025/QH15** (PIT Law, effective 01/07/2026)

Tax rules are NOT inferred from Circular 99 alone. Tax liability/rates/conditions are verified from applicable tax legislation.

## Critical Regulatory Rule

Never implement a tax rate simply because it appears in an old application, database, blog, or code example. For every tax rule:

1. Current Legal Source
2. Applicable Article/Clause
3. Effective Period
4. Tax Business Rule
5. Domain Configuration
6. Automated Test

## Domain Model Implemented

### Phase 3 Domains

1. **Tax Type** (`TaxCategory` enum, `TaxType` entity)
   - VAT, CIT, PIT, Special Consumption, Resource, Environmental, Import/Export Duty
   - Distinguishes different tax concepts with different calculation behavior

2. **Tax Treatment** (`TaxTreatmentType` enum, `TaxTreatment` entity)
   - StandardRate, ReducedRate, ZeroRate, Exempt, NonTaxable
   - `InputCreditAllowed` bool captures 0% vs exempt distinction (Vietnamese VAT Law)
   - 0% rate = deductible input credit; exempt = non-deductible

3. **Tax Authority** (`TaxAuthorityLevel` enum, `TaxAuthority` entity)
   - National, Provincial, District hierarchy per Decision 381/QD-BTC
   - Reference/master data, not hard-coded

4. **Tax Rate** (`TaxRate` entity)
   - Effective dating: EffectiveFrom DateOnly required, EffectiveTo DateOnly? nullable
   - Unique index: (CompanyId, TaxTypeId, RateValue, EffectiveFrom)
   - GetByTaxTypeAndDateAsync implements date range resolution

5. **Tax Rule & Exemption** (`TaxRule` entity, `TaxExemptionReason` entity)
   - TaxRule has 4 FKs: Company, TaxType, TaxRate (nullable), TaxTreatment
   - TaxRateId nullable for exempt/non-taxable rules (no rate applies)
   - LegalReference required for audit traceability
   - Conditions text field for rule conditions
   - GetActiveRulesForDateAsync for effective-date resolution
   - TaxExemptionReason with LegalBasis required

6. **Tax Accounting Mapping** (`TaxAccountingMapping` entity)
   - 4 FKs: Company, TaxType, TaxTreatment, Account
   - MappingType enum: InputVAT, OutputVAT, VATPayable, CITPayable, PITPayable, ImportVAT, TaxDeductible
   - Links to COA per Circular 99:
     - Input VAT → Account 1331/1332
     - Output VAT → Account 33311
     - Import VAT → Account 33312
     - VAT Payable → Account 3331
     - CIT Payable → Account 3334
     - PIT Payable → Account 3335

7. **Tax Period** (`TaxPeriod` entity)
   - FilingFrequency enum: Monthly, Quarterly
   - TaxPeriodStatus enum: Open, Filed, Closed
   - Links to FiscalPeriodId and TaxTypeId
   - Status workflow: Open → Filed → Closed with domain invariants
   - TaxPeriod ≠ FiscalPeriod (different business concepts)

## Architecture Compliance

### Domain Purity
- Domain.csproj has zero NuGet PackageReference elements
- Domain has zero references to Infrastructure, Api, or external packages
- All entities in Domain/Entities/ with private parameterless constructors
- All ports in Domain/Ports/ start with I
- All value objects/enums in Domain/ValueObjects/

### Infrastructure Conventions
- All tables snake_case: `tax_types`, `tax_treatments`, `tax_authorities`, `tax_rates`, `tax_rules`, `tax_exemption_reasons`, `tax_accounting_mappings`, `tax_periods`
- All entities have xmin row version concurrency token
- CompanyId FKs use DeleteBehavior.Restrict
- Unique indexes enforced per-company uniqueness

### Dependency Direction
- Api → Application → Domain → Infrastructure
- Application references Domain only
- Infrastructure implements Domain ports
- All 22 NetArchTest architecture constraints pass

## Historical Integrity

Tax configuration uses effective dating + versioning + transaction snapshot contract:

- EffectiveFrom/EffectiveTo on TaxRate, TaxRule, TaxPeriod
- Changing current configuration does NOT alter interpretation of historical transactions
- Future transaction modules will snapshot Tax Type, Code, Treatment, Rate, Rule Version, Effective Date, Legal Reference

## Test Coverage

- 22/22 architecture tests pass
- Domain entities follow BaseEntity pattern with DomainException validation
- Application layer uses CQRS with MediatR and FluentValidation
- Build succeeds with TreatWarningsAsErrors=true, zero warnings

## Regulatory Traceability

| Legal Source | Article | Domain Entity | Implementation |
|--------------|---------|---------------|----------------|
| Law 48/2024/QH15 | Art. 4 | TaxRate | 0% VAT for exports |
| Law 48/2024/QH15 | Art. 5 | TaxExemptionReason | VAT-exempt goods |
| Law 48/2024/QH15 | Art. 9 | TaxTreatment | 5%/8%/10% rates |
| Law 67/2025/QH15 | Art. 11 | TaxRate | CIT 20%/15%/17% |
| Law 109/2025/QH15 | Art. 9 | TaxRate | PIT 5/10/20/30/35% |
| Circular 99/2025 | Art. 28 | TaxAccountingMapping | Account 1331/3331/3334/3335 |

## Decisions

1. **TaxType → TaxCategory enum rename**: Avoid C# namespace collision with TaxType entity
2. **TaxRateId nullable on TaxRule**: Supports exempt/non-taxable rules without rate
3. **LegalReference required**: All material tax rules must be traceable to legal source
4. **InputCreditAllowed bool**: Captures critical 0% vs exempt distinction in Vietnamese VAT
5. **Separate TaxPeriod from FiscalPeriod**: Different concepts despite alignment
6. **No tax calculation engine**: Foundation only, no transaction processing

## Non-Goals

- No VAT/CIT/PIT calculation engine
- No tax declarations or returns
- No e-invoice integration
- No sales/purchase tax processing
- No payroll tax calculation
- No GL posting (future transaction modules will consume foundation)

## Conclusion

Phase 3 Tax Foundation is complete. 8 tax entities implemented with full regulatory traceability, architecture compliance, and historical integrity. Ready for Phase 4 transaction modules.
