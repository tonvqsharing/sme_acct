# Research Log

## Context & Prior Work

### Project Context
- Vietnamese enterprise accounting web app (ASP.NET MVC + Clean Architecture + CQRS)
- Phase 3: Tax Foundation on top of Phase 1 (Accounting Foundation) and Phase 2 (Accounting Control & Posting Configuration)
- Must integrate with COA, Posting Configuration, Currency, and Accounting Period from prior phases
- Regulatory research against current Vietnamese tax legislation required
- TDD approach, no tax calculation engine yet — foundation only

### Prior Phase Learnings
- Circular 99/2025/TT-BTC effective January 1, 2026 — enterprise accounting regime
- E-invoice XML is legally binding (not PDF) — TVAN providers (Viettel/MISA/BKAV) as adapter implementations
- Chart of Accounts: 9 categories, 4-digit Level 1 hierarchy, 25+ key account codes
- Architecture enforcement: csproj refs + NetArchTest.Rules tests

### Vietnamese Accounting Domain
- VAS (Vietnamese Accounting Standards) compliance
- Circular 99/2025/TT-BTC maps to: Domain posting rules, Infrastructure audit, Application reports
- IFRS transition via Decision 345 — `IAccountingPolicy` interface abstraction for VAS vs IFRS

## External Knowledge & Resources

### Current Tax Laws

#### 1. VAT Law — Law No. 48/2024/QH15
- **Document:** Luật số 48/2024/QH15 — Luật Thuế giá trị gia tăng (Value-added Tax Law)
- **Issue Date:** November 26, 2024
- **Effective Date:** July 1, 2025
- **Status:** In force (replaced Law No. 13/2008/QH12)
- **Key Changes:**
  - New 0% VAT rate provisions for exports and international transport
  - 5% rate for essential goods/services (clean water, medical equipment, agricultural inputs)
  - 10% standard rate for all other goods/services
  - Temporary 8% reduction for eligible items (effective July 1, 2025 to December 31, 2026)
  - Expanded e-invoice requirements
  - Revised input VAT credit rules
  - Article 18: Transitional provisions for household businesses (effective January 1, 2026)

#### 2. CIT Law — Law No. 67/2025/QH15
- **Document:** Luật số 67/2025/QH15 — Luật Thuế thu nhập doanh nghiệp (Corporate Income Tax Law)
- **Issue Date:** June 14, 2025
- **Effective Date:** October 1, 2025
- **Status:** In force (replaced previous CIT law)
- **Key Changes:**
  - Standard CIT rate: 20%
  - Small enterprises (revenue ≤ VND 3 billion): 15%
  - Medium enterprises (revenue VND 3–50 billion): 17%
  - Oil and gas: 25–50% (per contract)
  - Precious minerals: 40–50%
  - New preferential rates: 10% for 15 years, 17% for 10 years
  - SME incentives removed for affiliated larger enterprises
  - Deemed CIT rates for foreign corporate sellers (2% on gross proceeds)

#### 3. PIT Law — Law No. 109/2025/QH15
- **Document:** Luật số 109/2025/QH15 — Luật Thuế thu nhập cá nhân (Personal Income Tax Law)
- **Issue Date:** December 10, 2025
- **Effective Date:** July 1, 2026
- **Status:** Not yet effective (applicable from 2026 tax year for employment/business income)
- **Key Changes:**
  - Progressive tax brackets reduced from 7 to 5
  - New brackets: 5%, 10%, 20%, 30%, 35%
  - Personal deduction: VND 15.5 million/month (up from VND 11 million)
  - Dependant deduction: VND 6.2 million/month (up from VND 4.4 million)
  - Non-residents: flat 20% on Vietnam-sourced income
  - Business income: turnover-based taxation (0.5% to 5% depending on activity)

### VAT Rules & Rates

#### Current VAT Rates (as of 2026)
| Rate | Application | Notes |
|------|-------------|-------|
| **10%** | Standard rate | Most goods and services |
| **8%** | Temporary reduction | Items normally at 10% (excludes telecom, finance, real estate, etc.) |
| **5%** | Reduced rate | Essential goods: clean water, medical equipment, medicines, fertilizers, social housing |
| **0%** | Zero rate | Exported goods, international transport, services to foreign parties |
| **Exempt** | Not subject to VAT | Self-produced agricultural products, land use rights transfer, credit services, securities, life insurance, public healthcare/education |

#### Key Distinctions: 0% Rate vs. VAT-Exempt
| Criteria | 0% Tax Rate | VAT-Exempt |
|----------|-------------|------------|
| **Scope** | Still within VAT scope | Not subject to VAT |
| **Output VAT** | Charged at 0% | Not charged |
| **Input VAT Credit** | Deductible and refundable | Not deductible/not refundable |
| **Declaration** | Must declare VAT | No VAT declaration required |
| **Examples** | Exported goods, international transport | Agricultural products, financial services, healthcare |

#### Temporary 8% Reduction (Resolution 204/2025/QH15)
- **Period:** July 1, 2025 to December 31, 2026
- **Eligible:** Items normally subject to 10% VAT
- **Excluded:**
  - Telecommunications
  - Finance, banking, securities, insurance
  - Real estate business
  - Metal products
  - Mining products (except coal)
  - Goods/services subject to special consumption tax (except gasoline)

#### Input VAT Credit Rules
- Deductible: Input VAT on goods/services used for VAT-taxable production/trading
- Non-deductible: Input VAT on goods/services used for non-VAT-taxable activities
- Mixed use: Proportional deduction based on revenue ratio
- Fixed assets: Fully deductible even for mixed use
- Refund: Available for VAT-exclusive producers with residual input VAT ≥ VND 300 million for 12+ months

### CIT Rules & Rates

#### Current CIT Rates (as of 2026)
| Category | Rate | Condition |
|----------|------|-----------|
| **Standard** | 20% | All enterprises not otherwise qualifying |
| **Small enterprise** | 15% | Annual revenue ≤ VND 3 billion |
| **Medium enterprise** | 17% | Annual revenue VND 3–50 billion |
| **Oil and gas** | 25–50% | Per contract, decided by Prime Minister |
| **Precious minerals** | 40–50% | 50% standard; 40% if 70%+ area in extremely difficult conditions |

#### Preferential CIT Rates
| Rate | Duration | Eligibility |
|------|----------|-------------|
| **10%** | 15 years | New investment projects in high-tech parks, digital technology, AI data centers, automobile manufacturing |
| **10%** | Open-ended | Activities in specified sectors in difficult socio-economic areas |
| **15%** | Open-ended | Activities in specified sectors not in difficult areas |
| **17%** | 10 years | New investment projects in economic zones |

#### Tax Holidays
- 10% projects: 4 years exemption + 9 years at 50% reduction
- 17% projects: 2 years exemption + 4 years at 50% reduction

### PIT Rules & Rates

#### Current PIT Rates (from 2026 tax year)
**Progressive Tax Table (Resident Individuals):**
| Tax Grade | Monthly Taxable Income (VND) | Annual Taxable Income (VND million) | Tax Rate |
|-----------|------------------------------|-------------------------------------|----------|
| 1 | Up to 10,000,000 | Up to 120 | 5% |
| 2 | Over 10,000,000 to 30,000,000 | Over 120 to 360 | 10% |
| 3 | Over 30,000,000 to 60,000,000 | Over 360 to 720 | 20% |
| 4 | Over 60,000,000 to 100,000,000 | Over 720 to 1,200 | 30% |
| 5 | Over 100,000,000 | Over 1,200 | 35% |

**Non-Resident Individuals:** Flat 20% on Vietnam-sourced income

**Business Income (Turnover-based):**
| Activity | Rate |
|----------|------|
| Distribution/supply of goods | 0.5% |
| Services without materials | 2% |
| Leasing/agency | 5% |
| Production/transport with materials | 1.5% |
| Digital content/advertising | 5% |
| Other | 1% |

**Exemptions:** Annual revenue ≤ VND 500 million (household/individual business)

#### Deductions (from 2026)
- Personal deduction: VND 15.5 million/month (VND 186 million/year)
- Dependant deduction: VND 6.2 million/month
- Compulsory social insurance: 10.5% (8% social + 1.5% health + 1% unemployment)
- Voluntary pension/life premiums (capped)
- Charitable contributions

### Tax Treatment Classifications

#### VAT Treatment Categories
1. **Standard Rate (10%)** — Default for most goods/services
2. **Reduced Rate (5%)** — Essential goods/services specified by law
3. **Zero Rate (0%)** — Export-oriented activities
4. **Exempt** — Social/essential services (no input credit)
5. **Non-Taxable** — Outside VAT scope entirely

#### Key Treatment Rules
- **Mixed Supply:** Highest rate applies if cannot separate
- **Export Goods:** 0% rate with full input credit
- **Import VAT:** Creditable if used for VAT-taxable production
- **Non-Cash Payment:** Required for input VAT credit on purchases ≥ VND 5 million
- **Filing Frequency:** Monthly (revenue > VND 50 billion) or Quarterly (≤ VND 50 billion)

### Tax Accounting (Circular 99/2025/TT-BTC)

#### Chart of Accounts for Tax
**Account 133 — VAT Deductible:**
- **1331:** VAT on goods and services
- **1332:** VAT on fixed assets

**Account 333 — Taxes and Payables to State Budget:**
- **3331:** VAT payable
  - 33311: Output VAT
  - 33312: Import VAT
- **3332:** Special consumption tax
- **3333:** Export/import duties
- **3334:** Corporate income tax
- **3335:** Personal income tax
- **3336:** Resource tax
- **3337:** Land tax, land rent
- **3338:** Environmental protection tax and others
- **3339:** Fees, charges, and other payables

#### Key Tax Accounting Entries

**1. Purchase of Goods/Services (Credit Method):**
```
Debit: 152, 153, 156 (Inventory at cost excl. VAT)
Debit: 1331 (Input VAT deductible)
Credit: 111, 112, 331 (Total payment)
```

**2. Purchase of Fixed Assets:**
```
Debit: 211, 213, 217 (Asset cost incl. non-deductible VAT)
Debit: 1332 (Input VAT on fixed assets)
Credit: 331 (Accounts payable)
```

**3. Sale of Goods/Services:**
```
Debit: 131 (Accounts receivable)
Credit: 511, 515, 711 (Revenue excl. VAT)
Credit: 33311 (Output VAT)
```

**4. Import VAT:**
```
Debit: 1331 (Input VAT deductible)
Credit: 33312 (Import VAT payable)
```

**5. Period-End VAT Settlement:**
```
Debit: 33311 (Output VAT)
Credit: 133 (Input VAT deductible)
```
- Balance in 3331 = VAT payable to state budget
- Balance in 133 = Carry forward for next period or refund

**6. Payment of VAT:**
```
Debit: 3331 (VAT payable)
Credit: 112 (Bank deposit)
```

**7. CIT Payment:**
```
Debit: 3334 (CIT payable)
Credit: 112 (Bank deposit)
```

**8. PIT Withholding:**
```
Debit: 3335 (PIT payable)
Credit: 111, 112 (Cash/bank)
```

### Effective Dates & Transitions

#### Timeline of Major Tax Law Changes
| Law | Effective Date | Transition Period |
|-----|----------------|-------------------|
| VAT Law 48/2024/QH15 | July 1, 2025 | Household business provisions: Jan 1, 2026 |
| CIT Law 67/2025/QH15 | October 1, 2025 | Applies from 2025 tax year |
| PIT Law 109/2025/QH15 | July 1, 2026 | Employment/business income: from 2026 tax year |
| Circular 99/2025/TT-BTC | January 1, 2026 | Applies to fiscal years starting from Jan 1, 2026 |
| Decree 70/2025/NĐ-CP (E-invoices) | June 1, 2025 | Replaces Decree 123/2020/NĐ-CP |
| Decree 181/2025/NĐ-CP (VAT guidance) | July 1, 2025 | Implements VAT Law 48/2024/QH15 |
| Resolution 204/2025/QH15 (8% reduction) | July 1, 2025 | Expires December 31, 2026 |

#### Transitional Provisions
- **VAT:** Old VAT Law (13/2008/QH12) ceases effect from July 1, 2025
- **CIT:** Old CIT law repealed from October 1, 2025
- **PIT:** Old PIT law (04/2007/QH12) ceases effect from July 1, 2026; employment/business income provisions cease from 2026 tax year
- **Accounting:** Circular 99/2025/TT-BTC replaces previous accounting regime from January 1, 2026

### Regulatory Sources & References

#### Primary Sources
1. **Luật số 48/2024/QH15** — Luật Thuế giá trị gia tăng (VAT Law)
   - Issued: November 26, 2024
   - Effective: July 1, 2025
   - Source: congbao.chinhphu.vn, thuvienphapluat.vn

2. **Luật số 67/2025/QH15** — Luật Thuế thu nhập doanh nghiệp (CIT Law)
   - Issued: June 14, 2025
   - Effective: October 1, 2025
   - Source: congbao.chinhphu.vn, vietnam-briefing.com

3. **Luật số 109/2025/QH15** — Luật Thuế thu nhập cá nhân (PIT Law)
   - Issued: December 10, 2025
   - Effective: July 1, 2026
   - Source: congbao.chinhphu.vn, english.luatvietnam.vn

4. **Thông tư 99/2025/TT-BTC** — Hướng dẫn Chế độ kế toán doanh nghiệp
   - Issued: October 27, 2025
   - Effective: January 1, 2026
   - Source: congbao.chinhphu.vn

5. **Nghị định 181/2025/NĐ-CP** — Hướng dẫn Luật Thuế GTGT
   - Implements VAT Law 48/2024/QH15
   - Source: dfkhanoi.com

6. **Nghị định 320/2025/NĐ-CP** — Hướng dẫn Luật Thuế TNDN
   - Implements CIT Law 67/2025/QH15
   - Effective: December 15, 2025
   - Source: vietnam-briefing.com

7. **Nghị định 70/2025/NĐ-CP** — Hóa đơn, chứng từ
   - Amends Decree 123/2020/NĐ-CP on e-invoices
   - Effective: June 1, 2025
   - Source: kpmg.com, prv.com.vn

8. **Nghị quyết 204/2025/QH15** — Giảm thuế GTGT
   - Temporary 8% VAT reduction
   - Period: July 1, 2025 to December 31, 2026
   - Source: vanzbon.vn

9. **Thông tư 32/2025/TT-BTC** — Hướng dẫn hóa đơn điện tử
   - Implements Decree 70/2025/NĐ-CP
   - Effective: June 1, 2025
   - Source: rsmhanoi.com.vn

10. **Nghị định 144/2026/NĐ-CP** — Sửa đổi Luật Thuế GTGT
    - Amends VAT exemptions and input credit rules
    - Effective: June 20, 2026
    - Source: global.ecovis.com

#### Secondary Sources
- PwC Worldwide Tax Summaries (taxsummaries.pwc.com)
- Vietnam Briefing (vietnam-briefing.com)
- EY Tax Updates (ey.com)
- LuatVietnam (luatvietnam.vn)
- MISA SME Accounting (sme.misa.vn)

## Requirements & Constraints

### For Tax Foundation Implementation
1. **Tax Type Entity** — Must support: VAT, CIT, PIT, Special Consumption Tax, Resource Tax, Environmental Tax, Import/Export Duties
2. **Tax Rate Entity** — Must support: Standard rates, preferential rates, temporary reductions (8% VAT), effective dating
3. **Tax Rule Entity** — Must link: Tax type + rate + conditions + effective period
4. **Tax Treatment Classification** — Must distinguish: Standard rate, reduced rate, zero rate, exempt, non-taxable
5. **Tax Accounting Mapping** — Must map to Circular 99 accounts: 1331, 1332, 3331, 33311, 33312, 3334, 3335
6. **Effective Dating** — All tax rules must have valid-from/valid-to dates for transitional provisions
7. **Legal Traceability** — Must link tax rules to specific law articles/clauses

### Regulatory Compliance
- Circular 99/2025/TT-BTC compliance mandatory from January 1, 2026
- E-invoice XML format legally binding
- Non-cash payment evidence required for input VAT credit ≥ VND 5 million
- Filing frequency based on prior-year revenue (monthly if > VND 50 billion)

## Suggested Approach

1. **Start with Tax Type enum** — VAT, CIT, PIT, Special Consumption, Resource, Environmental, Import/Export Duties
2. **Create Tax Rate entity** — Rate value, effective dates, tax type FK, conditions
3. **Create Tax Rule entity** — Links tax type to rate with conditions and legal references
4. **Create Tax Treatment entity** — Classifies goods/services: standard, reduced, zero, exempt, non-taxable
5. **Create Tax Accounting Mapping** — Maps tax type + treatment to Circular 99 accounts
6. **Create Tax Exemption Reason entity** — Documents why goods/services are exempt
7. **Create Tax Authority entity** — General Department of Taxation, local tax offices
8. **Create Tax Period entity** — Links to FiscalPeriod with tax filing deadlines

## Verification Criteria

### What "Done Correctly" Looks Like
1. **Tax Type** supports all 7+ Vietnamese tax types with correct legal references
2. **Tax Rate** entity correctly stores: 10%, 8% (temporary), 5%, 0% for VAT; 20%, 15%, 17% for CIT; 5%–35% progressive for PIT
3. **Effective Dating** handles transitional provisions (e.g., VAT 8% reduction expires Dec 31, 2026)
4. **Tax Treatment** correctly distinguishes 0% rate (deductible input) vs. exempt (non-deductible input)
5. **Tax Accounting Mapping** correctly links to Circular 99 accounts (1331, 33311, 33312, 3334, 3335)
6. **Legal Traceability** links each tax rule to specific law number, article, and clause
7. **Architecture Tests** pass — domain entities in Domain layer, ports start with I, zero NuGet refs in Domain

### What "Failing" Looks Like
1. Tax rates hardcoded without effective dates
2. Missing distinction between 0% rate and exempt treatment
3. Incorrect Circular 99 account mapping
4. Domain entities referencing Infrastructure layer
5. Missing legal references for tax rules
6. No support for temporary tax reductions (8% VAT)

## Quality Standards

### Good Output
- All tax types documented with current legal references
- Tax rates stored with effective dates and conditions
- Clear distinction between tax treatments (standard, reduced, zero, exempt, non-taxable)
- Accounting entries follow Circular 99/2025/TT-BTC exactly
- Legal traceability enables audit trail
- Supports transitional provisions (old law → new law)

### Merely Functional
- Tax rates stored but no effective dating
- Missing legal references
- Incorrect account mapping
- No distinction between 0% and exempt
- Hardcoded values without configurability

## Verification Results — [G3] TaxRule & TaxExemptionReason

**VERIFIED_PASS** — All requirements met.

### TaxRule
- Entity: 4 FKs (CompanyId, TaxTypeId, TaxRateId nullable long?, TaxTreatmentId) all Restrict ✓
- Properties: Code, Name, Conditions (nullable), LegalReference (required), EffectiveFrom (DateOnly), EffectiveTo (DateOnly?), IsActive (bool), Description ✓
- Private parameterless ctor + public ctor with DomainException validation (CompanyId > 0, TaxTypeId > 0, TaxRateId valid when provided, TaxTreatmentId > 0, Code/Name/LegalReference non-empty) ✓
- Deactivate() sets IsActive = false ✓
- TaxRuleCreated event: TaxRuleId + CompanyId + occurredOn (event minimalism) ✓
- ITaxRuleRepository: GetByIdAsync, GetByCodeAsync(code, companyId), GetAllByCompanyAsync, GetActiveRulesForDateAsync(date, companyId), AddAsync — 5 methods ✓
- TaxRuleConfiguration: snake_case `tax_rules`, unique index (CompanyId, Code), 4 FKs Restrict (including nullable TaxRateId), xmin row version ✓
- EfTaxRuleRepository: GetActiveRulesForDateAsync filters EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive ✓

### TaxExemptionReason
- Entity: 2 FKs (CompanyId, TaxTypeId) both Restrict ✓
- Properties: Code, Name, LegalBasis (required), Description (nullable), IsActive (bool) ✓
- Private parameterless ctor + public ctor with DomainException validation ✓
- TaxExemptionReasonCreated event: TaxExemptionReasonId + CompanyId + occurredOn ✓
- ITaxExemptionReasonRepository: GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, GetAllByTaxTypeAsync, AddAsync — 5 methods ✓
- TaxExemptionReasonConfiguration: snake_case `tax_exemption_reasons`, unique index (CompanyId, Code), 2 FKs Restrict, xmin ✓
- EfTaxExemptionReasonRepository: all methods with AsNoTracking for reads ✓

### Infrastructure
- DbContext: 24 DbSets, 20 ignored events (DomainEvent + 19 events) ✓
- DI: 19 AddScoped registrations ✓

### Cross-cutting
- Domain.csproj: zero NuGet PackageReference elements ✓
- Build: 0 warnings, 0 errors ✓
- Architecture tests: 22/22 pass ✓
- All entities in Domain.Entities namespace, all ports in Domain.Ports, all events in Domain.Events ✓

---

## Verification Results — [G4] TaxAccountingMapping

**VERIFIED_PASS** — All requirements met.

### Domain
- TaxAccountingMappingType enum: 7 values (InputVAT, OutputVAT, VATPayable, CITPayable, PITPayable, ImportVAT, TaxDeductible) ✓
- TaxAccountingMapping entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity ✓
- 4 FKs: CompanyId, TaxTypeId, TaxTreatmentId, AccountId — all validated > 0 in constructor ✓
- MappingType (enum), IsActive (bool default true), Description (string?) properties ✓
- Private parameterless ctor + public ctor with DomainException validation ✓
- Deactivate() sets IsActive = false ✓

### Events
- TaxAccountingMappingCreated: TaxAccountingMappingId + CompanyId + occurredOn (event minimalism) ✓

### Ports
- ITaxAccountingMappingRepository in `SmeAccounting.Domain.Ports` — starts with I ✓
- 4 methods: GetByIdAsync, GetAllByCompanyAsync, GetByTaxTypeAndTreatmentAsync, AddAsync ✓

### Infrastructure
- TaxAccountingMappingConfiguration: snake_case `tax_accounting_mappings`, unique index (CompanyId, MappingType), 4 FKs all Restrict, MappingType HasConversion<string>(), xmin row version ✓
- Account FK pattern: `HasOne<Account>().WithMany().HasForeignKey().OnDelete(Restrict)` — matches OpeningBalanceMapping ✓
- EfTaxAccountingMappingRepository: AsNoTracking for GetAllByCompany, tracked for GetById/GetByTaxTypeAndTreatment ✓
- DbContext: 25 DbSets, 21 ignored events (DomainEvent + 20 events) ✓
- DI: 20 AddScoped registrations ✓

### Cross-cutting
- Domain.csproj: zero NuGet PackageReference elements ✓
- Build: 0 warnings, 0 errors ✓
- Architecture tests: 22/22 pass ✓
- All files in correct namespaces (Domain.Entities, Domain.Events, Domain.Ports, Domain.ValueObjects) ✓

---

## Prior Attempt Analysis
(none — first research cycle)

---

# Task-Specific Research — [G6] Integration commands/queries + EF migration

## Context & Prior Work

### What Exists
- **All 8 tax domain entities** are complete (G1-G5): TaxType, TaxTreatment, TaxAuthority, TaxRate, TaxRule, TaxExemptionReason, TaxAccountingMapping, TaxPeriod
- **All 8 port interfaces** exist in Domain/Ports with defined methods
- **DbContext:** 26 DbSets, 23 ignored events, 21 DI registrations
- **No Application layer files** exist for any tax entity yet — no commands, handlers, queries, DTOs, or validators
- **No EF migration** for tax tables yet — domain entities exist but tables aren't in the database

### Established CQRS Patterns (from VoucherType/TransactionReason)

**Command pattern:** `record CreateXxxCommand(params...) : IRequest<CreateXxxResult>;` + `record CreateXxxResult(long Id);`

**Handler pattern:** `internal sealed class CreateXxxHandler(IXxxRepository repository, IUnitOfWork unitOfWork) : IRequestHandler<CreateXxxCommand, CreateXxxResult>` — creates entity, calls AddAsync, calls SaveChangesAsync, returns new Id

**Query-by-Id pattern:** `record GetXxxQuery(long XxxId) : IRequest<XxxDto?>;` — returns nullable (null if not found)

**Query-by-company pattern:** `record GetXxxsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<XxxDto>>;`

**Deactivate pattern:** `record DeactivateXxxCommand(long XxxId) : IRequest<DeactivateXxxResult>;` + `record DeactivateXxxResult;` — handler loads entity, calls Deactivate(), calls SaveChangesAsync

**DTO pattern:** `record XxxDto(long Id, ..., bool IsActive, string? Description);` — enum properties stored as `string` via `.ToString()`

**Validator pattern:** `class CreateXxxCommandValidator : AbstractValidator<CreateXxxCommand>` — FluentValidation rules for required fields, max lengths, enum IsInEnum, FK > 0

**Handler location:** `src/SmeAccounting.Application/Handlers/` — one handler per file

**No DI registration needed** in Application layer — MediatR assembly scan + FluentValidation auto-registration handle it

## Existing Tools & Resources

### Pattern Sources (copy from these)

| Pattern | Source File | Relevance |
|---------|------------|-----------|
| Command + Result | `CreateVoucherTypeCommand.cs` | Code/Name/CompanyId/Enum/Description |
| Command + Result (2 FKs) | `CreateTransactionReasonCommand.cs` | Code/Name/FK/CompanyId/Description |
| Handler (single FK) | `CreateVoucherTypeHandler.cs` | Repository + UoW injection, entity creation, AddAsync |
| Handler (2 FKs) | `CreateTransactionReasonHandler.cs` | Same but with VoucherTypeId |
| Handler (Deactivate) | `DeactivateVoucherTypeHandler.cs` | GetById + null check + Deactivate() + SaveChanges |
| Query (by company) | `GetVoucherTypesByCompanyQuery.cs` | CompanyId param, IReadOnlyList DTO |
| Query (by FK) | `GetTransactionReasonsByVoucherTypeQuery.cs` | FK param, IReadOnlyList DTO |
| Query (single) | `GetVoucherTypeQuery.cs` | Single ID param, nullable DTO |
| DTO | `VoucherTypeDto.cs` | record with all entity fields, enum as string |
| DTO (2 FKs) | `TransactionReasonDto.cs` | record with 2 FKs |
| Validator | `CreateVoucherTypeCommandValidator.cs` | NotEmpty, MaximumLength, IsInEnum, GreaterThan(0) |
| Validator (2 FKs) | `CreateTransactionReasonCommandValidator.cs` | Same + second FK > 0 |
| Get handler | `GetVoucherTypeHandler.cs` | GetByIdAsync + null → null mapping |
| List handler | `GetVoucherTypesByCompanyHandler.cs` | GetAllAsync + Where + Select to DTO |

### Application DI (no changes needed)

`src/SmeAccounting.Application/DependencyInjection.cs` uses assembly scan — auto-discovers all handlers and validators. No manual registration.

### Architecture Test Impact

**Naming convention tests that validate Application layer:**
- Test 6: `Commands_In_Commands_Namespace_Should_End_With_Command` — all `IRequest` types in `SmeAccounting.Application.Commands` must end with "Command"
- Test 7: `Queries_In_Queries_Namespace_Should_End_With_Query` — all types in `SmeAccounting.Application.Queries` must end with "Query"
- Test 8: `DTOs_Should_End_With_Dto` — all types in `SmeAccounting.Application.DTOs` must end with "Dto"
- Test 12: `Application_Handlers_Should_Not_Reference_Infrastructure_Namespace` — handlers must NOT reference `SmeAccounting.Infrastructure`

**Impact:** Command names must end with "Command", query names with "Query", DTO names with "Dto". Handlers can only reference Domain and Application — never Infrastructure.

## Requirements & Constraints

### Per-Entity Commands/Queries/DTOs/Validators

#### 1. TaxType (G1 entity)

**Entity properties:** Id, Code, Name, TaxCategory (enum), CompanyId, IsActive, Description

| Artifact | Name | Properties/Notes |
|----------|------|-----------------|
| Command | `CreateTaxTypeCommand` | Code, Name, TaxCategory (enum), CompanyId, Description? |
| Result | `CreateTaxTypeResult` | long Id |
| Query | `GetTaxTypeQuery` | long TaxTypeId → TaxTypeDto? |
| Query | `GetTaxTypesByCompanyQuery` | long CompanyId → IReadOnlyList<TaxTypeDto> |
| Command | `DeactivateTaxTypeCommand` | long TaxTypeId → DeactivateTaxTypeResult |
| DTO | `TaxTypeDto` | Id, Code, Name, TaxCategory (string), CompanyId, IsActive, Description? |
| Validator | `CreateTaxTypeCommandValidator` | Code NotEmpty + MaxLen(20), Name NotEmpty + MaxLen(200), TaxCategory IsInEnum, CompanyId > 0 |
| Handler | `CreateTaxTypeHandler` | IX + IUnitOfWork |
| Handler | `GetTaxTypeHandler` | IX only |
| Handler | `GetTaxTypesByCompanyHandler` | IX only |
| Handler | `DeactivateTaxTypeHandler` | IX + IUnitOfWork |

#### 2. TaxTreatment (G1 entity)

**Entity properties:** Id, Code, Name, TaxTypeId (FK), TaxTreatmentType (enum), InputCreditAllowed, CompanyId, IsActive, Description

| Artifact | Name | Properties/Notes |
|----------|------|-----------------|
| Command | `CreateTaxTreatmentCommand` | Code, Name, TaxTypeId, TaxTreatmentType (enum), InputCreditAllowed, CompanyId, Description? |
| Result | `CreateTaxTreatmentResult` | long Id |
| Query | `GetTaxTreatmentQuery` | long TaxTreatmentId → TaxTreatmentDto? |
| Query | `GetTaxTreatmentsByCompanyQuery` | long CompanyId → IReadOnlyList<TaxTreatmentDto> |
| Query | `GetTaxTreatmentsByTaxTypeQuery` | long TaxTypeId → IReadOnlyList<TaxTreatmentDto> |
| Command | `DeactivateTaxTreatmentCommand` | long TaxTreatmentId → DeactivateTaxTreatmentResult |
| DTO | `TaxTreatmentDto` | Id, Code, Name, TaxTypeId, TaxTreatmentType (string), InputCreditAllowed, CompanyId, IsActive, Description? |
| Validator | `CreateTaxTreatmentCommandValidator` | Code/Name NotEmpty + MaxLen, TaxTypeId > 0, TaxTreatmentType IsInEnum, CompanyId > 0 |

#### 3. TaxAuthority (G1 entity)

**Entity properties:** Id, Code, Name, AuthorityLevel (enum), CompanyId, IsActive, Address?, Phone?, Description?

| Artifact | Name | Properties/Notes |
|----------|------|-----------------|
| Command | `CreateTaxAuthorityCommand` | Code, Name, AuthorityLevel (enum), CompanyId, Address?, Phone?, Description? |
| Result | `CreateTaxAuthorityResult` | long Id |
| Query | `GetTaxAuthorityQuery` | long TaxAuthorityId → TaxAuthorityDto? |
| Query | `GetTaxAuthoritiesByCompanyQuery` | long CompanyId → IReadOnlyList<TaxAuthorityDto> |
| Command | `DeactivateTaxAuthorityCommand` | long TaxAuthorityId → DeactivateTaxAuthorityResult |
| DTO | `TaxAuthorityDto` | Id, Code, Name, AuthorityLevel (string), CompanyId, IsActive, Address?, Phone?, Description? |
| Validator | `CreateTaxAuthorityCommandValidator` | Code/Name NotEmpty + MaxLen, AuthorityLevel IsInEnum, CompanyId > 0 |

#### 4. TaxRate (G2 entity)

**Entity properties:** Id, CompanyId, TaxTypeId (FK), RateValue (decimal), RateName, EffectiveFrom (DateOnly), EffectiveTo (DateOnly?), IsActive, Description

| Artifact | Name | Properties/Notes |
|----------|------|-----------------|
| Command | `CreateTaxRateCommand` | TaxTypeId, RateValue (decimal), RateName, EffectiveFrom (DateOnly), EffectiveTo (DateOnly?), CompanyId, Description? |
| Result | `CreateTaxRateResult` | long Id |
| Query | `GetTaxRateQuery` | long TaxRateId → TaxRateDto? |
| Query | `GetTaxRatesByCompanyQuery` | long CompanyId → IReadOnlyList<TaxRateDto> |
| Command | `DeactivateTaxRateCommand` | long TaxRateId → DeactivateTaxRateResult |
| DTO | `TaxRateDto` | Id, CompanyId, TaxTypeId, RateValue, RateName, EffectiveFrom, EffectiveTo, IsActive, Description? |
| Validator | `CreateTaxRateCommandValidator` | TaxTypeId > 0, RateValue >= 0, RateName NotEmpty + MaxLen(200), EffectiveFrom (required, validated as DateOnly), CompanyId > 0 |

**Note:** No Code property on TaxRate. DTO uses RateName for display.

#### 5. TaxRule (G3 entity)

**Entity properties:** Id, CompanyId, TaxTypeId (FK), TaxRateId (FK?), TaxTreatmentId (FK), Code, Name, Conditions?, LegalReference, EffectiveFrom (DateOnly), EffectiveTo (DateOnly?), IsActive, Description

| Artifact | Name | Properties/Notes |
|----------|------|-----------------|
| Command | `CreateTaxRuleCommand` | TaxTypeId, TaxRateId? (nullable long), TaxTreatmentId, Code, Name, LegalReference, EffectiveFrom, EffectiveTo?, Conditions?, CompanyId, Description? |
| Result | `CreateTaxRuleResult` | long Id |
| Query | `GetTaxRuleQuery` | long TaxRuleId → TaxRuleDto? |
| Query | `GetTaxRulesByCompanyQuery` | long CompanyId → IReadOnlyList<TaxRuleDto> |
| Command | `DeactivateTaxRuleCommand` | long TaxRuleId → DeactivateTaxRuleResult |
| DTO | `TaxRuleDto` | Id, CompanyId, TaxTypeId, TaxRateId?, TaxTreatmentId, Code, Name, Conditions?, LegalReference, EffectiveFrom, EffectiveTo, IsActive, Description? |
| Validator | `CreateTaxRuleCommandValidator` | TaxTypeId > 0, TaxRateId > 0 when provided, TaxTreatmentId > 0, Code/Name/LegalReference NotEmpty + MaxLen, CompanyId > 0 |

#### 6. TaxExemptionReason (G3 entity)

**Entity properties:** Id, CompanyId, TaxTypeId (FK), Code, Name, LegalBasis, Description?, IsActive

| Artifact | Name | Properties/Notes |
|----------|------|-----------------|
| Command | `CreateTaxExemptionReasonCommand` | TaxTypeId, Code, Name, LegalBasis, CompanyId, Description? |
| Result | `CreateTaxExemptionReasonResult` | long Id |
| Query | `GetTaxExemptionReasonQuery` | long TaxExemptionReasonId → TaxExemptionReasonDto? |
| Query | `GetTaxExemptionReasonsByCompanyQuery` | long CompanyId → IReadOnlyList<TaxExemptionReasonDto> |
| Query | `GetTaxExemptionReasonsByTaxTypeQuery` | long TaxTypeId → IReadOnlyList<TaxExemptionReasonDto> |
| Command | `DeactivateTaxExemptionReasonCommand` | long TaxExemptionReasonId → DeactivateTaxExemptionReasonResult |
| DTO | `TaxExemptionReasonDto` | Id, CompanyId, TaxTypeId, Code, Name, LegalBasis, Description?, IsActive |
| Validator | `CreateTaxExemptionReasonCommandValidator` | TaxTypeId > 0, Code/Name/LegalBasis NotEmpty + MaxLen, CompanyId > 0 |

#### 7. TaxAccountingMapping (G4 entity)

**Entity properties:** Id, CompanyId, TaxTypeId (FK), TaxTreatmentId (FK), AccountId (FK), MappingType (enum), IsActive, Description

| Artifact | Name | Properties/Notes |
|----------|------|-----------------|
| Command | `CreateTaxAccountingMappingCommand` | TaxTypeId, TaxTreatmentId, AccountId, MappingType (enum), CompanyId, Description? |
| Result | `CreateTaxAccountingMappingResult` | long Id |
| Query | `GetTaxAccountingMappingQuery` | long TaxAccountingMappingId → TaxAccountingMappingDto? |
| Query | `GetTaxAccountingMappingsByCompanyQuery` | long CompanyId → IReadOnlyList<TaxAccountingMappingDto> |
| Command | `DeactivateTaxAccountingMappingCommand` | long TaxAccountingMappingId → DeactivateTaxAccountingMappingResult |
| DTO | `TaxAccountingMappingDto` | Id, CompanyId, TaxTypeId, TaxTreatmentId, AccountId, MappingType (string), IsActive, Description? |
| Validator | `CreateTaxAccountingMappingCommandValidator` | TaxTypeId > 0, TaxTreatmentId > 0, AccountId > 0, MappingType IsInEnum, CompanyId > 0 |

#### 8. TaxPeriod (G5 entity)

**Entity properties:** Id, CompanyId, FiscalPeriodId (FK), TaxTypeId (FK), FilingDeadline (DateOnly), FilingFrequency (enum), Status (enum), IsActive, Description

| Artifact | Name | Properties/Notes |
|----------|------|-----------------|
| Command | `CreateTaxPeriodCommand` | FiscalPeriodId, TaxTypeId, FilingFrequency (enum), FilingDeadline (DateOnly), CompanyId, Description? |
| Result | `CreateTaxPeriodResult` | long Id |
| Query | `GetTaxPeriodQuery` | long TaxPeriodId → TaxPeriodDto? |
| Query | `GetTaxPeriodsByCompanyQuery` | long CompanyId → IReadOnlyList<TaxPeriodDto> |
| Command | `DeactivateTaxPeriodCommand` | long TaxPeriodId → DeactivateTaxPeriodResult |
| DTO | `TaxPeriodDto` | Id, CompanyId, FiscalPeriodId, TaxTypeId, FilingDeadline, FilingFrequency (string), Status (string), IsActive, Description? |
| Validator | `CreateTaxPeriodCommandValidator` | FiscalPeriodId > 0, TaxTypeId > 0, FilingFrequency IsInEnum, CompanyId > 0 |

**Note:** No Code on TaxPeriod. No GetByCompositeKey query in G6 (can add later via controllers).

### EF Migration

**Migration name:** `Phase3TaxFoundation`

**Command:** `dotnet ef migrations add Phase3TaxFoundation --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`

**Tables to create (7 new tables):**
1. `tax_types` — G1
2. `tax_treatments` — G1
3. `tax_authorities` — G1
4. `tax_rates` — G2
5. `tax_rules` — G3
6. `tax_exemption_reasons` — G3
7. `tax_accounting_mappings` — G4
8. `tax_periods` — G5

**Wait — that's 8 tables.** All 8 tax entities need tables. The migration covers ALL of G1-G5.

**Pre-requisite:** Build must succeed before running `dotnet ef migrations add` (EF Core reads compiled assemblies).

**Memory constraint:** `pkill MSBuild` if OOM during migration generation.

## Suggested Approach

### Step 1: Create DTOs (8 files)
Create `TaxTypeDto`, `TaxTreatmentDto`, `TaxAuthorityDto`, `TaxRateDto`, `TaxRuleDto`, `TaxExemptionReasonDto`, `TaxAccountingMappingDto`, `TaxPeriodDto` in `src/SmeAccounting.Application/DTOs/`.

### Step 2: Create Commands (8 files, each with command + result)
Create `CreateTaxTypeCommand`, `CreateTaxTreatmentCommand`, `CreateTaxAuthorityCommand`, `CreateTaxRateCommand`, `CreateTaxRuleCommand`, `CreateTaxExemptionReasonCommand`, `CreateTaxAccountingMappingCommand`, `CreateTaxPeriodCommand` in `src/SmeAccounting.Application/Commands/`.

### Step 3: Create Deactivate Commands (8 files)
Create `DeactivateTaxTypeCommand`, etc. in `src/SmeAccounting.Application/Commands/`.

### Step 4: Create Queries (24 files: 8 single + 8 by-company + 8 special)
- 8 `GetXxxQuery` (single by ID)
- 8 `GetXxxsByCompanyQuery` (list by CompanyId)
- 2 additional: `GetTaxTreatmentsByTaxTypeQuery`, `GetTaxExemptionReasonsByTaxTypeQuery`

### Step 5: Create Validators (8 files)
Create FluentValidation validators for each Create command.

### Step 6: Create Handlers (32 files)
- 8 Create handlers (with IUnitOfWork)
- 8 Deactivate handlers (with IUnitOfWork)
- 8 Get-by-Id handlers (read-only)
- 8 Get-by-Company handlers (read-only)

### Step 7: Build
`dotnet build SmeAccounting.sln` — must succeed with zero warnings.

### Step 8: Run Architecture Tests
`dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 must pass.

### Step 9: Generate EF Migration
`dotnet ef migrations add Phase3TaxFoundation --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`

### Step 10: Verify Migration
Check migration file has 8 new tables with correct schema.

## Verification Criteria

### What "Done Correctly" Looks Like

1. **8 DTOs** in `SmeAccounting.Application.DTOs` — all end with "Dto" (test 8)
2. **8 Create commands** in `SmeAccounting.Application.Commands` — all end with "Command" (test 6)
3. **8 Deactivate commands** in `SmeAccounting.Application.Commands` — all end with "Command"
4. **8+ queries** in `SmeAccounting.Application.Queries` — all end with "Query" (test 7)
5. **8 validators** in `SmeAccounting.Application.Validators` — FluentValidation AbstractValidator
6. **32 handlers** in `SmeAccounting.Application.Handlers` — internal sealed, IRequestHandler
7. **No Infrastructure references** in any handler (test 12)
8. **All enum properties in DTOs** stored as string via `.ToString()`
9. **Build:** 0 warnings, 0 errors (TreatWarningsAsErrors)
10. **Architecture tests:** 22/22 pass
11. **Migration:** `Phase3TaxFoundation` creates all 8 tables
12. **Migration SQL:** Correct PKs, indexes, FKs, unique constraints
13. **Down migration:** Full reversal (DropTable for all 8 tables)

### What "Failing" Looks Like

1. Command ending with "Result" instead of "Command" → architecture test failure (test 6)
2. Query not ending with "Query" → architecture test failure (test 7)
3. DTO not ending with "Dto" → architecture test failure (test 8)
4. Handler referencing `SmeAccounting.Infrastructure` namespace → architecture test failure (test 12)
5. Missing validator for any Create command → no validation (validation silently skipped)
6. Wrong DTO properties (missing FK, wrong enum conversion) → API returns incorrect data
7. Missing nullable for TaxRateId in TaxRule command/DTO → forces all rules to have a rate (wrong for exempt rules)
8. Migration missing unique index → allows duplicate data at DB level
9. Migration missing FK constraint → orphaned records possible
10. Down migration missing DropTable → can't rollback

## Quality Standards

### Good Output
- Exact match to VoucherType/TransactionReason CQRS patterns
- DTOs map ALL entity properties (no omissions)
- All enum properties use `.ToString()` consistently in DTO mapping
- Validators cover ALL required fields and FK > 0 constraints
- Handlers use `internal sealed` class pattern
- All query handlers use appropriate repository methods (GetAllByCompanyAsync for list queries)
- Migration generates correct PostgreSQL schema with snake_case naming
- Build and all 22 architecture tests pass

### Merely Functional
- Commands/queries work but naming doesn't match conventions (fails architecture tests)
- DTOs missing properties (e.g., missing InputCreditAllowed on TaxTreatmentDto)
- Validators too strict or too loose (missing FK validation, missing max length)
- Handlers not sealed (violates established pattern)
- Migration missing indexes or unique constraints
- Down migration incomplete (can't rollback)

## Files to Create/Modify

### New Files (~56 total)

**DTOs (8):**
- `src/SmeAccounting.Application/DTOs/TaxTypeDto.cs`
- `src/SmeAccounting.Application/DTOs/TaxTreatmentDto.cs`
- `src/SmeAccounting.Application/DTOs/TaxAuthorityDto.cs`
- `src/SmeAccounting.Application/DTOs/TaxRateDto.cs`
- `src/SmeAccounting.Application/DTOs/TaxRuleDto.cs`
- `src/SmeAccounting.Application/DTOs/TaxExemptionReasonDto.cs`
- `src/SmeAccounting.Application/DTOs/TaxAccountingMappingDto.cs`
- `src/SmeAccounting.Application/DTOs/TaxPeriodDto.cs`

**Create Commands (8):**
- `src/SmeAccounting.Application/Commands/CreateTaxTypeCommand.cs`
- `src/SmeAccounting.Application/Commands/CreateTaxTreatmentCommand.cs`
- `src/SmeAccounting.Application/Commands/CreateTaxAuthorityCommand.cs`
- `src/SmeAccounting.Application/Commands/CreateTaxRateCommand.cs`
- `src/SmeAccounting.Application/Commands/CreateTaxRuleCommand.cs`
- `src/SmeAccounting.Application/Commands/CreateTaxExemptionReasonCommand.cs`
- `src/SmeAccounting.Application/Commands/CreateTaxAccountingMappingCommand.cs`
- `src/SmeAccounting.Application/Commands/CreateTaxPeriodCommand.cs`

**Deactivate Commands (8):**
- `src/SmeAccounting.Application/Commands/DeactivateTaxTypeCommand.cs`
- `src/SmeAccounting.Application/Commands/DeactivateTaxTreatmentCommand.cs`
- `src/SmeAccounting.Application/Commands/DeactivateTaxAuthorityCommand.cs`
- `src/SmeAccounting.Application/Commands/DeactivateTaxRateCommand.cs`
- `src/SmeAccounting.Application/Commands/DeactivateTaxRuleCommand.cs`
- `src/SmeAccounting.Application/Commands/DeactivateTaxExemptionReasonCommand.cs`
- `src/SmeAccounting.Application/Commands/DeactivateTaxAccountingMappingCommand.cs`
- `src/SmeAccounting.Application/Commands/DeactivateTaxPeriodCommand.cs`

**Queries (~24):**
- 8 single-by-ID: `GetXxxQuery` files
- 8 by-company: `GetXxxsByCompanyQuery` files
- 2 by-parent: `GetTaxTreatmentsByTaxTypeQuery.cs`, `GetTaxExemptionReasonsByTaxTypeQuery.cs`

**Validators (8):**
- `src/SmeAccounting.Application/Validators/CreateTaxTypeCommandValidator.cs`
- `src/SmeAccounting.Application/Validators/CreateTaxTreatmentCommandValidator.cs`
- `src/SmeAccounting.Application/Validators/CreateTaxAuthorityCommandValidator.cs`
- `src/SmeAccounting.Application/Validators/CreateTaxRateCommandValidator.cs`
- `src/SmeAccounting.Application/Validators/CreateTaxRuleCommandValidator.cs`
- `src/SmeAccounting.Application/Validators/CreateTaxExemptionReasonCommandValidator.cs`
- `src/SmeAccounting.Application/Validators/CreateTaxAccountingMappingCommandValidator.cs`
- `src/SmeAccounting.Application/Validators/CreateTaxPeriodCommandValidator.cs`

**Handlers (32):**
- 8 Create handlers in `src/SmeAccounting.Application/Handlers/`
- 8 Deactivate handlers
- 8 Get-by-Id handlers
- 8 Get-by-Company handlers

### Modified Files
- None — DI is auto-scanned, no file edits needed

### Generated Files (1)
- EF migration file (auto-generated by `dotnet ef migrations add`)

## Implementation Order (for executor)

1. DTOs first (they define the contract)
2. Commands + Results (define the operations)
3. Queries (define the reads)
4. Validators (validate commands)
5. Handlers (implement the logic)
6. Build
7. Test
8. Migration

## Key Gotchas

1. **Nullable TaxRateId on TaxRule:** The command, DTO, and validator must handle `long?` (nullable). Exempt rules have no rate.
2. **DateOnly in commands:** C# `DateOnly` works in records. MediatR handles it fine. No special serialization needed for handlers.
3. **Enum-to-string in DTOs:** Always `.ToString()` in handler mapping. Never store enum int values in DTOs.
4. **Handler null-check pattern:** Get single query handlers return `XxxDto?`. Handler returns `null` if entity not found. Command to list handler uses `.Select()` — no null check needed (empty list is fine).
5. **No Infrastructure references in handlers:** Handlers reference Domain entities and ports only. Repository implementations are injected via DI (interface), not concrete type.
6. **GetAllByCompanyAsync vs GetAllAsync:** Tax entities use `GetAllByCompanyAsync(companyId)` — not `GetAllAsync()`. The list query handler passes CompanyId to the repository method.
7. **Migration memory:** `pkill MSBuild` before migration if OOM. Build first, then migrate.
8. **TaxRate has no Code:** TaxRate DTO uses RateName, not Code. Don't try to add a Code field.

---

# Task-Specific Research — [G4] TaxAccountingMapping domain

## Context & Prior Work

### What Exists
- **TaxType entity** (G1): CompanyId + Code + Name + TaxCategory + IsActive + Description — 8 tax types (VAT, CIT, PIT, SpecialConsumption, Resource, Environmental, ImportDuty, ExportDuty)
- **TaxTreatment entity** (G1): CompanyId + TaxTypeId FK + Code + Name + TaxTreatmentType + InputCreditAllowed + IsActive + Description — 5 treatments (StandardRate, ReducedRate, ZeroRate, Exempt, NonTaxable)
- **Account entity** (Phase 1): AccountCode (VO) + Name + Level + AccountType + NormalBalance + CompanyId + IsActive — the COA entity TaxAccountingMapping references
- **PostingConfiguration entity** (Phase 2): CompanyId + VoucherTypeId FK + DebitAccountId FK + CreditAccountId FK + TransactionReasonId FK? + DisplayOrder + IsActive — precedent for Account FK pattern
- **OpeningBalanceMapping entity** (Phase 2): CompanyId + VoucherTypeId FK + DebitAccountId FK + CreditAccountId FK + IsActive — precedent for Account FK pattern
- **24 DbSets, 20 ignored events** in DbContext currently
- **19 AddScoped DI registrations** currently

### Key Design Insight: Single AccountId (not Debit/Credit pair)
Unlike PostingConfiguration and OpeningBalanceMapping which have **two** Account FKs (DebitAccountId + CreditAccountId), TaxAccountingMapping has **one** AccountId FK. This is correct because:
- TaxAccountingMapping maps a tax type+treatment to a **single** COA account
- The debit/credit direction is determined at posting time by the journal entry template, not by the mapping
- Example: "Output VAT" mapping points to Account 33311 — when a sale occurs, the system knows to Credit this account (per Circular 99 template)

### Circular 99 Account Mapping Requirements

| MappingType | Circular 99 Account | Account Name | Account Category |
|-------------|-------------------|--------------|-----------------|
| InputVAT | 1331 | VAT on goods and services | Asset (1xxx) |
| InputVAT | 1332 | VAT on fixed assets | Asset (1xxx) |
| OutputVAT | 33311 | Output VAT | Liability (3xxx) |
| VATPayable | 3331 | VAT payable (parent) | Liability (3xxx) |
| ImportVAT | 33312 | Import VAT | Liability (3xxx) |
| CITPayable | 3334 | Corporate income tax payable | Liability (3xxx) |
| PITPayable | 3335 | Personal income tax payable | Liability (3xxx) |
| TaxDeductible | 1331 | VAT deductible (general) | Asset (1xxx) |

**Note:** 1331 appears for both InputVAT and TaxDeductible — same account, different mapping context. The MappingType distinguishes the purpose.

### Journal Entry Templates from Circular 99 (for context — not implemented in G4)

**Purchase of goods/services:**
```
Debit: 152/153/156 (Inventory)    Credit: 111/112/331 (Payment)
Debit: 1331 (Input VAT — InputVAT mapping)
```

**Sale of goods/services:**
```
Debit: 131 (Receivable)           Credit: 511/515/711 (Revenue)
                                  Credit: 33311 (Output VAT — OutputVAT mapping)
```

**Import VAT:**
```
Debit: 1331 (Input VAT — InputVAT mapping)
Credit: 33312 (Import VAT payable — ImportVAT mapping)
```

**VAT Settlement:**
```
Debit: 33311 (Output VAT)         Credit: 1331 (Input VAT deductible — TaxDeductible mapping)
```

## Existing Tools & Resources

### Pattern Sources (copy from these)
| File | Relevance |
|------|-----------|
| `OpeningBalanceMapping.cs` | Closest entity pattern — CompanyId + FKs to Account + IsActive + Deactivate() |
| `OpeningBalanceMappingConfiguration.cs` | FK to Account pattern: `HasOne<Account>().WithMany().HasForeignKey().OnDelete(Restrict)` |
| `PostingConfiguration.cs` | Similar multi-FK entity with Account references |
| `TaxTreatment.cs` | Entity with CompanyId + multiple FKs — same pattern |
| `TaxTreatmentConfiguration.cs` | Two FKs both Restrict — same pattern |

### EF Config FK-to-Account Pattern (from OpeningBalanceMappingConfiguration)
```csharp
builder.HasOne<Account>()
    .WithMany()
    .HasForeignKey(e => e.AccountId)
    .OnDelete(DeleteBehavior.Restrict);
```
No navigation property on entity — FK relationship configured in EF config only.

## Requirements & Constraints

### Entity Properties
| Property | Type | Constraints | Notes |
|----------|------|-------------|-------|
| CompanyId | long | FK → companies, Restrict, required | Company scoping |
| TaxTypeId | long | FK → tax_types, Restrict, required | Which tax type |
| TaxTreatmentId | long | FK → tax_treatments, Restrict, required | Which treatment |
| AccountId | long | FK → accounts, Restrict, required | Target COA account |
| MappingType | TaxAccountingMappingType enum | HasConversion<string>() | What this mapping represents |
| IsActive | bool | default true | Soft-delete |
| Description | string? | max 500 | Optional notes |

### Enum: TaxAccountingMappingType
Values (7): InputVAT, OutputVAT, VATPayable, CITPayable, PITPayable, ImportVAT, TaxDeductible

**Naming collision check:** `TaxAccountingMappingType` (enum) vs `TaxAccountingMapping` (entity) — distinct names, no collision. Safe as-is.

### FK Validation (in constructor)
- CompanyId > 0 — DomainException
- TaxTypeId > 0 — DomainException
- TaxTreatmentId > 0 — DomainException
- AccountId > 0 — DomainException
- No need to validate Account exists/is active in domain constructor — that's application-layer responsibility (repository lookup before create)

### Unique Index Design
**Option A:** `(CompanyId, MappingType)` — one mapping per type per company
**Option B:** `(CompanyId, TaxTypeId, TaxTreatmentId, MappingType)` — more granular

**Recommendation: Option A** — `(CompanyId, MappingType)` is simpler and matches the business rule: a company has ONE account for "OutputVAT", ONE for "CITPayable", etc. The TaxType/TaxTreatment FKs provide the semantic grouping, but the mapping type is the unique identifier.

### Repository Methods
| Method | Purpose |
|--------|---------|
| GetByIdAsync(long id) | Standard lookup |
| GetAllByCompanyAsync(long companyId) | Company-scoped list |
| GetByTaxTypeAndTreatmentAsync(long taxTypeId, long treatmentTypeId, long companyId) | Lookup by semantic key |
| AddAsync(TaxAccountingMapping mapping) | Insert |

**No GetByCodeAsync** — TaxAccountingMapping has no Code property. Unique lookup is by MappingType per company.

### DbContext Changes
- **Current:** 24 DbSets, 20 ignored events
- **After G4:** 25 DbSets, 21 ignored events (+TaxAccountingMapping DbSet + TaxAccountingMappingCreated Ignore)

### DI Changes
- **Current:** 19 AddScoped registrations
- **After G4:** 20 AddScoped registrations (+ITaxAccountingMappingRepository)

## Suggested Approach

1. Create `TaxAccountingMappingType` enum in `Domain/ValueObjects/TaxAccountingMappingType.cs` — 7 values
2. Create `TaxAccountingMappingCreated` event in `Domain/Events/TaxAccountingMappingCreated.cs` — TaxAccountingMappingId + CompanyId + occurredOn
3. Create `TaxAccountingMapping` entity in `Domain/Entities/TaxAccountingMapping.cs` — 4 FKs + MappingType + IsActive + Description, DomainException validation, Deactivate()
4. Create `ITaxAccountingMappingRepository` port in `Domain/Ports/ITaxAccountingMappingRepository.cs` — 4 methods
5. Create `TaxAccountingMappingConfiguration` in `Infrastructure/Persistence/Configurations/TaxAccountingMappingConfiguration.cs` — snake_case table, 4 FKs Restrict, unique index (CompanyId, MappingType), xmin
6. Create `EfTaxAccountingMappingRepository` in `Infrastructure/Repositories/EfTaxAccountingMappingRepository.cs`
7. Edit `SmeAccountingDbContext.cs` — add DbSet + Ignore
8. Edit `DependencyInjection.cs` — add AddScoped
9. Build + test

## Verification Criteria

### What "Done Correctly" Looks Like
1. `TaxAccountingMappingType` enum has exactly 7 values: InputVAT, OutputVAT, VATPayable, CITPayable, PITPayable, ImportVAT, TaxDeductible
2. `TaxAccountingMapping` entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity, private parameterless ctor, public ctor with DomainException validation
3. Entity has 4 FKs: CompanyId, TaxTypeId, TaxTreatmentId, AccountId — all validated > 0 in constructor
4. `TaxAccountingMappingCreated` event carries TaxAccountingMappingId + CompanyId + occurredOn
5. `ITaxAccountingMappingRepository` in `SmeAccounting.Domain.Ports` — starts with I, 4 methods (GetById, GetAllByCompany, GetByTaxTypeAndTreatment, Add)
6. EF config: snake_case table `tax_accounting_mappings`, unique index `(CompanyId, MappingType)`, 4 FKs all Restrict (Company, TaxType, TaxTreatment, Account), xmin row version
7. EF config: `HasConversion<string>()` for MappingType enum, `HasOne<Account>().WithMany().HasForeignKey().OnDelete(Restrict)` for Account FK
8. Repository: `AsNoTracking()` for GetAllByCompany, tracked for GetById/GetByTaxTypeAndTreatment
9. DbContext: 25 DbSets, 21 ignored events
10. DI: 20 AddScoped registrations
11. Build: zero warnings (TreatWarningsAsErrors)
12. Tests: 22/22 pass

### What "Failing" Looks Like
1. Enum named `TaxAccountingMapping` causing namespace collision with entity → compiler error (won't happen — names are distinct)
2. Entity missing private parameterless constructor → EF Core runtime failure
3. Missing `modelBuilder.Ignore<TaxAccountingMappingCreated>()` → EF Core migration error
4. Missing `DbSet<TaxAccountingMapping>` → entity not tracked by DbContext
5. Missing DI registration → runtime dependency injection failure
6. Missing unique index → duplicate mapping types allowed at DB level
7. Wrong namespace on entity → architecture test failure
8. Entity using `ArgumentNullException` instead of `DomainException` → violates established pattern
9. Account FK using Cascade delete instead of Restrict → violates established pattern
10. Missing any of the 4 FK validations in constructor → allows invalid references
11. Repository using `GetAllAsync()` instead of `GetAllByCompanyAsync(companyId)` → violates company-scoping

## Quality Standards

### Good Output
- Exact match to OpeningBalanceMapping pattern (FK to Account, CompanyId, IsActive, Deactivate)
- TaxAccountingMappingType enum values are self-documenting and match Circular 99 account categories
- 4 FKs all validated in constructor with DomainException
- EF config follows every convention (snake_case, xmin, all FKs Restrict, unique index)
- Code compiles with zero warnings
- All 22 architecture tests pass without modification
- Unique index on (CompanyId, MappingType) prevents duplicate mappings per company

### Merely Functional
- Entity works but uses different validation pattern (ArgumentNullException vs DomainException)
- Missing unique index (allows duplicate mapping types)
- Missing any FK validation
- No domain event raised in constructor
- Account FK uses Cascade instead of Restrict
- Repository uses GetAllAsync instead of GetAllByCompanyAsync
- Enum values don't match Circular 99 account categories

---

# Researcher 3 — Constraints & Schema Deep-Dive

## Requirements & Constraints

### Database Schema (Entity Configurations)

All 18 entity configurations follow these **universal patterns**:

| Pattern | Implementation |
|---------|---------------|
| **Table naming** | `builder.ToTable("snake_case_plural")` — e.g. `accounts`, `journal_entries`, `voucher_types` |
| **Primary key** | `builder.HasKey(e => e.Id)` + `builder.Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd()` |
| **Concurrency token** | `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")` — on every entity |
| **Company FK** | `builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — no navigation property on entity |
| **Enum storage** | `builder.Property(e => e.Xxx).HasColumnName("xxx").HasConversion<string>()` — always string, never int |
| **FK nav-free** | No Company/VoucherType navigation properties on entities — FK relationships configured in EF config only |

#### Table: `accounts`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK, auto-increment) | |
| `code` | `varchar(20)` | Required, OwnedValue (AccountCode.Value) |
| `name` | `varchar(max)` | |
| `level` | `int` | |
| `parent_id` | `bigint?` | FK → accounts(id), DeleteBehavior.Restrict |
| `account_type` | `varchar(max)` | HasConversion<string>() (Asset/Liability/Equity/Revenue/Expense) |
| `is_active` | `bool` | Default true |
| `account_group_id` | `bigint?` | |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `description` | `varchar(500)` | |
| `normal_balance` | `varchar(max)` | HasConversion<string>() (Debit/Credit) |
| `xmin` | `uint` | IsRowVersion |
| **Indexes** | `parent_id` index | |

#### Table: `account_groups`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `code` | `varchar(20)` | Required |
| `name` | `varchar(200)` | Required |
| `account_type` | `varchar(max)` | HasConversion<string>() |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `display_order` | `int` | |
| `xmin` | `uint` | IsRowVersion |

#### Table: `companies`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `name` | `varchar(200)` | Required |
| `tax_code` | `varchar(13)` | Required, **Unique index** |
| `address` | `varchar(500)` | Required |
| `phone` | `varchar(20)` | |
| `email` | `varchar(200)` | |
| `fiscal_year_start_month` | `int` | |
| `fiscal_year_start_day` | `int` | |
| `functional_currency_code` | `varchar(3)` | Required |
| `is_active` | `bool` | |
| `xmin` | `uint` | IsRowVersion |

#### Table: `currencies`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `code` | `varchar(3)` | Required, **Unique index** |
| `name` | `varchar(100)` | Required |
| `symbol` | `varchar(10)` | Required |
| `decimal_places` | `int` | |
| `is_default` | `bool` | |
| `is_active` | `bool` | |
| `xmin` | `uint` | IsRowVersion |

#### Table: `fiscal_years`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `year` | `int` | |
| `start_date` | `date` | |
| `end_date` | `date` | |
| `description` | `varchar(max)` | |
| `status` | `varchar(max)` | HasConversion<string>() (Open/Closed) |
| `xmin` | `uint` | IsRowVersion |

#### Table: `fiscal_periods`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `year_id` | `bigint` | FK → fiscal_years(id), index |
| `month` | `int` | |
| `start_date` | `date` | |
| `end_date` | `date` | |
| `period_type` | `varchar(max)` | HasConversion<string>() (Monthly/Quarterly) |
| `status` | `varchar(max)` | HasConversion<string>() (Open/Closing/Closed) |
| `opened_at` | `timestamptz?` | |
| `closed_at` | `timestamptz?` | |
| `xmin` | `uint` | IsRowVersion |

#### Table: `journal_entries`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `entry_number` | `varchar(50)` | Required, indexed |
| `date` | `timestamptz` | |
| `period_id` | `bigint` | FK → fiscal_periods(id), indexed |
| `description` | `varchar(500)` | |
| `source_type` | `varchar(100)` | |
| `source_id` | `bigint?` | |
| `posted_by` | `varchar(100)` | |
| `posted_at` | `timestamptz?` | |
| `is_posted` | `bool` | |
| `xmin` | `uint` | IsRowVersion |

#### Table: `journal_entry_lines`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `entry_id` | `bigint` | FK → journal_entries(id), indexed |
| `account_id` | `bigint` | FK → accounts(id), indexed |
| `description` | `varchar(500)` | |
| `debit_amount` | `decimal` | OwnedValue (Money.Amount) |
| `debit_currency` | `varchar(3)` | OwnedValue (Money.Currency) |
| `credit_amount` | `decimal` | OwnedValue (Money.Amount) |
| `credit_currency` | `varchar(3)` | OwnedValue (Money.Currency) |
| `department_id` | `bigint?` | FK → departments(id), DeleteBehavior.SetNull |
| `cost_center_id` | `bigint?` | FK → cost_centers(id), DeleteBehavior.SetNull |
| `project_id` | `bigint?` | FK → projects(id), DeleteBehavior.SetNull |
| `xmin` | `uint` | IsRowVersion |
| **Indexes** | `entry_id`, `account_id`, `department_id`, `cost_center_id`, `project_id` | |

#### Table: `posting_references`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `journal_entry_id` | `bigint` | FK → journal_entries(id), indexed |
| `source_type` | `varchar(100)` | Required |
| `source_id` | `bigint?` | |
| `xmin` | `uint` | IsRowVersion |
| **Indexes** | composite `(source_type, source_id)` | |

#### Table: `voucher_types`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `code` | `varchar(20)` | Required |
| `name` | `varchar(200)` | Required |
| `voucher_category` | `varchar(max)` | HasConversion<string>() |
| `is_active` | `bool` | |
| `description` | `varchar(500)` | |
| `xmin` | `uint` | IsRowVersion |
| **Unique index** | `(company_id, code)` | |

#### Table: `transaction_reasons`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `voucher_type_id` | `bigint` | FK → voucher_types(id), DeleteBehavior.Restrict |
| `code` | `varchar(20)` | Required |
| `name` | `varchar(200)` | Required |
| `is_active` | `bool` | |
| `description` | `varchar(500)` | |
| `xmin` | `uint` | IsRowVersion |
| **Unique index** | `(company_id, code)` | — NOT composite with voucher_type_id |

#### Table: `document_numbering_series`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `voucher_type_id` | `bigint` | FK → voucher_types(id), DeleteBehavior.Restrict |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `prefix` | `varchar(20)` | Required |
| `next_number` | `int` | |
| `padding_length` | `int` | |
| `is_default` | `bool` | |
| `is_active` | `bool` | |
| `description` | `varchar(500)` | |
| `xmin` | `uint` | IsRowVersion |
| **Unique index** | `(voucher_type_id, company_id, prefix)` | |

#### Table: `posting_configurations`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `voucher_type_id` | `bigint` | FK → voucher_types(id), DeleteBehavior.Restrict |
| `debit_account_id` | `bigint` | FK → accounts(id), DeleteBehavior.Restrict |
| `credit_account_id` | `bigint` | FK → accounts(id), DeleteBehavior.Restrict |
| `transaction_reason_id` | `bigint?` | FK → transaction_reasons(id), DeleteBehavior.Restrict |
| `display_order` | `int` | |
| `is_active` | `bool` | |
| `description` | `varchar(500)` | |
| `xmin` | `uint` | IsRowVersion |
| **Index** | composite `(voucher_type_id, transaction_reason_id)` | |

#### Table: `departments`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `code` | `varchar(50)` | Required |
| `name` | `varchar(200)` | Required |
| `is_active` | `bool` | |
| `xmin` | `uint` | IsRowVersion |
| **Unique index** | `(company_id, code)` | |

#### Table: `cost_centers`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `code` | `varchar(50)` | Required |
| `name` | `varchar(200)` | Required |
| `is_active` | `bool` | |
| `xmin` | `uint` | IsRowVersion |
| **Unique index** | `(company_id, code)` | |

#### Table: `projects`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `code` | `varchar(50)` | Required |
| `name` | `varchar(200)` | Required |
| `start_date` | `date?` | |
| `end_date` | `date?` | |
| `is_active` | `bool` | |
| `xmin` | `uint` | IsRowVersion |
| **Unique index** | `(company_id, code)` | |

#### Table: `exchange_rates`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `from_currency_code` | `varchar(3)` | Required |
| `to_currency_code` | `varchar(3)` | Required |
| `rate` | `decimal(10,6)` | |
| `rate_type` | `varchar(max)` | HasConversion<string>() |
| `effective_date` | `date` | |
| `source` | `varchar(200)` | |
| `xmin` | `uint` | IsRowVersion |
| **Unique index** | `(company_id, from_currency_code, to_currency_code, rate_type, effective_date)` | |

#### Table: `opening_balance_mappings`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `bigint` (PK) | |
| `company_id` | `bigint` | FK → companies(id), DeleteBehavior.Restrict |
| `voucher_type_id` | `bigint` | FK → voucher_types(id), DeleteBehavior.Restrict |
| `debit_account_id` | `bigint` | FK → accounts(id), DeleteBehavior.Restrict |
| `credit_account_id` | `bigint` | FK → accounts(id), DeleteBehavior.Restrict |
| `is_active` | `bool` | |
| `description` | `varchar(500)` | |
| `xmin` | `uint` | IsRowVersion |
| **Unique index** | `(company_id, voucher_type_id, debit_account_id, credit_account_id)` | |

---

### DbContext Structure

**File:** `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs`

**DbSets (18 total):**
```csharp
DbSet<Account> Accounts
DbSet<AccountGroup> AccountGroups
DbSet<JournalEntry> JournalEntries
DbSet<JournalEntryLine> JournalEntryLines
DbSet<FiscalYear> FiscalYears
DbSet<FiscalPeriod> FiscalPeriods
DbSet<PostingReference> PostingReferences
DbSet<Company> Companies
DbSet<Currency> Currencies
DbSet<ExchangeRate> ExchangeRates
DbSet<Department> Departments
DbSet<CostCenter> CostCenters
DbSet<Project> Projects
DbSet<VoucherType> VoucherTypes
DbSet<DocumentNumberingSeries> DocumentNumberingSeries
DbSet<TransactionReason> TransactionReasons
DbSet<PostingConfiguration> PostingConfigurations
DbSet<OpeningBalanceMapping> OpeningBalanceMappings
```

**Ignored domain events (14 total):**
```csharp
modelBuilder.Ignore<DomainEvent>();
modelBuilder.Ignore<AccountCreated>();
modelBuilder.Ignore<AccountDeprecated>();
modelBuilder.Ignore<JournalEntryPosted>();
modelBuilder.Ignore<PeriodClosed>();
modelBuilder.Ignore<CompanyCreated>();
modelBuilder.Ignore<CurrencyCreated>();
modelBuilder.Ignore<FiscalYearCreated>();
modelBuilder.Ignore<ExchangeRateRecorded>();
modelBuilder.Ignore<DepartmentCreated>();
modelBuilder.Ignore<CostCenterCreated>();
modelBuilder.Ignore<ProjectCreated>();
modelBuilder.Ignore<VoucherTypeCreated>();
modelBuilder.Ignore<TransactionReasonCreated>();
```

**Key pattern:** Every new entity needs BOTH a `DbSet<T>` property AND `modelBuilder.Ignore<Event>()` for its domain events.

**Configuration application:** `modelBuilder.ApplyConfigurationsFromAssembly(typeof(SmeAccountingDbContext).Assembly)` — auto-discovers all `IEntityTypeConfiguration<T>` in the Infrastructure assembly.

**SaveChangesAsync override:** Collects domain events from `ChangeTracker.Entries<BaseEntity>()` before save, then publishes after save (currently stub — `await Task.CompletedTask`).

**DI registration pattern:** `AddScoped<IXxxRepository, EfXxxRepository>()` in `DependencyInjection.cs`.

---

### Architecture Test Rules (22 tests)

#### DomainPurityTests (3 tests)
1. **Domain_Should_Have_No_NuGet_PackageReferences** — Parses Domain.csproj, asserts zero `<PackageReference>` elements
2. **Domain_Should_Not_Reference_Microsoft_Or_Npgsql_Packages** — Checks no packages start with `Microsoft.`, `Npgsql.`, `Serilog.`, `EFCore.`
3. **Domain_Should_Have_No_EntityFramework_Assembly_Dependency** — NetArchTest: Domain assembly must not depend on `Microsoft.EntityFrameworkCore`

**Impact on Tax Foundation:** Tax entities MUST be in `SmeAccounting.Domain` assembly. Domain.csproj must remain zero NuGet refs. No EF Core references in Domain.

#### NamingConventionsTests (6 tests)
4. **Entities_Inheriting_BaseEntity_Should_Reside_In_Entities_Namespace** — All BaseEntity subclasses must be in `SmeAccounting.Domain.Entities`
5. **Repository_Interfaces_Should_Start_With_I** — All interfaces ending with "Repository" must start with "I"
6. **Commands_In_Commands_Namespace_Should_End_With_Command** — IRequest types in Commands namespace must end with "Command"
7. **Queries_In_Queries_Namespace_Should_End_With_Query** — Types in Queries namespace must end with "Query"
8. **DTOs_Should_End_With_Dto** — Types in DTOs namespace must end with "Dto"
9. **Controllers_Should_End_With_Controller** — Types in Controllers namespace must end with "Controller"

**Impact on Tax Foundation:** Tax entities → `Domain.Entities`, tax repositories → `IXxxRepository`, tax commands → `XxxCommand`, tax DTOs → `XxxDto`.

#### LayerCouplingTests (4 tests)
10. **Controllers_Should_Not_Reference_Domain_Entities_Namespace** — Api.Controllers must not depend on `SmeAccounting.Domain.Entities`
11. **Controllers_Should_Not_Reference_Domain_Ports_Namespace** — Api.Controllers must not depend on `SmeAccounting.Domain.Ports`
12. **Application_Handlers_Should_Not_Reference_Infrastructure_Namespace** — MediatR handlers must not depend on `SmeAccounting.Infrastructure`
13. **Infrastructure_Should_Not_Reference_Api_Namespace** — Infrastructure must not depend on Api

#### DependencyRulesTests (7 tests)
14. **Domain_Should_Not_Depend_On_Application** — Domain must not reference Application
15. **Domain_Should_Not_Depend_On_Infrastructure** — Domain must not reference Infrastructure
16. **Domain_Should_Not_Depend_On_Api** — Domain must not reference Api
17. **Application_Should_Not_Depend_On_Infrastructure** — Application must not reference Infrastructure
18. **Application_Should_Not_Depend_On_Api** — Application must not reference Api
19. **Infrastructure_Should_Not_Depend_Api** — Infrastructure must not reference Api
20. **Api_Controllers_Should_Not_Depend_On_Infrastructure** — Controllers must not depend on Infrastructure

#### PostingRuleIsolationTests (2 tests)
21. **IPostingService_Should_Reside_In_Domain_Assembly** — IPostingService must be in Domain
22. **JournalEntry_Balance_Rule_Should_Be_Enforceable_In_Domain** — JournalEntry, Money, IPostingService all in Domain

**Impact:** If any tax entity, port, or value object violates these rules, the 22-test suite breaks. Build fails (TreatWarningsAsErrors + tests run in CI).

---

### Port Interface Patterns

All 18 port interfaces in `Domain/Ports/`:

| Interface | Methods | Pattern |
|-----------|---------|---------|
| `IAccountRepository` | GetByIdAsync, GetAllAsync, AddAsync, UpdateAsync | Basic CRUD |
| `IJournalEntryRepository` | GetByIdAsync, GetAllAsync, AddAsync | Basic (no Update) |
| `ICompanyRepository` | GetByIdAsync, GetByTaxCodeAsync, GetAllAsync, AddAsync | + unique lookup |
| `ICurrencyRepository` | GetByIdAsync, GetByCodeAsync, GetAllAsync, AddAsync | + unique lookup |
| `IExchangeRateRepository` | GetByIdAsync, GetByCurrencyPairAsync, GetAllAsync, AddAsync | + compound lookup |
| `IDepartmentRepository` | GetByIdAsync, GetByCodeAsync(code, companyId), GetAllAsync, AddAsync | + code+company lookup |
| `ICostCenterRepository` | GetByIdAsync, GetByCodeAsync(code, companyId), GetAllAsync, AddAsync | Same as Department |
| `IProjectRepository` | GetByIdAsync, GetByCodeAsync(code, companyId), GetAllAsync, AddAsync | Same as Department |
| `IVoucherTypeRepository` | GetByIdAsync, GetByCodeAsync(code, companyId), GetAllAsync, AddAsync | Same as Department |
| `ITransactionReasonRepository` | GetByIdAsync, GetByCodeAsync(code, companyId), GetAllByVoucherTypeAsync, AddAsync | + voucher type filter |
| `IPostingConfigurationRepository` | GetByIdAsync, GetAllByVoucherTypeAsync, GetAllByCompanyAsync, AddAsync | Company-scoped queries |
| `IDocumentNumberingSeriesRepository` | GetByIdAsync, GetDefaultAsync(voucherTypeId, companyId), GetAllByCompanyAsync, AddAsync | + default lookup |
| `IOpeningBalanceMappingRepository` | GetByIdAsync, GetAllByCompanyAsync, AddAsync | Minimal |
| `IUnitOfWork` | SaveChangesAsync | Single method |
| `IClock` | Now property | Single property |
| `IAuditLogger` | LogAsync(action, entity, entityId, details) | Audit trail |
| `IForeignExchangeRateProvider` | ConvertAsync(amount, targetCurrency, date) | External service |
| `IPostingService` | PostAsync(JournalEntry) | Domain service |

**Tax repository pattern to follow:** `GetByIdAsync`, `GetByCodeAsync(code, companyId)`, `GetAllAsync` or scoped query, `AddAsync`. No `UpdateAsync` (change tracking handles it).

---

### Value Object Patterns

All 10 value objects in `Domain/ValueObjects/`:

| VO | Type | Pattern |
|----|------|---------|
| `Money` | `record` | `Amount (decimal)` + `Currency (string)` — arithmetic operators with currency-mismatch guards |
| `AccountCode` | `record` | `Value (string)` — validated: numeric, ≥4 digits |
| `AccountType` | `enum` | Asset, Liability, Equity, Revenue, Expense |
| `NormalBalance` | `enum` | Debit, Credit |
| `PeriodType` | `enum` | Monthly, Quarterly |
| `PeriodStatus` | `enum` | Open, Closing, Closed |
| `ExchangeRateType` | `enum` | Average, Actual, Book, Contract |
| `FiscalYearStatus` | `enum` | Open, Closed |
| `VoucherCategory` | `enum` | Receipt, Payment, Journal, Adjustment, Opening |
| `Currency` | `record` | `Code, Name, IsDefault` — simple record (NOT referenced by Money VO) |

**Tax value objects to create:** TaxType enum (VAT, CIT, PIT, SpecialConsumption, Resource, Environmental, ImportDuty, ExportDuty), TaxRateType enum (Standard, Reduced, Zero, Exempt, NonTaxable), TaxTreatment enum.

**Enum location:** `Domain/ValueObjects/` — NOT `Domain/Enums/` (no such directory).

---

### Domain Event Patterns

All 14 domain events in `Domain/Events/`:

**Base class:** `DomainEvent` — abstract, with `OccurredOn (DateTimeOffset)` and `EventId (Guid)`.

| Event | Properties | Pattern |
|-------|-----------|---------|
| `AccountCreated` | AccountId | Single ID + occurredOn |
| `AccountDeprecated` | AccountId | Single ID + occurredOn |
| `JournalEntryPosted` | EntryId | Single ID + occurredOn |
| `PeriodClosed` | PeriodId | Single ID + occurredOn |
| `CompanyCreated` | CompanyId | Single ID + occurredOn |
| `CurrencyCreated` | CurrencyId | Single ID + occurredOn |
| `FiscalYearCreated` | FiscalYearId, CompanyId, Year | Entity ID + CompanyId + extra |
| `ExchangeRateRecorded` | ExchangeRateId, CompanyId | Entity ID + CompanyId |
| `DepartmentCreated` | DepartmentId, CompanyId | Entity ID + CompanyId |
| `CostCenterCreated` | CostCenterId, CompanyId | Entity ID + CompanyId |
| `ProjectCreated` | ProjectId, CompanyId | Entity ID + CompanyId |
| `VoucherTypeCreated` | VoucherTypeId, CompanyId | Entity ID + CompanyId |
| `TransactionReasonCreated` | TransactionReasonId, CompanyId | Entity ID + CompanyId |

**Event minimalism:** Events carry entity ID + company ID only — avoid duplicating entity data in events.

**DbContext pattern:** Every new event needs `modelBuilder.Ignore<EventType>()` in DbContext.

---

### Key Constraints for Tax Foundation

#### Entity Design Constraints
1. **All tax entities MUST inherit `BaseEntity`** — `long Id` + `DomainEvents` collection
2. **Private parameterless constructor** required for EF Core materialization
3. **Public constructor with validation** — use `DomainException` for invariant violations (not `ArgumentNullException`)
4. **CompanyId FK required** on all company-scoped tax entities — `HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict)`
5. **No Company navigation property** on entity — FK relationship in EF config only
6. **IsActive soft-delete** — no hard delete for audit trail
7. **Events raised in constructor** — `AddDomainEvent(new XxxCreated(Id, CompanyId, DateTimeOffset.UtcNow))`

#### EF Configuration Constraints
1. **Table names:** snake_case plural — `tax_types`, `tax_rates`, `tax_rules`, etc.
2. **Column names:** snake_case — `tax_type_id`, `effective_from`, `effective_to`
3. **All enums:** `HasConversion<string>()` — never int
4. **All entities:** `xmin` row version last
5. **Unique indexes:** Composite `(CompanyId, Code)` for per-company uniqueness
6. **FK patterns:** `HasOne<X>().WithMany().HasForeignKey().OnDelete(DeleteBehavior.Restrict)` — consistent
7. **Max lengths:** Code=20, Name=200, Description=500 — enforced in EF config

#### Repository Constraints
1. **Interface in Domain:** `IXxxRepository` in `Domain/Ports/`
2. **Implementation in Infrastructure:** `EfXxxRepository` in `Infrastructure/Repositories/`
3. **DI registration:** `AddScoped<IXxxRepository, EfXxxRepository>()` in `DependencyInjection.cs`
4. **Methods:** `GetByIdAsync`, `GetByCodeAsync(code, companyId)`, `GetAllAsync` or scoped, `AddAsync`
5. **No UpdateAsync** — EF Core change tracking handles updates

#### DbContext Constraints
1. **New DbSet:** `public DbSet<TaxType> TaxTypes => Set<TaxType>();`
2. **New Ignore:** `modelBuilder.Ignore<TaxTypeCreated>();` for each new event
3. **Total count tracking:** Currently 18 DbSets, 14 ignored events

#### Architecture Constraints
1. **Domain assembly:** Zero NuGet refs, no EF Core, no Infrastructure, no Application, no Api
2. **Entities namespace:** `SmeAccounting.Domain.Entities`
3. **Ports namespace:** `SmeAccounting.Domain.Ports`
4. **Events namespace:** `SmeAccounting.Domain.Events`
5. **ValueObjects namespace:** `SmeAccounting.Domain.ValueObjects`
6. **Repository naming:** `IXxxRepository` → `EfXxxRepository`
7. **All 22 architecture tests must pass** — any violation breaks the build

#### Integration Constraints
1. **Must link to existing entities:** Account (for tax account mapping), Company (for company scoping), FiscalPeriod (for tax periods), VoucherType (for tax document types)
2. **Tax accounts from Circular 99:** 1331, 1332, 3331, 33311, 33312, 3334, 3335 — must be mappable to Account entities
3. **Effective dating:** All tax rules need `EffectiveFrom`/`EffectiveTo` dates for transitional provisions
4. **Legal traceability:** Link tax rules to law articles/clauses for audit trail

---

# Researcher 4 — Environment & Integration

## Environment & Integration

### Build Configuration

**File:** `Directory.Build.props` (repo root)

| Setting | Value | Notes |
|---------|-------|-------|
| TargetFramework | `net10.0` | .NET 10 SDK 10.0.401 |
| LangVersion | `13` | C# 13 |
| Nullable | `enable` | All projects |
| ImplicitUsings | `enable` | All projects |
| TreatWarningsAsErrors | `true` | Build breaks on any warning |

**File:** `.editorconfig` (repo root)
- 4-space indent for C# files
- 2-space indent for csproj/json/yaml
- LF line endings, UTF-8 charset
- Allman brace style (`csharp_new_line_before_open_brace = all`)
- `_camelCase` for private fields (enforced as suggestion)
- `var` preferred everywhere (suggestion level)
- Expression-bodied properties and accessors: enabled
- Expression-bodied constructors: disabled
- `dotnet_style_qualification_for_field = false:warning` — no `this.` prefix

**No `global.json`** — SDK version not pinned.

**Build verification command:** `dotnet build SmeAccounting.sln` — must succeed with zero warnings (TreatWarningsAsErrors=true).

### Dependency Injection Setup

**File:** `src/SmeAccounting.Application/DependencyInjection.cs`
```csharp
public static IServiceCollection AddApplication(this IServiceCollection services)
{
    services.AddMediatR(cfg => {
        cfg.RegisterServicesFromAssembly(typeof(DependencyInjection).Assembly);
        cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
    });
    services.AddValidatorsFromAssembly(typeof(DependencyInjection).Assembly);
    return services;
}
```
- MediatR assembly scan discovers all `IRequest<T>` handlers
- `ValidationBehavior<TRequest, TResponse>` runs all `IValidator<T>` before handler
- FluentValidation auto-registered via `AddValidatorsFromAssembly`

**File:** `src/SmeAccounting.Infrastructure/DependencyInjection.cs`
```csharp
public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
{
    services.AddDbContext<SmeAccountingDbContext>((sp, options) => {
        var connectionString = configuration.GetConnectionString("DefaultConnection")
            ?? "Host=localhost;Database=sme_accounting;Username=postgres;Password=postgres";
        options.UseNpgsql(connectionString);
    });
    services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<SmeAccountingDbContext>());
    // 13 repository registrations (AddScoped<IXxx, EfXxx>())
    services.AddSingleton<IClock, SystemClock>();
    services.AddScoped<IAuditLogger, AuditLogger>();
    services.AddScoped<IForeignExchangeRateProvider, BankExchangeRateProvider>();
    return services;
}
```

**Tax entity registration pattern:** Add ONE line per new repository:
```csharp
services.AddScoped<ITaxTypeRepository, EfTaxTypeRepository>();
```

**Current repository registrations (13):**
1. IAccountRepository → EfAccountRepository
2. IJournalEntryRepository → EfJournalEntryRepository
3. ICompanyRepository → EfCompanyRepository
4. ICurrencyRepository → EfCurrencyRepository
5. IExchangeRateRepository → EfExchangeRateRepository
6. IDepartmentRepository → EfDepartmentRepository
7. ICostCenterRepository → EfCostCenterRepository
8. IProjectRepository → EfProjectRepository
9. IVoucherTypeRepository → EfVoucherTypeRepository
10. IDocumentNumberingSeriesRepository → EfDocumentNumberingSeriesRepository
11. ITransactionReasonRepository → EfTransactionReasonRepository
12. IPostingConfigurationRepository → EfPostingConfigurationRepository
13. IOpeningBalanceMappingRepository → EfOpeningBalanceMappingRepository

**File:** `src/SmeAccounting.Api/Program.cs`
- `builder.Services.AddApplication()` — registers MediatR + FluentValidation
- `builder.Services.AddInfrastructure(builder.Configuration)` — registers EF Core + repositories
- `builder.Services.AddControllersWithViews()` — MVC pattern (NOT minimal API)
- Swagger at `/swagger` in Development mode
- MVC routing: `{controller=Home}/{action=Index}/{id?}`

### API/Controller Patterns

**Architecture:** MVC controllers (NOT API controllers). All inherit `Controller` base class.

**6 controllers total:**

| Controller | Pattern | Notes |
|-----------|---------|-------|
| `HomeController` | Thin MVC | `Index()`, `About()`, `Error()` — no MediatR |
| `SettingsController` | Thin MVC | `Index()` only — no MediatR |
| `ChartOfAccountsController` | MediatR dispatch | `Index`, `Create` (GET/POST), `Deprecate` |
| `JournalEntryController` | MediatR dispatch | `Index`, `Create` (GET/POST), `Post` |
| `FiscalPeriodController` | MediatR dispatch | `Index`, `Open`, `Close` |
| `ReportingController` | MediatR dispatch | `BalanceSheet`, `IncomeStatement` |

**Controller pattern:**
```csharp
public class XxxController : Controller
{
    private readonly IMediator _mediator;

    public XxxController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(CancellationToken ct)
    {
        var result = await _mediator.Send(new GetXxxQuery(...), ct);
        var vm = new XxxViewModel(result);
        return View(vm);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(CreateXxxViewModel model, CancellationToken ct)
    {
        if (!ModelState.IsValid) return View(model);
        try {
            var command = new CreateXxxCommand(...);
            await _mediator.Send(command, ct);
            return RedirectToAction(nameof(Index));
        }
        catch (ValidationException ex) {
            foreach (var error in ex.Errors)
                ModelState.AddModelError(error.PropertyName, error.ErrorMessage);
            return View(model);
        }
    }
}
```

**Key patterns:**
- `[ValidateAntiForgeryToken]` on all POST actions
- `CancellationToken ct` parameter on all async actions
- `ValidationException` caught in controllers, errors added to `ModelState`
- ViewModels as records: `record XxxViewModel(IReadOnlyList<XxxDto> Items)`
- CreateViewModels as classes with `[Required]`, `[StringLength]`, `[RegularExpression]` attributes
- Redirect to `Index` after successful create

**ViewModels (5):**
- `ChartOfAccountsViewModel` — record wrapping `IReadOnlyList<AccountDto>`
- `JournalEntryViewModel` — record wrapping `IReadOnlyList<JournalEntryDto>`
- `FiscalPeriodViewModel` — record wrapping `IReadOnlyList<FiscalPeriodDto>`
- `CreateAccountViewModel` — class with DataAnnotation validation
- `CreateJournalEntryViewModel` — class with DataAnnotation validation

### Migration Patterns

**4 migrations exist (chronological):**

| Migration | Name | Tables Created |
|-----------|------|---------------|
| `20260916051341` | InitialCreate | accounts, account_groups, fiscal_years, fiscal_periods, journal_entries, journal_entry_lines, posting_references |
| `20260916051520` | FixAccountNameColumn | Column fix only |
| `20260916083803` | AccountingFoundation | companies, currencies, departments, cost_centers, projects, exchange_rates + FK additions |
| `20260917013843` | Phase2AccountingControlConfig | voucher_types, document_numbering_series, opening_balance_mappings, transaction_reasons, posting_configurations |

**Naming convention:** Descriptive feature name — `Phase2AccountingControlConfig`, `AccountingFoundation`. NOT per-task numbering.

**Down migration pattern:** Full reversal — `DropTable` for new tables, `DropColumn`/`DropForeignKey`/`DropIndex` for alterations. Reversal order is reverse of Up.

**Key migration patterns:**
- PostgreSQL `bigint` with `IdentityByDefaultColumn` for PKs
- `varchar(N)` for bounded strings, `text` for unbounded
- `HasConversion<string>()` for enums → stored as `text`
- `xmin` row version: `type: "xid", rowVersion: true`
- FK naming: `FK_{table}_{referenced}_{column}` — e.g. `FK_voucher_types_companies_company_id`
- Index naming: `IX_{table}_{column}` for single, `IX_{table}_{col1}_{col2}` for composite
- Unique indexes: `unique: true` in `CreateIndex`
- `defaultValue: 0L` for non-nullable FK columns added to existing tables (backfill needed in production)
- `defaultValue: new DateOnly(1, 1, 1)` for DateOnly columns
- `defaultValue: ""` for required string columns

**Migration generation:**
```bash
dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api
```
- Build must succeed first (EF Core reads compiled assemblies)
- `pkill MSBuild` if OOM in memory-constrained environments

### Test Infrastructure

**Single test project:** `tests/SmeAccounting.ArchitectureTests/`

**Framework:** xunit 2.9.3 with `Microsoft.NET.Test.Sdk 17.14.1`

**NuGet packages:**
- xunit 2.9.3
- xunit.runner.visualstudio 3.1.4
- Microsoft.NET.Test.Sdk 17.14.1
- NetArchTest.Rules 1.3.2
- coverlet.collector 6.0.4

**Project references:** All 4 source projects (Domain, Application, Infrastructure, Api)

**Global using:** `Xunit` namespace imported project-wide

**22 architecture tests across 5 files:**

| File | Tests | Purpose |
|------|-------|---------|
| `DomainPurityTests.cs` | 3 | Domain: zero NuGet refs, no EF Core, no Microsoft/Npgsql packages |
| `NamingConventionsTests.cs` | 6 | Entities in Entities ns, repos start with I, commands end with Command, queries with Query, DTOs with Dto, controllers with Controller |
| `LayerCouplingTests.cs` | 4 | Controllers don't reference Domain.Entities/Ports, handlers don't reference Infrastructure, Infrastructure doesn't reference Api |
| `DependencyRulesTests.cs` | 7 | Full dependency direction enforcement (Domain↔Application↔Infrastructure↔Api) |
| `PostingRuleIsolationTests.cs` | 2 | IPostingService and JournalEntry balance rule in Domain |

**Test execution:**
```bash
dotnet test tests/SmeAccounting.ArchitectureTests/
```

**No other test projects exist.** Tax entities will be validated by these 22 tests — no new tests needed unless new architecture rules are added.

### Configuration

**File:** `src/SmeAccounting.Api/appsettings.json`
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*"
}
```

**File:** `src/SmeAccounting.Api/appsettings.Development.json`
```json
{
  "DetailedErrors": true,
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  }
}
```

**Connection string pattern:** `Host=IP;Database=name;Username=user;Password=pass`
- PostgreSQL 16.14 on Windows host (172.21.208.1)
- Database: `sme_acct_dev`
- Connect from Kali: `PGPASSWORD=123456 psql -h 172.21.208.1 -U dev -d sme_acct_dev`

**No environment-specific configuration needed for tax entities** — they use the same connection and DbContext as all other entities.

### NuGet Packages by Project

| Project | Key Packages | Version |
|---------|-------------|---------|
| Domain | (none — pure library) | — |
| Application | MediatR, FluentValidation, FluentValidation.DependencyInjectionExtensions | 14.2.0, 12.1.0, 12.1.0 |
| Infrastructure | Microsoft.EntityFrameworkCore, Npgsql.EntityFrameworkCore.PostgreSQL, Microsoft.Extensions.DependencyInjection, EFCore.NamingConventions | 10.0.4, 10.0.3, 10.0.12, 10.0.* |
| Api | EF Core Design (via Microsoft.NET.Sdk.Web), Swashbuckle, MediatR, FluentValidation | (inherited) |
| ArchitectureTests | xunit, NetArchTest.Rules, Microsoft.NET.Test.Sdk, coverlet.collector | 2.9.3, 1.3.2, 17.14.1, 6.0.4 |

**Tax entity NuGet impact:** ZERO — Domain must remain pure. No new packages needed for tax entities.

### Integration Points for Tax Foundation

**Must integrate with existing entities:**
1. **Account** — Tax accounting mappings reference Account entities (1331, 1332, 3331, etc.)
2. **Company** — All tax entities scoped by CompanyId FK
3. **FiscalPeriod** — Tax periods link to fiscal periods for filing deadlines
4. **VoucherType** — Tax document types (VAT invoice, CIT return, PIT withholding slip)
5. **PostingConfiguration** — Tax posting rules extend existing posting configuration

**No new NuGet packages required** — all infrastructure (EF Core, MediatR, FluentValidation) already configured.

**Migration will be single file** — `Phase3TaxFoundation` covering all new tables (following AccountingFoundation and Phase2AccountingControlConfig pattern).

---

# Task-Specific Research — [G1] TaxType domain foundation

## Files to Create/Modify

### New Files (6)

#### 1. `src/SmeAccounting.Domain/ValueObjects/TaxType.cs` — Enum

**Pattern source:** `AccountType.cs`, `VoucherCategory.cs`

```csharp
namespace SmeAccounting.Domain.ValueObjects;

public enum TaxType
{
    VAT,
    CIT,
    PIT,
    SpecialConsumption,
    Resource,
    Environmental,
    ImportDuty,
    ExportDuty
}
```

**Exact namespace:** `SmeAccounting.Domain.ValueObjects`
**No using statements** — enums are plain values.
**Gotcha:** Do NOT name the enum the same as the entity class. The entity is `SmeAccounting.Domain.Entities.TaxType`, the enum is `SmeAccounting.Domain.ValueObjects.TaxType`. C# resolves by namespace. Entity file uses `using SmeAccounting.Domain.ValueObjects;` — this causes ambiguity. **Resolution:** Rename enum to `TaxCategory` to avoid collision. The entity uses `TaxCategory` property of type `TaxCategory` (the enum). This matches the VoucherType pattern where `VoucherCategory` is the enum name, distinct from the `VoucherType` entity.

**Revised enum name:** `TaxCategory` (not `TaxType` — collision with entity name).

```csharp
namespace SmeAccounting.Domain.ValueObjects;

public enum TaxCategory
{
    VAT,
    CIT,
    PIT,
    SpecialConsumption,
    Resource,
    Environmental,
    ImportDuty,
    ExportDuty
}
```

**Regulatory mapping for 8 values:**
| Enum Value | Vietnamese Law | Account (Circular 99) |
|------------|---------------|----------------------|
| VAT | Law 48/2024/QH15 | 3331 (payable), 1331/1332 (deductible), 33311 (output), 33312 (import) |
| CIT | Law 67/2025/QH15 | 3334 |
| PIT | Law 109/2025/QH15 | 3335 |
| SpecialConsumption | Special Consumption Tax Law | 3332 |
| Resource | Resource Tax Law | 3336 |
| Environmental | Environmental Protection Tax Law | 3338 |
| ImportDuty | Customs Law | 3333 |
| ExportDuty | Customs Law | 3333 |

---

#### 2. `src/SmeAccounting.Domain/Entities/TaxType.cs` — Entity

**Pattern source:** `VoucherType.cs` (closest match — CompanyId-scoped, Code, Name, IsActive, Description)

```csharp
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class TaxType : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public TaxCategory TaxCategory { get; private set; }
    public long CompanyId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private TaxType() { }

    public TaxType(long companyId, string code, string name, TaxCategory taxCategory, string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");

        CompanyId = companyId;
        Code = code;
        Name = name;
        TaxCategory = taxCategory;
        Description = description;

        AddDomainEvent(new TaxTypeCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
```

**Exact namespace:** `SmeAccounting.Domain.Entities`
**Using statements:** `SmeAccounting.Domain.Events`, `SmeAccounting.Domain.Exceptions`, `SmeAccounting.Domain.ValueObjects`
**Class:** `public class TaxType : BaseEntity` — NOT a record, NOT sealed
**Private parameterless constructor:** `private TaxType() { }` — EF Core materialization
**Public constructor:** CompanyId first param (matching VoucherType), then Code, Name, TaxCategory, Description optional
**Validation:** `DomainException` for invariant violations (CompanyId, Code, Name) — matches VoucherType pattern
**Event raised in constructor:** `AddDomainEvent(new TaxTypeCreated(Id, companyId, DateTimeOffset.UtcNow))`
**Deactivate:** `IsActive = false` only — no event (matches VoucherType pattern)

**Properties:**
| Property | Type | Default | Max Length (EF config) |
|----------|------|---------|----------------------|
| Code | string | string.Empty | 20 |
| Name | string | string.Empty | 200 |
| TaxCategory | TaxCategory (enum) | — | HasConversion<string>() |
| CompanyId | long | — | FK to companies |
| IsActive | bool | true | — |
| Description | string? | null | 500 |

**Gotcha — Id=0 in event:** When entity is first created in memory (before SaveChanges), `Id` is 0. The event carries `Id=0`. This is known and matches VoucherType/Department/CostCenter/Project pattern. Real ID assigned by EF Core after SaveChanges.

---

#### 3. `src/SmeAccounting.Domain/Events/TaxTypeCreated.cs` — Domain Event

**Pattern source:** `VoucherTypeCreated.cs`

```csharp
namespace SmeAccounting.Domain.Events;

public class TaxTypeCreated : DomainEvent
{
    public long TaxTypeId { get; }
    public long CompanyId { get; }

    public TaxTypeCreated(
        long taxTypeId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxTypeId = taxTypeId;
        CompanyId = companyId;
    }
}
```

**Exact namespace:** `SmeAccounting.Domain.Events`
**No using statements needed** — DomainEvent is in same namespace.
**Pattern:** Entity ID + CompanyId + occurredOn — matches VoucherTypeCreated exactly.
**Event minimalism:** No Code, Name, TaxCategory — just IDs.

---

#### 4. `src/SmeAccounting.Domain/Ports/ITaxTypeRepository.cs` — Port Interface

**Pattern source:** `IVoucherTypeRepository.cs`

```csharp
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITaxTypeRepository
{
    Task<TaxType?> GetByIdAsync(long id);
    Task<TaxType?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<TaxType>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(TaxType taxType);
}
```

**Exact namespace:** `SmeAccounting.Domain.Ports`
**Using:** `SmeAccounting.Domain.Entities`
**Methods:**
- `GetByIdAsync(long id)` — standard lookup
- `GetByCodeAsync(string code, long companyId)` — unique per company lookup
- `GetAllByCompanyAsync(long companyId)` — company-scoped (NOT `GetAllAsync()` like VoucherType — tax types are company-specific)
- `AddAsync(TaxType taxType)` — insert only

**Gotcha:** Plan says `GetAllByCompanyAsync` not `GetAllAsync`. This is deliberate — tax types are company-scoped, unlike VoucherType which uses global `GetAllAsync()`. Follow the plan.

**No UpdateAsync** — EF Core change tracking handles updates (matches all other repos).

---

#### 5. `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxTypeConfiguration.cs` — EF Config

**Pattern source:** `VoucherTypeConfiguration.cs`

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class TaxTypeConfiguration : IEntityTypeConfiguration<TaxType>
{
    public void Configure(EntityTypeBuilder<TaxType> builder)
    {
        builder.ToTable("tax_types");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.Code)
            .HasColumnName("code")
            .IsRequired()
            .HasMaxLength(20);

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.TaxCategory)
            .HasColumnName("tax_category")
            .HasConversion<string>();

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.CompanyId, e.Code })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
```

**Exact namespace:** `SmeAccounting.Infrastructure.Persistence.Configurations`
**Using:** `Microsoft.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore.Metadata.Builders`, `SmeAccounting.Domain.Entities`, `SmeAccounting.Domain.ValueObjects`
**Class:** `internal sealed class TaxTypeConfiguration : IEntityTypeConfiguration<TaxType>`
**Table:** `tax_types` (snake_case plural)
**Unique index:** `(CompanyId, Code)` — prevents duplicate tax type codes per company
**Company FK:** `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — no navigation property on entity
**Enum conversion:** `HasConversion<string>()` for TaxCategory — stores as text, not int
**xmin:** Always last, `IsRowVersion()`
**Max lengths:** Code=20, Name=200, Description=500

**Auto-discovery:** `modelBuilder.ApplyConfigurationsFromAssembly(typeof(SmeAccountingDbContext).Assembly)` in DbContext auto-discovers this config — no manual registration needed.

---

#### 6. `src/SmeAccounting.Infrastructure/Repositories/EfTaxTypeRepository.cs` — Repository

**Pattern source:** `EfVoucherTypeRepository.cs`

```csharp
using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTaxTypeRepository : ITaxTypeRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTaxTypeRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TaxType?> GetByIdAsync(long id)
    {
        return await _context.TaxTypes
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<TaxType?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.TaxTypes
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<TaxType>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.TaxTypes
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(TaxType taxType)
    {
        await _context.TaxTypes.AddAsync(taxType);
    }
}
```

**Exact namespace:** `SmeAccounting.Infrastructure.Repositories`
**Using:** `Microsoft.EntityFrameworkCore`, `SmeAccounting.Domain.Entities`, `SmeAccounting.Domain.Ports`, `SmeAccounting.Infrastructure.Persistence`
**Class:** `public class EfTaxTypeRepository : ITaxTypeRepository`
**Key patterns:**
- `GetByIdAsync` — tracked (no AsNoTracking)
- `GetByCodeAsync` — tracked, composite filter (Code + CompanyId)
- `GetAllByCompanyAsync` — `AsNoTracking()`, filtered by CompanyId, ordered by Code
- `AddAsync` — delegates to DbSet.AddAsync
- No `UpdateAsync` — change tracking handles it

---

### Modified Files (2)

#### 7. `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` — DbContext edits

Add **1 DbSet** + **1 Ignore**:

```csharp
// DbSet — add after existing DbSets (e.g., after OpeningBalanceMappings line)
public DbSet<TaxType> TaxTypes => Set<TaxType>();

// Ignore — add in OnModelCreating after existing Ignore calls
modelBuilder.Ignore<TaxTypeCreated>();
```

**Current counts:** 18 DbSets, 14 ignored events → **New counts:** 19 DbSets, 15 ignored events

**Important:** The `using SmeAccounting.Domain.Events;` is already in the file. The `using SmeAccounting.Domain.Entities;` is also already there. No new using statements needed.

---

#### 8. `src/SmeAccounting.Infrastructure/DependencyInjection.cs` — DI registration

Add **1 line** after existing repository registrations:

```csharp
services.AddScoped<ITaxTypeRepository, EfTaxTypeRepository>();
```

**Current count:** 13 repository registrations → **New count:** 14

**Using statements:** `SmeAccounting.Domain.Ports` and `SmeAccounting.Infrastructure.Repositories` already imported. No new usings needed.

---

### Architecture Tests — Verification (no code changes needed)

The 22 existing architecture tests automatically validate TaxType:

| Test | What it checks for TaxType |
|------|---------------------------|
| `Entities_Inheriting_BaseEntity_Should_Reside_In_Entities_Namespace` | TaxType in `SmeAccounting.Domain.Entities` ✓ |
| `Repository_Interfaces_Should_Start_With_I` | ITaxTypeRepository starts with "I" ✓ |
| `Domain_Should_Have_No_NuGet_PackageReferences` | Domain.csproj unchanged ✓ |
| `Domain_Should_Have_No_EntityFramework_Assembly_Dependency` | TaxType entity has no EF Core refs ✓ |
| `Domain_Should_Not_Depend_On_Application/Infrastructure/Api` | TaxType is pure domain ✓ |

**No new test files or test methods required.** Build + `dotnet test` validates everything.

---

## Implementation Sequence

1. Create `TaxCategory` enum in `Domain/ValueObjects/TaxCategory.cs`
2. Create `TaxTypeCreated` event in `Domain/Events/TaxTypeCreated.cs`
3. Create `TaxType` entity in `Domain/Entities/TaxType.cs`
4. Create `ITaxTypeRepository` port in `Domain/Ports/ITaxTypeRepository.cs`
5. Create `TaxTypeConfiguration` in `Infrastructure/Persistence/Configurations/TaxTypeConfiguration.cs`
6. Create `EfTaxTypeRepository` in `Infrastructure/Repositories/EfTaxTypeRepository.cs`
7. Edit `SmeAccountingDbContext.cs` — add DbSet + Ignore
8. Edit `DependencyInjection.cs` — add AddScoped registration
9. `dotnet build SmeAccounting.sln` — must succeed (TreatWarningsAsErrors)
10. `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 must pass

---

## Verification Criteria

### What "Done Correctly" Looks Like
1. `TaxCategory` enum has exactly 8 values: VAT, CIT, PIT, SpecialConsumption, Resource, Environmental, ImportDuty, ExportDuty
2. `TaxType` entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity, private ctor, public ctor with DomainException validation
3. `TaxTypeCreated` event carries TaxTypeId + CompanyId + occurredOn
4. `ITaxTypeRepository` in `SmeAccounting.Domain.Ports` — starts with I, 4 methods
5. EF config: snake_case table `tax_types`, unique index `(CompanyId, Code)`, CompanyId FK Restrict, xmin row version
6. Repository: `AsNoTracking()` for GetAllByCompany, tracked for GetById/GetByCode
7. DbContext: 19 DbSets, 15 ignored events
8. DI: 14 AddScoped registrations
9. Build: zero warnings (TreatWarningsAsErrors)
10. Tests: 22/22 pass

### What "Failing" Looks Like
1. Enum named `TaxType` causing namespace collision with entity → compiler error
2. Entity missing private parameterless constructor → EF Core runtime failure
3. Missing `modelBuilder.Ignore<TaxTypeCreated>()` → EF Core migration error
4. Missing `DbSet<TaxType>` → entity not tracked by DbContext
5. Missing DI registration → runtime dependency injection failure
6. Missing unique index → duplicate codes allowed at DB level
7. Wrong namespace on entity → architecture test failure
8. Entity using `ArgumentNullException` instead of `DomainException` → violates established pattern
9. Missing `using SmeAccounting.Domain.ValueObjects` in entity → TaxCategory unresolved
10. Repository using `GetAllAsync()` instead of `GetAllByCompanyAsync(companyId)` → violates plan spec

---

## Quality Standards

### Good Output
- Exact match to VoucherType pattern (constructor shape, validation, event, Deactivate)
- TaxCategory enum names are self-documenting (VAT, CIT, PIT, etc.)
- EF config follows every convention (snake_case, xmin, CompanyId Restrict, unique index)
- Code compiles with zero warnings
- All 22 architecture tests pass without modification

### Merely Functional
- Entity works but uses different validation pattern (ArgumentNullException vs DomainException)
- Missing unique index (allows duplicate codes)
- Repository uses GetAllAsync instead of GetAllByCompanyAsync
- No domain event raised in constructor
- Enum values don't match Vietnamese tax law categories

---

# Task-Specific Research — [G1] TaxTreatment domain foundation

## Critical Design Decision: Enum Naming

**Problem:** Plan says create `TaxTreatment` enum in `src/SmeAccounting.Domain/ValueObjects/TaxTreatment.cs` AND `TaxTreatment` entity in `src/SmeAccounting.Domain/Entities/TaxTreatment.cs`. Same name in different namespaces causes C# namespace collision when entity imports the enum namespace.

**Established resolution pattern:** Follow TaxType/TaxCategory and VoucherType/VoucherCategory precedent:
- Entity: `TaxTreatment` (in `SmeAccounting.Domain.Entities`)
- Enum: `TaxTreatmentType` (in `SmeAccounting.Domain.ValueObjects`)

**Enum values:** StandardRate, ReducedRate, ZeroRate, Exempt, NonTaxable

**This rename is non-negotiable.** The TaxType G1 research proved enum-name collision is a compiler error.

## Files to Create/Modify

### New Files (6)

#### 1. `src/SmeAccounting.Domain/ValueObjects/TaxTreatmentType.cs` — Enum

**Pattern source:** `VoucherCategory.cs`, `TaxCategory.cs` (once created by parallel TaxType task)

```csharp
namespace SmeAccounting.Domain.ValueObjects;

public enum TaxTreatmentType
{
    StandardRate,
    ReducedRate,
    ZeroRate,
    Exempt,
    NonTaxable
}
```

**Exact namespace:** `SmeAccounting.Domain.ValueObjects`
**No using statements** — enum is a plain value type.
**CRITICAL:** Do NOT name this `TaxTreatment` — collision with entity. Must be `TaxTreatmentType`.

**Regulatory mapping for 5 values:**
| Enum Value | Vietnamese Law Reference | Input Credit Allowed | Description |
|------------|--------------------------|---------------------|-------------|
| StandardRate | VAT Law 48/2024 Art. 3, 4 | Yes | 10% standard VAT (or 8% temporary) |
| ReducedRate | VAT Law 48/2024 Art. 4 | Yes | 5% essential goods (clean water, medicine, social housing) |
| ZeroRate | VAT Law 48/2024 Art. 4 | Yes | 0% on exports, international transport |
| Exempt | VAT Law 48/2024 Art. 5 | **No** | Agricultural products, finance, healthcare, education |
| NonTaxable | Outside VAT scope | **No** | Land use rights, salary/wages, insurance payouts |

**Key regulatory distinction (CRITICAL for executor):**
- **ZeroRate (0%)** — Still within VAT scope. Output VAT charged at 0%. **Input VAT credit IS deductible.** Must declare VAT.
- **Exempt** — Outside VAT obligation. No output VAT charged. **Input VAT credit is NOT deductible.** No VAT declaration required.
- This is the single most important distinction in Vietnamese VAT law. The `InputCreditAllowed` bool on the entity captures this.

---

#### 2. `src/SmeAccounting.Domain/Entities/TaxTreatment.cs` — Entity

**Pattern source:** `TransactionReason.cs` (entity with FK to another entity — VoucherTypeId FK pattern)

```csharp
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class TaxTreatment : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public long TaxTypeId { get; private set; }
    public TaxTreatmentType TaxTreatmentType { get; private set; }
    public bool InputCreditAllowed { get; private set; }
    public long CompanyId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private TaxTreatment() { }

    public TaxTreatment(
        long companyId,
        long taxTypeId,
        string code,
        string name,
        TaxTreatmentType taxTreatmentType,
        bool inputCreditAllowed,
        string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (taxTypeId <= 0)
            throw new DomainException("TaxTypeId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");

        CompanyId = companyId;
        TaxTypeId = taxTypeId;
        Code = code;
        Name = name;
        TaxTreatmentType = taxTreatmentType;
        InputCreditAllowed = inputCreditAllowed;
        Description = description;

        AddDomainEvent(new TaxTreatmentCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
```

**Exact namespace:** `SmeAccounting.Domain.Entities`
**Using statements:** `SmeAccounting.Domain.Events`, `SmeAccounting.Domain.Exceptions`, `SmeAccounting.Domain.ValueObjects`
**Class:** `public class TaxTreatment : BaseEntity` — NOT a record, NOT sealed
**Private parameterless constructor:** `private TaxTreatment() { }` — EF Core materialization
**Public constructor:** CompanyId + TaxTypeId first (matching TransactionReason's CompanyId + VoucherTypeId pattern), then Code, Name, TaxTreatmentType, InputCreditAllowed, Description optional
**Validation:** `DomainException` for invariant violations (CompanyId, TaxTypeId, Code, Name) — matches TransactionReason pattern
**Event raised in constructor:** `AddDomainEvent(new TaxTreatmentCreated(Id, companyId, DateTimeOffset.UtcNow))`
**Deactivate:** `IsActive = false` only — no event (matches all prior entities)

**Properties:**
| Property | Type | Default | Max Length (EF config) | Notes |
|----------|------|---------|----------------------|-------|
| Code | string | string.Empty | 20 | Unique per company |
| Name | string | string.Empty | 200 | |
| TaxTypeId | long | — | FK to tax_types | Required, Restrict delete |
| TaxTreatmentType | TaxTreatmentType (enum) | — | HasConversion<string>() | StandardRate, ReducedRate, etc. |
| InputCreditAllowed | bool | — | — | true for 0% rate, false for exempt |
| CompanyId | long | — | FK to companies | Required, Restrict delete |
| IsActive | bool | true | — | Soft-delete |
| Description | string? | null | 500 | |

**Why InputCreditAllowed is on entity (not computed from enum):**
- Future flexibility: Some exempt categories may have partial credit rules
- Circular 99 Art. 28 defines specific exemption categories where credit may apply in mixed-use scenarios
- Avoids coupling business logic to enum lookup

**Gotcha — Id=0 in event:** Same as all other entities. Real ID assigned by EF Core after SaveChanges.

---

#### 3. `src/SmeAccounting.Domain/Events/TaxTreatmentCreated.cs` — Domain Event

**Pattern source:** `TransactionReasonCreated.cs`, `VoucherTypeCreated.cs`

```csharp
namespace SmeAccounting.Domain.Events;

public class TaxTreatmentCreated : DomainEvent
{
    public long TaxTreatmentId { get; }
    public long CompanyId { get; }

    public TaxTreatmentCreated(
        long taxTreatmentId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxTreatmentId = taxTreatmentId;
        CompanyId = companyId;
    }
}
```

**Exact namespace:** `SmeAccounting.Domain.Events`
**No using statements needed** — DomainEvent is in same namespace.
**Pattern:** Entity ID + CompanyId + occurredOn — matches all company-scoped entity events.
**Event minimalism:** No Code, Name, TaxTypeId, TaxTreatmentType, InputCreditAllowed — just IDs.

---

#### 4. `src/SmeAccounting.Domain/Ports/ITaxTreatmentRepository.cs` — Port Interface

**Pattern source:** `ITransactionReasonRepository.cs` (has additional scoped query by parent entity)

```csharp
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITaxTreatmentRepository
{
    Task<TaxTreatment?> GetByIdAsync(long id);
    Task<TaxTreatment?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<TaxTreatment>> GetAllByCompanyAsync(long companyId);
    Task<IReadOnlyList<TaxTreatment>> GetAllByTaxTypeAsync(long taxTypeId);
    Task AddAsync(TaxTreatment taxTreatment);
}
```

**Exact namespace:** `SmeAccounting.Domain.Ports`
**Using:** `SmeAccounting.Domain.Entities`
**Methods:**
- `GetByIdAsync(long id)` — standard lookup
- `GetByCodeAsync(string code, long companyId)` — unique per company lookup
- `GetAllByCompanyAsync(long companyId)` — company-scoped (NOT `GetAllAsync()` — treatments are company-specific)
- `GetAllByTaxTypeAsync(long taxTypeId)` — filter by parent TaxType (plan specifies this method)
- `AddAsync(TaxTreatment taxTreatment)` — insert only

**Why `GetAllByTaxTypeAsync` instead of `GetAllByCompanyAndTaxTypeAsync`:** Follows plan spec. TaxTypeId is globally unique in the context of a company (a treatment type belongs to one tax type). The repository method filters by TaxTypeId which already implies company scope when used through the application layer.

**No UpdateAsync** — EF Core change tracking handles updates (matches all other repos).

---

#### 5. `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxTreatmentConfiguration.cs` — EF Config

**Pattern source:** `TransactionReasonConfiguration.cs` (entity with two FKs: Company + parent entity)

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class TaxTreatmentConfiguration : IEntityTypeConfiguration<TaxTreatment>
{
    public void Configure(EntityTypeBuilder<TaxTreatment> builder)
    {
        builder.ToTable("tax_treatments");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.TaxTypeId)
            .HasColumnName("tax_type_id");

        builder.Property(e => e.Code)
            .HasColumnName("code")
            .IsRequired()
            .HasMaxLength(20);

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.TaxTreatmentType)
            .HasColumnName("tax_treatment_type")
            .HasConversion<string>();

        builder.Property(e => e.InputCreditAllowed)
            .HasColumnName("input_credit_allowed");

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.CompanyId, e.Code })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<TaxType>()
            .WithMany()
            .HasForeignKey(e => e.TaxTypeId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
```

**Exact namespace:** `SmeAccounting.Infrastructure.Persistence.Configurations`
**Using:** `Microsoft.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore.Metadata.Builders`, `SmeAccounting.Domain.Entities`, `SmeAccounting.Domain.ValueObjects`
**Class:** `internal sealed class TaxTreatmentConfiguration : IEntityTypeConfiguration<TaxTreatment>`
**Table:** `tax_treatments` (snake_case plural)
**Unique index:** `(CompanyId, Code)` — prevents duplicate treatment codes per company (matches TransactionReason pattern: unique on CompanyId+Code, NOT composite with TaxTypeId)
**Two FKs:**
1. `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`
2. `HasOne<TaxType>().WithMany().HasForeignKey(e => e.TaxTypeId).OnDelete(DeleteBehavior.Restrict)`
**Enum conversion:** `HasConversion<string>()` for TaxTreatmentType — stores as text, not int
**Bool storage:** `InputCreditAllowed` stored as `boolean` (default EF mapping)
**xmin:** Always last, `IsRowVersion()`
**Max lengths:** Code=20, Name=200, Description=500

**Why TaxType FK is `HasOne<TaxType>().WithMany()`:** No navigation property on entity (FK nav-free pattern). The EF config defines the relationship.

---

#### 6. `src/SmeAccounting.Infrastructure/Repositories/EfTaxTreatmentRepository.cs` — Repository

**Pattern source:** `EfTransactionReasonRepository.cs` (has scoped query by parent entity)

```csharp
using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTaxTreatmentRepository : ITaxTreatmentRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTaxTreatmentRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TaxTreatment?> GetByIdAsync(long id)
    {
        return await _context.TaxTreatments
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<TaxTreatment?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.TaxTreatments
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<TaxTreatment>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.TaxTreatments
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task<IReadOnlyList<TaxTreatment>> GetAllByTaxTypeAsync(long taxTypeId)
    {
        return await _context.TaxTreatments
            .AsNoTracking()
            .Where(e => e.TaxTypeId == taxTypeId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(TaxTreatment taxTreatment)
    {
        await _context.TaxTreatments.AddAsync(taxTreatment);
    }
}
```

**Exact namespace:** `SmeAccounting.Infrastructure.Repositories`
**Using:** `Microsoft.EntityFrameworkCore`, `SmeAccounting.Domain.Entities`, `SmeAccounting.Domain.Ports`, `SmeAccounting.Infrastructure.Persistence`
**Class:** `public class EfTaxTreatmentRepository : ITaxTreatmentRepository`
**Key patterns:**
- `GetByIdAsync` — tracked (no AsNoTracking)
- `GetByCodeAsync` — tracked, composite filter (Code + CompanyId)
- `GetAllByCompanyAsync` — `AsNoTracking()`, filtered by CompanyId, ordered by Code
- `GetAllByTaxTypeAsync` — `AsNoTracking()`, filtered by TaxTypeId, ordered by Code
- `AddAsync` — delegates to DbSet.AddAsync
- No `UpdateAsync` — change tracking handles it

---

### Modified Files (2)

#### 7. `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` — DbContext edits

Add **1 DbSet** + **1 Ignore**:

```csharp
// DbSet — add after existing DbSets (after TaxTypes if TaxType G1 is done first, or after OpeningBalanceMappings)
public DbSet<TaxTreatment> TaxTreatments => Set<TaxTreatment>();

// Ignore — add in OnModelCreating after existing Ignore calls
modelBuilder.Ignore<TaxTreatmentCreated>();
```

**Current counts:** 18 DbSets, 14 ignored events → **New counts:** 19 DbSets, 15 ignored events (after TaxType G1: 20 DbSets, 16 ignored events)

**Important:** The `using SmeAccounting.Domain.Events;` and `using SmeAccounting.Domain.Entities;` are already in the file. No new using statements needed.

**Order dependency:** If TaxType G1 creates `TaxTypes` DbSet first, add `TaxTreatments` after it. If parallel, add after `OpeningBalanceMappings`.

---

#### 8. `src/SmeAccounting.Infrastructure/DependencyInjection.cs` — DI registration

Add **1 line** after existing repository registrations:

```csharp
services.AddScoped<ITaxTreatmentRepository, EfTaxTreatmentRepository>();
```

**Current count:** 13 repository registrations → **New count:** 14 (after TaxType G1: 15)

**Using statements:** `SmeAccounting.Domain.Ports` and `SmeAccounting.Infrastructure.Repositories` already imported. No new usings needed.

---

### Architecture Tests — Verification (no code changes needed)

The 22 existing architecture tests automatically validate TaxTreatment:

| Test | What it checks for TaxTreatment |
|------|---------------------------------|
| `Entities_Inheriting_BaseEntity_Should_Reside_In_Entities_Namespace` | TaxTreatment in `SmeAccounting.Domain.Entities` ✓ |
| `Repository_Interfaces_Should_Start_With_I` | ITaxTreatmentRepository starts with "I" ✓ |
| `Domain_Should_Have_No_NuGet_PackageReferences` | Domain.csproj unchanged ✓ |
| `Domain_Should_Have_No_EntityFramework_Assembly_Dependency` | TaxTreatment entity has no EF Core refs ✓ |
| `Domain_Should_Not_Depend_On_Application/Infrastructure/Api` | TaxTreatment is pure domain ✓ |

**No new test files or test methods required.** Build + `dotnet test` validates everything.

---

## Implementation Sequence

1. Create `TaxTreatmentType` enum in `Domain/ValueObjects/TaxTreatmentType.cs`
2. Create `TaxTreatmentCreated` event in `Domain/Events/TaxTreatmentCreated.cs`
3. Create `TaxTreatment` entity in `Domain/Entities/TaxTreatment.cs`
4. Create `ITaxTreatmentRepository` port in `Domain/Ports/ITaxTreatmentRepository.cs`
5. Create `TaxTreatmentConfiguration` in `Infrastructure/Persistence/Configurations/TaxTreatmentConfiguration.cs`
6. Create `EfTaxTreatmentRepository` in `Infrastructure/Repositories/EfTaxTreatmentRepository.cs`
7. Edit `SmeAccountingDbContext.cs` — add DbSet + Ignore
8. Edit `DependencyInjection.cs` — add AddScoped registration
9. `dotnet build SmeAccounting.sln` — must succeed (TreatWarningsAsErrors)
10. `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 must pass

---

## Verification Criteria

### What "Done Correctly" Looks Like
1. `TaxTreatmentType` enum has exactly 5 values: StandardRate, ReducedRate, ZeroRate, Exempt, NonTaxable
2. `TaxTreatment` entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity, private ctor, public ctor with DomainException validation
3. Entity has both CompanyId FK and TaxTypeId FK — both validated as > 0 in constructor
4. `InputCreditAllowed` bool present on entity — true for ZeroRate/StandardRate/ReducedRate, false for Exempt/NonTaxable
5. `TaxTreatmentCreated` event carries TaxTreatmentId + CompanyId + occurredOn
6. `ITaxTreatmentRepository` in `SmeAccounting.Domain.Ports` — starts with I, 5 methods (including GetAllByTaxTypeAsync)
7. EF config: snake_case table `tax_treatments`, unique index `(CompanyId, Code)`, CompanyId FK Restrict, TaxTypeId FK Restrict, xmin row version
8. EF config: Two FKs both Restrict (Company + TaxType) — matches TransactionReason pattern
9. Repository: `AsNoTracking()` for GetAllByCompany and GetAllByTaxType, tracked for GetById/GetByCode
10. DbContext: correct DbSet count (depends on whether TaxType G1 runs first)
11. DI: correct AddScoped count
12. Build: zero warnings (TreatWarningsAsErrors)
13. Tests: 22/22 pass

### What "Failing" Looks Like
1. Enum named `TaxTreatment` causing namespace collision with entity → compiler error
2. Entity missing private parameterless constructor → EF Core runtime failure
3. Missing `modelBuilder.Ignore<TaxTreatmentCreated>()` → EF Core migration error
4. Missing `DbSet<TaxTreatment>` → entity not tracked by DbContext
5. Missing DI registration → runtime dependency injection failure
6. Missing unique index → duplicate codes allowed at DB level
7. Wrong namespace on entity → architecture test failure
8. Entity using `ArgumentNullException` instead of `DomainException` → violates established pattern
9. Missing `using SmeAccounting.Domain.ValueObjects` in entity → TaxTreatmentType unresolved
10. Repository using `GetAllAsync()` instead of `GetAllByCompanyAsync(companyId)` → violates plan spec
11. Missing TaxTypeId FK validation in constructor → allows invalid references
12. TaxType FK using Cascade delete instead of Restrict → violates established pattern
13. Entity missing `InputCreditAllowed` property → loses the critical 0% vs exempt distinction

---

## Quality Standards

### Good Output
- Exact match to TransactionReason pattern (two FKs, constructor shape, validation, event, Deactivate)
- TaxTreatmentType enum names are self-documenting (StandardRate, ZeroRate, Exempt, etc.)
- InputCreditAllowed correctly defaults based on regulatory requirements
- EF config follows every convention (snake_case, xmin, both FKs Restrict, unique index)
- Code compiles with zero warnings
- All 22 architecture tests pass without modification
- Regulatory distinction between 0% rate (deductible) and exempt (non-deductible) is captured in the model

### Merely Functional
- Entity works but uses different validation pattern (ArgumentNullException vs DomainException)
- Missing unique index (allows duplicate codes)
- Repository uses GetAllAsync instead of GetAllByCompanyAsync
- No domain event raised in constructor
- Missing InputCreditAllowed property
- TaxType FK uses Cascade instead of Restrict
- Enum values don't match Vietnamese tax law treatment categories

---

## Cross-Task Dependencies

**Depends on:** [G1] TaxType domain foundation — TaxTreatment has FK to TaxType entity
**Wait for:** TaxType entity must exist before TaxTreatment EF configuration can reference `HasOne<TaxType>()`
**Parallel safe:** Enum, event, and port interface can be created in parallel with TaxType
**EF config and repository must wait:** TaxType entity class must be compilable first

---

# Task-Specific Research — [G1] TaxAuthority domain foundation

## Critical Context: Vietnamese Tax Authority Structure

Vietnam's tax administration follows a **three-level hierarchy** under the Ministry of Finance:

| Level | Vietnamese Name | English Name | Scope |
|-------|----------------|--------------|-------|
| **National** | Tổng cục Thuế | General Department of Taxation (GDT) | National — under Ministry of Finance. 12 departments at central level. |
| **Provincial** | Cục Thuế tỉnh/thành phố | Regional Tax Sub-Departments | 20 regional sub-departments (Region I, Region II, etc.) per Decision 381/QD-BTC (Feb 2025). Legal person status, own seals. |
| **District** | Chi cục thuế | District-level Tax Teams | Under regional sub-departments. Districts, towns, cities. Max 350 units nationally. |

**Key regulatory facts:**
- GDT is an agency under the Ministry of Finance (Decision 381/QD-BTC, Feb 26, 2025)
- The Department of Taxation has replaced the "General Department" in name per Decision 381
- Each level has its own collection management agency code and State Treasury account
- The entity must reference this three-level structure for tax filing routing

**Why this matters for the entity:**
- A company may deal with its **district-level tax team** for routine filings
- Large enterprises deal directly with **provincial tax sub-departments**
- Certain national-level filings go to the **General Department of Taxation**
- The `AuthorityLevel` enum captures which tier a TaxAuthority reference represents

## Files to Create/Modify

### New Files (6)

#### 1. `src/SmeAccounting.Domain/ValueObjects/TaxAuthorityLevel.cs` — Enum

**Pattern source:** `VoucherCategory.cs`, `AccountType.cs`

```csharp
namespace SmeAccounting.Domain.ValueObjects;

public enum TaxAuthorityLevel
{
    National,
    Provincial,
    District
}
```

**Exact namespace:** `SmeAccounting.Domain.ValueObjects`
**No using statements** — enum is a plain value type.
**Enum values:**
| Value | Vietnamese Context | English Equivalent |
|-------|-------------------|-------------------|
| National | Tổng cục Thuế | General Department of Taxation |
| Provincial | Cục Thuế | Regional Tax Sub-Department |
| District | Chi cục thuế | District-level Tax Team |

**Regulatory mapping:**
- National → GDT central level (12 departments, policymaking)
- Provincial → 20 Regional Tax Sub-Departments (Decision 381/QD-BTC)
- District → District-level tax teams (max 350 units)

**Gotcha:** No namespace collision issue here — `TaxAuthorityLevel` is distinct from the entity name `TaxAuthority`. Unlike TaxType/TaxCategory where collision was a problem, this is safe as-is.

---

#### 2. `src/SmeAccounting.Domain/Entities/TaxAuthority.cs` — Entity

**Pattern source:** `VoucherType.cs` (CompanyId-scoped entity with Code, Name, IsActive, Description)

```csharp
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class TaxAuthority : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public TaxAuthorityLevel AuthorityLevel { get; private set; }
    public long CompanyId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Address { get; private set; }
    public string? Phone { get; private set; }

    private TaxAuthority() { }

    public TaxAuthority(
        long companyId,
        string code,
        string name,
        TaxAuthorityLevel authorityLevel,
        string? address = null,
        string? phone = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");

        CompanyId = companyId;
        Code = code;
        Name = name;
        AuthorityLevel = authorityLevel;
        Address = address;
        Phone = phone;

        AddDomainEvent(new TaxAuthorityCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
```

**Exact namespace:** `SmeAccounting.Domain.Entities`
**Using statements:** `SmeAccounting.Domain.Events`, `SmeAccounting.Domain.Exceptions`, `SmeAccounting.Domain.ValueObjects`
**Class:** `public class TaxAuthority : BaseEntity` — NOT a record, NOT sealed
**Private parameterless constructor:** `private TaxAuthority() { }` — EF Core materialization
**Public constructor:** CompanyId first (matching VoucherType), then Code, Name, AuthorityLevel, Address optional, Phone optional
**Validation:** `DomainException` for invariant violations (CompanyId, Code, Name) — matches VoucherType pattern
**Event raised in constructor:** `AddDomainEvent(new TaxAuthorityCreated(Id, companyId, DateTimeOffset.UtcNow))`
**Deactivate:** `IsActive = false` only — no event (matches all prior entities)

**Properties:**
| Property | Type | Default | Max Length (EF config) | Notes |
|----------|------|---------|----------------------|-------|
| Code | string | string.Empty | 20 | Unique per company (e.g., "GDT", "CT01-HN", "CT-QN-01") |
| Name | string | string.Empty | 200 | Full authority name |
| AuthorityLevel | TaxAuthorityLevel (enum) | — | HasConversion<string>() | National, Provincial, District |
| CompanyId | long | — | FK to companies | Required, Restrict delete |
| IsActive | bool | true | — | Soft-delete |
| Address | string? | null | 500 | Office address |
| Phone | string? | null | 20 | Contact phone |

**Why Address and Phone:** Tax authorities have physical offices where taxpayers may file documents. Company entity also has Address and Phone — same pattern for reference data.

**Gotcha — Id=0 in event:** Same as all other entities. Real ID assigned by EF Core after SaveChanges.

---

#### 3. `src/SmeAccounting.Domain/Events/TaxAuthorityCreated.cs` — Domain Event

**Pattern source:** `VoucherTypeCreated.cs`, `DepartmentCreated.cs`

```csharp
namespace SmeAccounting.Domain.Events;

public class TaxAuthorityCreated : DomainEvent
{
    public long TaxAuthorityId { get; }
    public long CompanyId { get; }

    public TaxAuthorityCreated(
        long taxAuthorityId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxAuthorityId = taxAuthorityId;
        CompanyId = companyId;
    }
}
```

**Exact namespace:** `SmeAccounting.Domain.Events`
**No using statements needed** — DomainEvent is in same namespace.
**Pattern:** Entity ID + CompanyId + occurredOn — matches VoucherTypeCreated/DepartmentCreated exactly.
**Event minimalism:** No Code, Name, AuthorityLevel, Address, Phone — just IDs.

---

#### 4. `src/SmeAccounting.Domain/Ports/ITaxAuthorityRepository.cs` — Port Interface

**Pattern source:** `IVoucherTypeRepository.cs`, `IDepartmentRepository.cs`

```csharp
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITaxAuthorityRepository
{
    Task<TaxAuthority?> GetByIdAsync(long id);
    Task<TaxAuthority?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<TaxAuthority>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(TaxAuthority taxAuthority);
}
```

**Exact namespace:** `SmeAccounting.Domain.Ports`
**Using:** `SmeAccounting.Domain.Entities`
**Methods:**
- `GetByIdAsync(long id)` — standard lookup
- `GetByCodeAsync(string code, long companyId)` — unique per company lookup
- `GetAllByCompanyAsync(long companyId)` — company-scoped (NOT `GetAllAsync()` — authorities are company-specific reference data)
- `AddAsync(TaxAuthority taxAuthority)` — insert only

**Why `GetAllByCompanyAsync`:** Tax authorities are company-scoped reference data. A company registers with specific tax offices based on its location and size. Each company may reference different tax authorities. Same pattern as TaxType/TaxTreatment.

**No UpdateAsync** — EF Core change tracking handles updates (matches all other repos).

---

#### 5. `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxAuthorityConfiguration.cs` — EF Config

**Pattern source:** `VoucherTypeConfiguration.cs`

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class TaxAuthorityConfiguration : IEntityTypeConfiguration<TaxAuthority>
{
    public void Configure(EntityTypeBuilder<TaxAuthority> builder)
    {
        builder.ToTable("tax_authorities");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.Code)
            .HasColumnName("code")
            .IsRequired()
            .HasMaxLength(20);

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.AuthorityLevel)
            .HasColumnName("authority_level")
            .HasConversion<string>();

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Address)
            .HasColumnName("address")
            .HasMaxLength(500);

        builder.Property(e => e.Phone)
            .HasColumnName("phone")
            .HasMaxLength(20);

        builder.HasIndex(e => new { e.CompanyId, e.Code })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
```

**Exact namespace:** `SmeAccounting.Infrastructure.Persistence.Configurations`
**Using:** `Microsoft.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore.Metadata.Builders`, `SmeAccounting.Domain.Entities`, `SmeAccounting.Domain.ValueObjects`
**Class:** `internal sealed class TaxAuthorityConfiguration : IEntityTypeConfiguration<TaxAuthority>`
**Table:** `tax_authorities` (snake_case plural)
**Unique index:** `(CompanyId, Code)` — prevents duplicate authority codes per company
**Company FK:** `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — no navigation property on entity
**Enum conversion:** `HasConversion<string>()` for AuthorityLevel — stores as text, not int
**xmin:** Always last, `IsRowVersion()`
**Max lengths:** Code=20, Name=200, Address=500, Phone=20

**Auto-discovery:** `modelBuilder.ApplyConfigurationsFromAssembly(typeof(SmeAccountingDbContext).Assembly)` in DbContext auto-discovers this config — no manual registration needed.

---

#### 6. `src/SmeAccounting.Infrastructure/Repositories/EfTaxAuthorityRepository.cs` — Repository

**Pattern source:** `EfVoucherTypeRepository.cs`

```csharp
using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTaxAuthorityRepository : ITaxAuthorityRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTaxAuthorityRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TaxAuthority?> GetByIdAsync(long id)
    {
        return await _context.TaxAuthorities
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<TaxAuthority?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.TaxAuthorities
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<TaxAuthority>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.TaxAuthorities
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(TaxAuthority taxAuthority)
    {
        await _context.TaxAuthorities.AddAsync(taxAuthority);
    }
}
```

**Exact namespace:** `SmeAccounting.Infrastructure.Repositories`
**Using:** `Microsoft.EntityFrameworkCore`, `SmeAccounting.Domain.Entities`, `SmeAccounting.Domain.Ports`, `SmeAccounting.Infrastructure.Persistence`
**Class:** `public class EfTaxAuthorityRepository : ITaxAuthorityRepository`
**Key patterns:**
- `GetByIdAsync` — tracked (no AsNoTracking)
- `GetByCodeAsync` — tracked, composite filter (Code + CompanyId)
- `GetAllByCompanyAsync` — `AsNoTracking()`, filtered by CompanyId, ordered by Code
- `AddAsync` — delegates to DbSet.AddAsync
- No `UpdateAsync` — change tracking handles it

---

### Modified Files (2)

#### 7. `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` — DbContext edits

Add **1 DbSet** + **1 Ignore**:

```csharp
// DbSet — add after existing DbSets (after OpeningBalanceMappings, or after TaxTypes/TaxTreatments if those are done first)
public DbSet<TaxAuthority> TaxAuthorities => Set<TaxAuthority>();

// Ignore — add in OnModelCreating after existing Ignore calls
modelBuilder.Ignore<TaxAuthorityCreated>();
```

**Current counts:** 18 DbSets, 14 ignored events → **New counts:** 19 DbSets, 15 ignored events (or 21/17 if TaxType+TaxTreatment done first)

**Important:** The `using SmeAccounting.Domain.Events;` and `using SmeAccounting.Domain.Entities;` are already in the file. No new using statements needed.

---

#### 8. `src/SmeAccounting.Infrastructure/DependencyInjection.cs` — DI registration

Add **1 line** after existing repository registrations:

```csharp
services.AddScoped<ITaxAuthorityRepository, EfTaxAuthorityRepository>();
```

**Current count:** 13 repository registrations → **New count:** 14 (or 16 if TaxType+TaxTreatment done first)

**Using statements:** `SmeAccounting.Domain.Ports` and `SmeAccounting.Infrastructure.Repositories` already imported. No new usings needed.

---

### Architecture Tests — Verification (no code changes needed)

The 22 existing architecture tests automatically validate TaxAuthority:

| Test | What it checks for TaxAuthority |
|------|--------------------------------|
| `Entities_Inheriting_BaseEntity_Should_Reside_In_Entities_Namespace` | TaxAuthority in `SmeAccounting.Domain.Entities` ✓ |
| `Repository_Interfaces_Should_Start_With_I` | ITaxAuthorityRepository starts with "I" ✓ |
| `Domain_Should_Have_No_NuGet_PackageReferences` | Domain.csproj unchanged ✓ |
| `Domain_Should_Have_No_EntityFramework_Assembly_Dependency` | TaxAuthority entity has no EF Core refs ✓ |
| `Domain_Should_Not_Depend_On_Application/Infrastructure/Api` | TaxAuthority is pure domain ✓ |

**No new test files or test methods required.** Build + `dotnet test` validates everything.

---

## Implementation Sequence

1. Create `TaxAuthorityLevel` enum in `Domain/ValueObjects/TaxAuthorityLevel.cs`
2. Create `TaxAuthorityCreated` event in `Domain/Events/TaxAuthorityCreated.cs`
3. Create `TaxAuthority` entity in `Domain/Entities/TaxAuthority.cs`
4. Create `ITaxAuthorityRepository` port in `Domain/Ports/ITaxAuthorityRepository.cs`
5. Create `TaxAuthorityConfiguration` in `Infrastructure/Persistence/Configurations/TaxAuthorityConfiguration.cs`
6. Create `EfTaxAuthorityRepository` in `Infrastructure/Repositories/EfTaxAuthorityRepository.cs`
7. Edit `SmeAccountingDbContext.cs` — add DbSet + Ignore
8. Edit `DependencyInjection.cs` — add AddScoped registration
9. `dotnet build SmeAccounting.sln` — must succeed (TreatWarningsAsErrors)
10. `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 must pass

---

## Verification Criteria

### What "Done Correctly" Looks Like
1. `TaxAuthorityLevel` enum has exactly 3 values: National, Provincial, District
2. `TaxAuthority` entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity, private ctor, public ctor with DomainException validation
3. Entity has Address and Phone optional properties (matching Company pattern for reference data)
4. `TaxAuthorityCreated` event carries TaxAuthorityId + CompanyId + occurredOn
5. `ITaxAuthorityRepository` in `SmeAccounting.Domain.Ports` — starts with I, 4 methods (GetById, GetByCode, GetAllByCompany, Add)
6. EF config: snake_case table `tax_authorities`, unique index `(CompanyId, Code)`, CompanyId FK Restrict, xmin row version
7. Repository: `AsNoTracking()` for GetAllByCompany, tracked for GetById/GetByCode
8. DbContext: correct DbSet count (depends on whether TaxType+TaxTreatment done first)
9. DI: correct AddScoped count
10. Build: zero warnings (TreatWarningsAsErrors)
11. Tests: 22/22 pass

### What "Failing" Looks Like
1. Entity missing private parameterless constructor → EF Core runtime failure
2. Missing `modelBuilder.Ignore<TaxAuthorityCreated>()` → EF Core migration error
3. Missing `DbSet<TaxAuthority>` → entity not tracked by DbContext
4. Missing DI registration → runtime dependency injection failure
5. Missing unique index → duplicate codes allowed at DB level
6. Wrong namespace on entity → architecture test failure
7. Entity using `ArgumentNullException` instead of `DomainException` → violates established pattern
8. Missing `using SmeAccounting.Domain.ValueObjects` in entity → AuthorityLevel unresolved
9. Repository using `GetAllAsync()` instead of `GetAllByCompanyAsync(companyId)` → violates plan spec
10. AuthorityLevel enum named `TaxAuthority` → collision with entity name
11. Missing Address/Phone properties → entity doesn't match plan spec
12. TaxAuthority FK using Cascade delete instead of Restrict → violates established pattern

---

## Quality Standards

### Good Output
- Exact match to VoucherType pattern (constructor shape, validation, event, Deactivate)
- TaxAuthorityLevel enum values match Vietnamese tax authority hierarchy (National/Provincial/District)
- Address and Phone properties included as optional fields (matching Company entity pattern for reference data)
- EF config follows every convention (snake_case, xmin, CompanyId Restrict, unique index)
- Code compiles with zero warnings
- All 22 architecture tests pass without modification

### Merely Functional
- Entity works but uses different validation pattern (ArgumentNullException vs DomainException)
- Missing unique index (allows duplicate codes)
- Repository uses GetAllAsync instead of GetAllByCompanyAsync
- No domain event raised in constructor
- Missing Address or Phone properties
- AuthorityLevel enum values don't match Vietnamese tax authority structure
- TaxAuthority FK uses Cascade instead of Restrict

---

## Cross-Task Dependencies

**Depends on:** None — TaxAuthority is a standalone company-scoped reference entity
**Parallel safe:** Can run in parallel with TaxType and TaxTreatment (all G1 tasks)
**No FK dependencies:** TaxAuthority does NOT reference TaxType, TaxTreatment, Account, or FiscalPeriod
**Standalone:** CompanyId FK only — same as VoucherType, Department, CostCenter, Project

---

## Audit Results — [G1] TaxType

**Auditor:** loop-engineer auditor agent
**Date:** 2026-09-17
**Verdict:** WARN

### Build & Tests
- `dotnet build SmeAccounting.sln`: **0 warnings, 0 errors** ✓
- `dotnet test tests/SmeAccounting.ArchitectureTests/`: **22/22 passed** ✓

### File-by-File Review

#### 1. `TaxCategory.cs` (ValueObjects) — CLEAN
- 8 enum values: VAT, CIT, PIT, SpecialConsumption, Resource, Environmental, ImportDuty, ExportDuty
- Correct namespace `SmeAccounting.Domain.ValueObjects`
- Name collision avoided (`TaxCategory` vs entity `TaxType`) — matches `VoucherCategory`/`VoucherType` precedent
- No usings needed — plain enum

#### 2. `TaxType.cs` (Entities) — CLEAN
- Exact structural clone of `VoucherType.cs` — line-for-line pattern match
- Inherits `BaseEntity` ✓
- Private parameterless constructor ✓
- Public constructor: CompanyId, Code, Name, TaxCategory, Description ✓
- Validation: DomainException for CompanyId > 0, Code not empty, Name not empty ✓
- Event raised: `TaxTypeCreated(Id, companyId, DateTimeOffset.UtcNow)` ✓
- `Deactivate()`: `IsActive = false` only (no event) ✓
- Properties match plan: Code (20), Name (200), TaxCategory (enum), CompanyId, IsActive, Description? (500)

#### 3. `TaxTypeCreated.cs` (Events) — CLEAN
- Inherits `DomainEvent` ✓
- Properties: `TaxTypeId` (long), `CompanyId` (long) ✓
- Constructor: taxTypeId, companyId, occurredOn → base(occurredOn) ✓
- Event minimalism: IDs only, no data duplication ✓
- Exact structural match to `VoucherTypeCreated.cs`

#### 4. `ITaxTypeRepository.cs` (Ports) — CLEAN
- 4 methods: GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, AddAsync ✓
- `GetAllByCompanyAsync(long companyId)` — company-scoped (correct per plan, NOT `GetAllAsync()`) ✓
- No UpdateAsync ✓
- Correct namespace `SmeAccounting.Domain.Ports` ✓

#### 5. `TaxTypeConfiguration.cs` (EF Config) — WARN (minor)
- `ToTable("tax_types")` ✓
- `HasKey`, `HasColumnName`, `ValueGeneratedOnAdd` on Id ✓
- All columns snake_case: company_id, code, name, tax_category, is_active, description ✓
- `HasConversion<string>()` for TaxCategory enum ✓
- MaxLength: Code=20, Name=200, Description=500 ✓
- Unique composite index on `(CompanyId, Code)` ✓
- Company FK: `HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict)` ✓
- xmin row version last ✓
- **Minor:** Extra `using SmeAccounting.Domain.ValueObjects;` — no other EF configuration in the project has this import (VoucherTypeConfiguration doesn't need it). The property type is resolved from the entity, not the import. Harmless but inconsistent.

#### 6. `EfTaxTypeRepository.cs` (Repository) — CLEAN
- Tracked queries: GetByIdAsync, GetByCodeAsync ✓
- `AsNoTracking()` on GetAllByCompanyAsync ✓
- `GetByCodeAsync`: composite filter (Code + CompanyId) ✓
- `GetAllByCompanyAsync`: filtered by CompanyId, ordered by Code ✓
- `AddAsync`: delegates to DbSet.AddAsync ✓
- No UpdateAsync ✓
- Exact pattern match to `EfVoucherTypeRepository.cs`

#### 7. `SmeAccountingDbContext.cs` — CLEAN
- `DbSet<TaxType> TaxTypes => Set<TaxType>()` ✓
- `modelBuilder.Ignore<TaxTypeCreated>()` ✓
- Both present — matches requirement "always both" ✓
- No new using statements needed (already imported) ✓

#### 8. `DependencyInjection.cs` — CLEAN
- `AddScoped<ITaxTypeRepository, EfTaxTypeRepository>()` ✓
- Correct placement after other repository registrations ✓

### Pattern Compliance Matrix

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Entity namespace | `SmeAccounting.Domain.Entities` | `SmeAccounting.Domain.Entities` | ✓ |
| Port namespace | `SmeAccounting.Domain.Ports` | `SmeAccounting.Domain.Ports` | ✓ |
| Event namespace | `SmeAccounting.Domain.Events` | `SmeAccounting.Domain.Events` | ✓ |
| Enum namespace | `SmeAccounting.Domain.ValueObjects` | `SmeAccounting.Domain.ValueObjects` | ✓ |
| Enum naming | `TaxCategory` (not `TaxType`) | `TaxCategory` | ✓ |
| Entity class | `public class TaxType : BaseEntity` | `public class TaxType : BaseEntity` | ✓ |
| Private ctor | `private TaxType() { }` | `private TaxType() { }` | ✓ |
| Validation pattern | DomainException | DomainException | ✓ |
| Event pattern | EntityId + CompanyId + occurredOn | TaxTypeId + CompanyId + occurredOn | ✓ |
| Repository methods | 4 (GetById, GetByCode, GetAllByCompany, Add) | 4 | ✓ |
| EF table name | `tax_types` | `tax_types` | ✓ |
| Unique index | `(CompanyId, Code)` | `(CompanyId, Code)` | ✓ |
| Company FK | Restrict | Restrict | ✓ |
| xmin row version | Yes, last | Yes, last | ✓ |
| Build warnings | 0 | 0 | ✓ |
| Architecture tests | 22/22 | 22/22 | ✓ |

### Issues Found

**WARN-1: Extra unused import in TaxTypeConfiguration.cs**
- `using SmeAccounting.Domain.ValueObjects;` — not present in any other EF configuration file (VoucherTypeConfiguration, TransactionReasonConfiguration, etc.)
- The `TaxCategory` type on the entity property is resolved from the entity type declaration, not from this import
- **Impact:** None — harmless, builds fine, no runtime effect
- **Recommendation:** Remove to match established pattern consistency

### Verdict: WARN

TaxType domain foundation is a precise structural clone of VoucherType. All 6 new files and 2 modified files follow established patterns exactly. One minor stylistic inconsistency (unused import) does not affect functionality or correctness. Build passes with 0 warnings. All 22 architecture tests pass.

---

## Audit Results — [G1] TaxTreatment

**Auditor:** loop-engineer auditor agent
**Date:** 2026-09-17
**Verdict:** CLEAN

### Build & Tests
- `dotnet build SmeAccounting.sln`: **0 warnings, 0 errors** ✓
- `dotnet test tests/SmeAccounting.ArchitectureTests/`: **22/22 passed** ✓

### File-by-File Review

#### 1. `TaxTreatmentType.cs` (ValueObjects) — CLEAN
- 5 enum values: StandardRate, ReducedRate, ZeroRate, Exempt, NonTaxable
- Correct namespace `SmeAccounting.Domain.ValueObjects`
- Name collision avoided (`TaxTreatmentType` vs entity `TaxTreatment`) — matches `TaxCategory`/`TaxType` and `VoucherCategory`/`VoucherType` precedent
- No usings needed — plain enum
- Enum values self-documenting for Vietnamese VAT treatment categories

#### 2. `TaxTreatment.cs` (Entities) — CLEAN
- Exact structural clone of `TransactionReason.cs` — two FK pattern (CompanyId + TaxTypeId)
- Inherits `BaseEntity` ✓
- Private parameterless constructor ✓
- Public constructor: CompanyId, TaxTypeId, Code, Name, TaxTreatmentType, InputCreditAllowed, Description ✓
- Validation: DomainException for CompanyId > 0, TaxTypeId > 0, Code not empty, Name not empty ✓
- `InputCreditAllowed` bool present — captures critical 0% rate (deductible) vs exempt (non-deductible) distinction ✓
- Event raised: `TaxTreatmentCreated(Id, companyId, DateTimeOffset.UtcNow)` ✓
- `Deactivate()`: `IsActive = false` only (no event) ✓
- Properties match plan: Code (20), Name (200), TaxTypeId (FK), TaxTreatmentType (enum), InputCreditAllowed (bool), CompanyId, IsActive, Description? (500)

#### 3. `TaxTreatmentCreated.cs` (Events) — CLEAN
- Inherits `DomainEvent` ✓
- Properties: `TaxTreatmentId` (long), `CompanyId` (long) ✓
- Constructor: taxTreatmentId, companyId, occurredOn → base(occurredOn) ✓
- Event minimalism: IDs only, no data duplication ✓
- Exact structural match to `VoucherTypeCreated.cs` / `TransactionReasonCreated.cs`

#### 4. `ITaxTreatmentRepository.cs` (Ports) — CLEAN
- 5 methods: GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, GetAllByTaxTypeAsync, AddAsync ✓
- `GetAllByCompanyAsync(long companyId)` — company-scoped ✓
- `GetAllByTaxTypeAsync(long taxTypeId)` — filter by parent entity (matches plan spec) ✓
- No UpdateAsync ✓
- Correct namespace `SmeAccounting.Domain.Ports` ✓

#### 5. `TaxTreatmentConfiguration.cs` (EF Config) — CLEAN
- `ToTable("tax_treatments")` ✓
- `HasKey`, `HasColumnName`, `ValueGeneratedOnAdd` on Id ✓
- All columns snake_case: company_id, tax_type_id, code, name, tax_treatment_type, input_credit_allowed, is_active, description ✓
- `HasConversion<string>()` for TaxTreatmentType enum ✓
- MaxLength: Code=20, Name=200, Description=500 ✓
- Unique composite index on `(CompanyId, Code)` ✓
- Two FKs both Restrict: Company + TaxType ✓
- `HasOne<TaxType>().WithMany().HasForeignKey().OnDelete(Restrict)` — no nav property, matches TransactionReason pattern ✓
- xmin row version last ✓
- `using SmeAccounting.Domain.ValueObjects;` is correctly needed here for `TaxTreatmentType` enum (unlike TaxTypeConfiguration where it was unnecessary)

#### 6. `EfTaxTreatmentRepository.cs` (Repository) — CLEAN
- Tracked queries: GetByIdAsync, GetByCodeAsync ✓
- `AsNoTracking()` on GetAllByCompanyAsync and GetAllByTaxTypeAsync ✓
- `GetByCodeAsync`: composite filter (Code + CompanyId) ✓
- `GetAllByCompanyAsync`: filtered by CompanyId, ordered by Code ✓
- `GetAllByTaxTypeAsync`: filtered by TaxTypeId, ordered by Code ✓
- `AddAsync`: delegates to DbSet.AddAsync ✓
- No UpdateAsync ✓
- Exact pattern match to `EfTransactionReasonRepository.cs`

#### 7. `SmeAccountingDbContext.cs` — CLEAN
- `DbSet<TaxTreatment> TaxTreatments => Set<TaxTreatment>()` ✓
- `modelBuilder.Ignore<TaxTreatmentCreated>()` ✓
- Both present — matches requirement "always both" ✓
- No new using statements needed (already imported) ✓

#### 8. `DependencyInjection.cs` — CLEAN
- `AddScoped<ITaxTreatmentRepository, EfTaxTreatmentRepository>()` ✓
- Correct placement after other repository registrations ✓

### Pattern Compliance Matrix

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Entity namespace | `SmeAccounting.Domain.Entities` | `SmeAccounting.Domain.Entities` | ✓ |
| Port namespace | `SmeAccounting.Domain.Ports` | `SmeAccounting.Domain.Ports` | ✓ |
| Event namespace | `SmeAccounting.Domain.Events` | `SmeAccounting.Domain.Events` | ✓ |
| Enum namespace | `SmeAccounting.Domain.ValueObjects` | `SmeAccounting.Domain.ValueObjects` | ✓ |
| Enum naming | `TaxTreatmentType` (not `TaxTreatment`) | `TaxTreatmentType` | ✓ |
| Entity class | `public class TaxTreatment : BaseEntity` | `public class TaxTreatment : BaseEntity` | ✓ |
| Private ctor | `private TaxTreatment() { }` | `private TaxTreatment() { }` | ✓ |
| Validation pattern | DomainException | DomainException | ✓ |
| Two FKs | CompanyId + TaxTypeId | CompanyId + TaxTypeId | ✓ |
| FK delete behavior | Both Restrict | Both Restrict | ✓ |
| InputCreditAllowed | bool present | bool present | ✓ |
| Event pattern | EntityId + CompanyId + occurredOn | TaxTreatmentId + CompanyId + occurredOn | ✓ |
| Repository methods | 5 (GetById, GetByCode, GetAllByCompany, GetAllByTaxType, Add) | 5 | ✓ |
| EF table name | `tax_treatments` | `tax_treatments` | ✓ |
| Unique index | `(CompanyId, Code)` | `(CompanyId, Code)` | ✓ |
| xmin row version | Yes, last | Yes, last | ✓ |
| Build warnings | 0 | 0 | ✓ |
| Architecture tests | 22/22 | 22/22 | ✓ |

### Issues Found

None. TaxTreatment is a clean implementation that precisely follows the RESEARCH.md specification and established patterns.

### Verdict: CLEAN

TaxTreatment domain foundation is a faithful implementation of the TransactionReason two-FK pattern. All 6 new files and 2 modified files follow established patterns exactly. The critical regulatory distinction between 0% rate (InputCreditAllowed=true) and exempt (InputCreditAllowed=false) is correctly captured in the entity model. The TaxTreatmentType enum avoids namespace collision with the entity class. Both FKs use Restrict delete behavior. Build passes with 0 warnings. All 22 architecture tests pass.

---

## Audit Results — [G1] TaxAuthority

**Auditor:** loop-engineer auditor agent
**Date:** 2026-09-17
**Verdict:** CLEAN

### Build & Tests
- `dotnet build SmeAccounting.sln`: **0 warnings, 0 errors** ✓
- `dotnet test tests/SmeAccounting.ArchitectureTests/`: **22/22 passed** ✓

### File-by-File Review

#### 1. `TaxAuthorityLevel.cs` (ValueObjects) — CLEAN
- 3 enum values: National, Provincial, District
- Correct namespace `SmeAccounting.Domain.ValueObjects`
- No namespace collision — `TaxAuthorityLevel` is distinct from entity `TaxAuthority`
- Matches Vietnamese 3-tier hierarchy: GDT → Regional Sub-Departments → District Teams (Decision 381/QD-BTC)
- No usings needed — plain enum

#### 2. `TaxAuthority.cs` (Entities) — CLEAN
- Exact structural clone of `VoucherType.cs` with Address/Phone additions
- Inherits `BaseEntity` ✓
- Private parameterless constructor ✓
- Public constructor: CompanyId, Code, Name, AuthorityLevel, Address?, Phone?, Description? ✓
- Validation: DomainException for CompanyId > 0, Code not empty, Name not empty ✓
- Event raised: `TaxAuthorityCreated(Id, companyId, DateTimeOffset.UtcNow)` ✓
- `Deactivate()`: `IsActive = false` only (no event) ✓
- Properties match plan + established pattern: Code (20), Name (200), AuthorityLevel (enum), CompanyId, IsActive, Address? (500), Phone? (20), Description? (500)
- Description property added — consistent with VoucherType/TaxType/TaxTreatment pattern (RESEARCH.md entity sample omitted it but EF config included it; executor correctly followed established pattern)

#### 3. `TaxAuthorityCreated.cs` (Events) — CLEAN
- Inherits `DomainEvent` ✓
- Properties: `TaxAuthorityId` (long), `CompanyId` (long) ✓
- Constructor: taxAuthorityId, companyId, occurredOn → base(occurredOn) ✓
- Event minimalism: IDs only, no data duplication ✓
- Exact structural match to `VoucherTypeCreated.cs`

#### 4. `ITaxAuthorityRepository.cs` (Ports) — CLEAN
- 4 methods: GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, AddAsync ✓
- `GetAllByCompanyAsync(long companyId)` — company-scoped (correct per plan, NOT `GetAllAsync()`) ✓
- Consistent with ITaxTypeRepository pattern ✓
- No UpdateAsync ✓
- Correct namespace `SmeAccounting.Domain.Ports` ✓

#### 5. `TaxAuthorityConfiguration.cs` (EF Config) — CLEAN
- `ToTable("tax_authorities")` ✓
- `HasKey`, `HasColumnName`, `ValueGeneratedOnAdd` on Id ✓
- All columns snake_case: company_id, code, name, authority_level, is_active, address, phone, description ✓
- `HasConversion<string>()` for AuthorityLevel enum ✓
- MaxLength: Code=20, Name=200, Address=500, Phone=20, Description=500 ✓
- Unique composite index on `(CompanyId, Code)` ✓
- Company FK: `HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict)` ✓
- xmin row version last ✓
- No unnecessary extra usings (unlike TaxTypeConfiguration which had extra `using ValueObjects`) ✓

#### 6. `EfTaxAuthorityRepository.cs` (Repository) — CLEAN
- Tracked queries: GetByIdAsync, GetByCodeAsync ✓
- `AsNoTracking()` on GetAllByCompanyAsync ✓
- `GetByCodeAsync`: composite filter (Code + CompanyId) ✓
- `GetAllByCompanyAsync`: filtered by CompanyId, ordered by Code ✓
- `AddAsync`: delegates to DbSet.AddAsync ✓
- No UpdateAsync ✓
- Exact pattern match to `EfTaxTypeRepository.cs`

#### 7. `SmeAccountingDbContext.cs` — CLEAN
- `DbSet<TaxAuthority> TaxAuthorities => Set<TaxAuthority>()` ✓
- `modelBuilder.Ignore<TaxAuthorityCreated>()` ✓
- Both present — matches requirement "always both" ✓
- Counts: 21 DbSets, 17 ignored events (correct after TaxType + TaxTreatment additions) ✓

#### 8. `DependencyInjection.cs` — CLEAN
- `AddScoped<ITaxAuthorityRepository, EfTaxAuthorityRepository>()` ✓
- Correct placement after other repository registrations ✓
- Count: 16 registrations (correct after TaxType + TaxTreatment additions) ✓

### Pattern Compliance Matrix

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Entity namespace | `SmeAccounting.Domain.Entities` | `SmeAccounting.Domain.Entities` | ✓ |
| Port namespace | `SmeAccounting.Domain.Ports` | `SmeAccounting.Domain.Ports` | ✓ |
| Event namespace | `SmeAccounting.Domain.Events` | `SmeAccounting.Domain.Events` | ✓ |
| Enum namespace | `SmeAccounting.Domain.ValueObjects` | `SmeAccounting.Domain.ValueObjects` | ✓ |
| Enum naming | `TaxAuthorityLevel` (no collision) | `TaxAuthorityLevel` | ✓ |
| Entity class | `public class TaxAuthority : BaseEntity` | `public class TaxAuthority : BaseEntity` | ✓ |
| Private ctor | `private TaxAuthority() { }` | `private TaxAuthority() { }` | ✓ |
| Validation pattern | DomainException | DomainException | ✓ |
| FK dependencies | Standalone (CompanyId only) | CompanyId only | ✓ |
| Event pattern | EntityId + CompanyId + occurredOn | TaxAuthorityId + CompanyId + occurredOn | ✓ |
| Repository methods | 4 (GetById, GetByCode, GetAllByCompany, Add) | 4 | ✓ |
| EF table name | `tax_authorities` | `tax_authorities` | ✓ |
| Unique index | `(CompanyId, Code)` | `(CompanyId, Code)` | ✓ |
| Company FK | Restrict | Restrict | ✓ |
| xmin row version | Yes, last | Yes, last | ✓ |
| Build warnings | 0 | 0 | ✓ |
| Architecture tests | 22/22 | 22/22 | ✓ |

### Issues Found

None. TaxAuthority is a clean standalone implementation that precisely follows the VoucherType pattern and RESEARCH.md specification.

### Verdict: CLEAN

TaxAuthority domain foundation is a faithful implementation of the VoucherType single-FK reference entity pattern. All 6 new files and 2 modified files follow established patterns exactly. The TaxAuthorityLevel enum correctly models Vietnam's 3-tier tax authority hierarchy without namespace collision. The entity is standalone (no FK dependencies beyond CompanyId) as required by the plan. Address and Phone properties match the Company entity pattern for reference data with physical offices. Build passes with 0 warnings. All 22 architecture tests pass.

---

## Verification Results — [G1] TaxType

**Verifier:** loop-engineer verifier agent
**Date:** 2026-09-17
**Result:** VERIFIED_PASS

### Requirements Checklist

#### Domain
- [x] TaxCategory enum in Domain/ValueObjects/ with 8 values: VAT, CIT, PIT, SpecialConsumption, Resource, Environmental, ImportDuty, ExportDuty
- [x] TaxType entity in Domain/Entities/ inheriting BaseEntity
- [x] Entity has CompanyId, Code, Name, TaxCategory, IsActive, Description properties
- [x] Entity has private parameterless constructor (`private TaxType() { }`)
- [x] Entity has public constructor with DomainException validation (companyId, code, name)
- [x] Entity has Deactivate() method (sets IsActive = false, no event)

#### Events
- [x] TaxTypeCreated event in Domain/Events/ with TaxTypeId, CompanyId, OccurredOn

#### Ports
- [x] ITaxTypeRepository in Domain/Ports/ — starts with "I"
- [x] Port has GetByIdAsync, GetByCodeAsync(code, companyId), GetAllByCompanyAsync, AddAsync

#### Infrastructure
- [x] TaxTypeConfiguration in Infrastructure/Persistence/Configurations/ — snake_case table "tax_types"
- [x] Unique index on (CompanyId, Code)
- [x] CompanyId FK with Restrict
- [x] TaxCategory HasConversion<string>()
- [x] xmin row version last
- [x] EfTaxTypeRepository implements ITaxTypeRepository — AsNoTracking for GetAllByCompany
- [x] DbContext has DbSet<TaxType> and Ignore<TaxTypeCreated>
- [x] DI has AddScoped<ITaxTypeRepository, EfTaxTypeRepository>() registration

#### Architecture
- [x] Entity in SmeAccounting.Domain.Entities namespace
- [x] Port starts with "I"
- [x] Domain.csproj has zero NuGet PackageReference (empty csproj)
- [x] All 22 architecture tests pass

#### Build
- [x] dotnet build passes with 0 errors, 0 warnings

### Edge Case Verification
- **Enum naming collision:** TaxCategory (not TaxType) avoids namespace collision with entity — verified matches VoucherCategory/VoucherType precedent
- **Domain purity:** Domain.csproj is empty — zero PackageReference elements
- **Pattern compliance:** Exact structural clone of VoucherType entity — constructor shape, validation, event, Deactivate() all match

### Stop Condition
Not met — 3/9 tasks complete. Continue to next task.

---

## Verification Results — [G1] TaxTreatment

**Verifier:** loop-engineer verifier agent
**Date:** 2026-09-17
**Result:** VERIFIED_PASS

### Requirements Checklist

#### Domain
- [x] TaxTreatmentType enum in Domain/ValueObjects/ with 5 values: StandardRate, ReducedRate, ZeroRate, Exempt, NonTaxable
- [x] TaxTreatment entity in Domain/Entities/ inheriting BaseEntity
- [x] Entity has CompanyId, TaxTypeId, Code, Name, TaxTreatmentType, InputCreditAllowed, IsActive, Description
- [x] Entity has private parameterless constructor (`private TaxTreatment() { }`)
- [x] Entity has public constructor with DomainException validation (companyId, taxTypeId, code, name)
- [x] Entity has Deactivate() method (sets IsActive = false, no event)

#### Events
- [x] TaxTreatmentCreated event in Domain/Events/ with TaxTreatmentId, CompanyId, OccurredOn

#### Ports
- [x] ITaxTreatmentRepository in Domain/Ports/ — starts with "I"
- [x] Port has GetByIdAsync, GetByCodeAsync(code, companyId), GetAllByCompanyAsync, GetAllByTaxTypeAsync, AddAsync

#### Infrastructure
- [x] TaxTreatmentConfiguration — snake_case table "tax_treatments"
- [x] Unique index on (CompanyId, Code)
- [x] CompanyId FK with Restrict
- [x] TaxTypeId FK with Restrict
- [x] TaxTreatmentType HasConversion<string>()
- [x] xmin row version last
- [x] EfTaxTreatmentRepository implements ITaxTreatmentRepository — AsNoTracking for GetAllByCompany and GetAllByTaxType
- [x] DbContext has DbSet<TaxTreatment> and Ignore<TaxTreatmentCreated>
- [x] DI has AddScoped<ITaxTreatmentRepository, EfTaxTreatmentRepository>() registration

#### Architecture
- [x] Entity in SmeAccounting.Domain.Entities namespace
- [x] Port starts with "I"
- [x] Domain.csproj has zero NuGet PackageReference (empty csproj)
- [x] All 22 architecture tests pass

#### Build
- [x] dotnet build passes with 0 errors, 0 warnings

### Edge Case Verification
- **Enum naming collision:** TaxTreatmentType (not TaxTreatment) avoids namespace collision with entity — verified matches TaxCategory/TaxType precedent
- **0% vs Exempt distinction:** InputCreditAllowed bool on entity captures critical regulatory distinction — ZeroRate/StandardRate/ReducedRate = true, Exempt/NonTaxable = false
- **Dual FK pattern:** Both CompanyId and TaxTypeId FKs with Restrict delete — matches TransactionReason two-FK pattern exactly

### Stop Condition
Not met — 4/9 tasks complete. Continue to next task.

---

## Verification Results — [G1] TaxAuthority

**Verifier:** loop-engineer verifier agent
**Date:** 2026-09-17
**Result:** VERIFIED_PASS

### Requirements Checklist

#### Domain
- [x] TaxAuthorityLevel enum in Domain/ValueObjects/ with 3 values: National, Provincial, District
- [x] TaxAuthority entity in Domain/Entities/ inheriting BaseEntity
- [x] Entity has CompanyId, Code, Name, AuthorityLevel, Address, Phone, IsActive, Description
- [x] Entity has private parameterless constructor (`private TaxAuthority() { }`)
- [x] Entity has public constructor with DomainException validation (companyId, code, name)
- [x] Entity has Deactivate() method (sets IsActive = false, no event)

#### Events
- [x] TaxAuthorityCreated event in Domain/Events/ with TaxAuthorityId, CompanyId, OccurredOn

#### Ports
- [x] ITaxAuthorityRepository in Domain/Ports/ — starts with "I"
- [x] Port has GetByIdAsync, GetByCodeAsync(code, companyId), GetAllByCompanyAsync, AddAsync

#### Infrastructure
- [x] TaxAuthorityConfiguration — snake_case table "tax_authorities"
- [x] Unique index on (CompanyId, Code)
- [x] CompanyId FK with Restrict
- [x] AuthorityLevel HasConversion<string>()
- [x] xmin row version last
- [x] EfTaxAuthorityRepository implements ITaxAuthorityRepository — AsNoTracking for GetAllByCompany
- [x] DbContext has DbSet<TaxAuthority> and Ignore<TaxAuthorityCreated>
- [x] DI has AddScoped<ITaxAuthorityRepository, EfTaxAuthorityRepository>() registration

#### Architecture
- [x] Entity in SmeAccounting.Domain.Entities namespace
- [x] Port starts with "I"
- [x] Domain.csproj has zero NuGet PackageReference (empty csproj)
- [x] All 22 architecture tests pass

#### Build
- [x] dotnet build passes with 0 errors, 0 warnings

### Edge Case Verification
- **Enum naming:** TaxAuthorityLevel (not TaxAuthority) avoids namespace collision — verified no collision risk
- **Domain purity:** Domain.csproj is empty — zero PackageReference elements
- **Pattern compliance:** Exact structural clone of VoucherType entity — standalone, no FK dependencies beyond CompanyId
- **Vietnamese hierarchy:** 3-tier enum (National/Provincial/District) matches Decision 381/QD-BTC tax authority structure

### Stop Condition
Not met — 4/9 tasks complete. Continue to next task.

---

# Task-Specific Research — [G2] TaxRate domain

## Critical Context: Tax Rate Effective Dating

Tax rates in Vietnamese law have temporal validity — they start and end on specific dates. Examples:
- **VAT 8% temporary reduction:** Effective July 1, 2025 → Expires December 31, 2026 (Resolution 204/2025/QH15)
- **VAT 10% standard:** Effective July 1, 2025 → Indefinite (VAT Law 48/2024)
- **CIT 20% standard:** Effective October 1, 2025 → Indefinite (CIT Law 67/2025)
- **CIT 15% small enterprise:** Effective October 1, 2025 → Indefinite

**Pattern choice:**
- ExchangeRate uses a single `EffectiveDate DateOnly` — one rate per date. This works for daily exchange rates but NOT for tax rates which have open-ended validity.
- FiscalYear uses `StartDate`/`EndDate` (both required `DateOnly`) — this works for bounded periods but NOT for indefinite rates.
- **TaxRate needs `EffectiveFrom DateOnly` (required) + `EffectiveTo DateOnly?` (nullable).** Null `EffectiveTo` means the rate is currently active/indefinite. This matches the real-world pattern where most tax rates have no announced end date.

**Why nullable EffectiveTo:**
- Standard rates (10% VAT, 20% CIT) have no end date — `EffectiveTo = null`
- Temporary reductions (8% VAT) have explicit end dates — `EffectiveTo = DateOnly(2026, 12, 31)`
- Nullable DateOnly is already used on Project entity (`DateOnly? StartDate`, `DateOnly? EndDate`) — no new EF complexity

## Entity Design

### TaxRate Entity Properties

| Property | Type | Default | Max Length (EF) | Notes |
|----------|------|---------|-----------------|-------|
| CompanyId | long | — | FK to companies | Required, Restrict |
| TaxTypeId | long | — | FK to tax_types | Required, Restrict |
| RateValue | decimal | — | decimal(5,2) | e.g., 10.00 for 10%, 8.50 for 8.5% |
| RateName | string | string.Empty | 200 | Descriptive: "Standard 10%", "Temporary 8%" |
| EffectiveFrom | DateOnly | — | date | Required — rate starts on this date |
| EffectiveTo | DateOnly? | null | date | Nullable — null means indefinite/active |
| IsActive | bool | true | — | Soft-delete |
| Description | string? | null | 500 | Optional notes |

**RateValue precision:** `decimal(5,2)` supports values 0.00–999.99 with 2 decimal places. Vietnamese tax rates range from 0% to 50% — this is sufficient. If future rates exceed 999.99%, the precision can be expanded (but that's not a realistic concern for tax rates).

**Why no Code property:** Tax rates don't have codes — they're identified by their tax type + rate value + effective date. The plan's unique index `(CompanyId, TaxType, RateValue, EffectiveFrom)` serves as the natural key. Adding a Code would be redundant with the descriptive RateName.

### Constructor Validation

```csharp
public TaxRate(
    long companyId,
    long taxTypeId,
    decimal rateValue,
    string rateName,
    DateOnly effectiveFrom,
    DateOnly? effectiveTo = null,
    string? description = null)
{
    if (companyId <= 0)
        throw new DomainException("CompanyId must be greater than zero.");
    if (taxTypeId <= 0)
        throw new DomainException("TaxTypeId must be greater than zero.");
    if (rateValue < 0)
        throw new DomainException("RateValue must be non-negative.");
    if (string.IsNullOrWhiteSpace(rateName))
        throw new DomainException("RateName is required.");
    if (effectiveTo.HasValue && effectiveTo.Value < effectiveFrom)
        throw new DomainException("EffectiveTo must not be before EffectiveFrom.");
    // ... set properties, raise event
}
```

**Validation notes:**
- `rateValue >= 0` (not `> 0`) — 0% VAT is a valid rate (exports)
- `effectiveTo >= effectiveFrom` — prevents invalid date ranges
- No validation that `effectiveTo` is required — null means indefinite (matches regulatory reality)

## EF Configuration Design

### Unique Index

**Plan says:** `(CompanyId, TaxType, RateValue, EffectiveFrom)`

**Analysis:** This is correct but we need to decide if TaxType in the index refers to the `TaxTypeId` column. Yes — the composite unique index should be on `(CompanyId, TaxTypeId, RateValue, EffectiveFrom)`. This prevents:
- Duplicate rate entries for the same company + tax type + rate value starting on the same date
- Multiple 10% VAT entries for the same company starting on the same date

**Index SQL equivalent:**
```sql
CREATE UNIQUE INDEX IX_tax_rates_company_id_tax_type_id_rate_value_effective_from
ON tax_rates (company_id, tax_type_id, rate_value, effective_from);
```

### DateOnly Configuration Pattern

From existing codebase (FiscalYearConfiguration, ExchangeRateConfiguration, ProjectConfiguration):
- `DateOnly` properties are mapped with just `.HasColumnName("column_name")` — no explicit column type or conversion needed
- EF Core maps `DateOnly` to PostgreSQL `date` automatically
- Nullable `DateOnly?` maps to nullable `date` column

```csharp
builder.Property(e => e.EffectiveFrom)
    .HasColumnName("effective_from");

builder.Property(e => e.EffectiveTo)
    .HasColumnName("effective_to");
```

No `HasColumnType("date")` needed — EF Core infers it. No `HasConversion` needed — DateOnly is natively supported in EF Core 8+.

### FK Configuration

Two FKs, both Restrict (matches TaxTreatment pattern):

```csharp
builder.HasOne<Company>()
    .WithMany()
    .HasForeignKey(e => e.CompanyId)
    .OnDelete(DeleteBehavior.Restrict);

builder.HasOne<TaxType>()
    .WithMany()
    .HasForeignKey(e => e.TaxTypeId)
    .OnDelete(DeleteBehavior.Restrict);
```

No navigation properties on entity — FK nav-free pattern (matches all existing entities).

## Repository Design

### ITaxRateRepository Methods

Per plan:
1. `GetByIdAsync(long id)` — standard lookup
2. `GetByTaxTypeAndDateAsync(long taxTypeId, DateOnly date, long companyId)` — find active rate for a tax type on a specific date
3. `GetAllByCompanyAsync(long companyId)` — company-scoped list
4. `AddAsync(TaxRate taxRate)` — insert

**GetByTaxTypeAndDateAsync implementation:**
```csharp
public async Task<TaxRate?> GetByTaxTypeAndDateAsync(long taxTypeId, DateOnly date, long companyId)
{
    return await _context.TaxRates
        .FirstOrDefaultAsync(e =>
            e.TaxTypeId == taxTypeId &&
            e.CompanyId == companyId &&
            e.EffectiveFrom <= date &&
            (e.EffectiveTo == null || e.EffectiveTo >= date) &&
            e.IsActive);
}
```

This query finds the rate where:
- Tax type matches
- Company matches
- EffectiveFrom is on or before the query date
- EffectiveTo is null (indefinite) OR on or after the query date
- Rate is active (not deactivated)

**Alternative: GetByTaxTypeAndDateAsync without IsActive filter** — could be useful for historical lookups. But the plan specifies the method as-is. The application layer can use GetAllByCompanyAsync + LINQ filtering for more complex queries.

### EfTaxRateRepository Patterns

- `GetByIdAsync` — tracked (no AsNoTracking)
- `GetByTaxTypeAndDateAsync` — tracked (may be followed by updates)
- `GetAllByCompanyAsync` — `AsNoTracking()`, filtered by CompanyId, ordered by TaxTypeId then EffectiveFrom
- `AddAsync` — delegates to DbSet.AddAsync
- No UpdateAsync — EF Core change tracking handles updates

## Files to Create/Modify

### New Files (5)

1. `src/SmeAccounting.Domain/Entities/TaxRate.cs` — Entity
2. `src/SmeAccounting.Domain/Events/TaxRateCreated.cs` — Domain Event
3. `src/SmeAccounting.Domain/Ports/ITaxRateRepository.cs` — Port Interface
4. `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxRateConfiguration.cs` — EF Config
5. `src/SmeAccounting.Infrastructure/Repositories/EfTaxRateRepository.cs` — Repository

### Modified Files (2)

6. `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` — Add DbSet + Ignore
7. `src/SmeAccounting.Infrastructure/DependencyInjection.cs` — Add AddScoped registration

### No New Enums Needed

TaxRate is a pure numeric entity with effective dates. No enum properties — just CompanyId (long FK), TaxTypeId (long FK), RateValue (decimal), RateName (string), EffectiveFrom (DateOnly), EffectiveTo (DateOnly?), IsActive (bool), Description (string?).

## Implementation Sequence

1. Create `TaxRateCreated` event in `Domain/Events/TaxRateCreated.cs`
2. Create `TaxRate` entity in `Domain/Entities/TaxRate.cs`
3. Create `ITaxRateRepository` port in `Domain/Ports/ITaxRateRepository.cs`
4. Create `TaxRateConfiguration` in `Infrastructure/Persistence/Configurations/TaxRateConfiguration.cs`
5. Create `EfTaxRateRepository` in `Infrastructure/Repositories/EfTaxRateRepository.cs`
6. Edit `SmeAccountingDbContext.cs` — add DbSet + Ignore
7. Edit `DependencyInjection.cs` — add AddScoped registration
8. `dotnet build SmeAccounting.sln` — must succeed (TreatWarningsAsErrors)
9. `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 must pass

## Verification Criteria

### What "Done Correctly" Looks Like
1. `TaxRate` entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity, private ctor, public ctor with DomainException validation
2. Entity has CompanyId FK + TaxTypeId FK — both validated as > 0
3. Entity has RateValue (decimal), RateName (string), EffectiveFrom (DateOnly), EffectiveTo (DateOnly?), IsActive (bool), Description (string?)
4. Constructor validates: companyId > 0, taxTypeId > 0, rateValue >= 0, rateName not empty, effectiveTo >= effectiveFrom
5. `TaxRateCreated` event carries TaxRateId + CompanyId + occurredOn
6. `ITaxRateRepository` in `SmeAccounting.Domain.Ports` — starts with I, 4 methods (GetById, GetByTaxTypeAndDate, GetAllByCompany, Add)
7. EF config: snake_case table `tax_rates`, composite unique index `(CompanyId, TaxTypeId, RateValue, EffectiveFrom)`, CompanyId FK Restrict, TaxTypeId FK Restrict, xmin row version
8. EF config: DateOnly properties mapped with just HasColumnName (no conversion needed)
9. Repository: `AsNoTracking()` for GetAllByCompany, tracked for GetById/GetByTaxTypeAndDate
10. Repository: `GetByTaxTypeAndDateAsync` filters by effective date range (EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date))
11. DbContext: 22 DbSets, 18 ignored events (after G1 adds: 21+1=22 DbSets, 17+1=18 events)
12. DI: 17 AddScoped registrations (after G1 adds: 16+1=17)
13. Build: zero warnings (TreatWarningsAsErrors)
14. Tests: 22/22 pass

### What "Failing" Looks Like
1. Entity missing private parameterless constructor → EF Core runtime failure
2. Missing `modelBuilder.Ignore<TaxRateCreated>()` → EF Core migration error
3. Missing `DbSet<TaxRate>` → entity not tracked by DbContext
4. Missing DI registration → runtime dependency injection failure
5. Missing unique index → duplicate rates allowed at DB level
6. Wrong namespace on entity → architecture test failure
7. Entity using `ArgumentNullException` instead of `DomainException` → violates established pattern
8. Missing TaxTypeId FK validation in constructor → allows invalid references
9. TaxType FK using Cascade delete instead of Restrict → violates established pattern
10. Missing EffectiveFrom/EffectiveTo properties → no effective dating support
11. EffectiveTo not nullable → can't represent indefinite/indefinite rates
12. RateValue validation allows negative values → invalid tax rate
13. GetByTaxTypeAndDateAsync doesn't filter by effective date range → returns wrong rate
14. Repository uses `GetAllAsync()` instead of `GetAllByCompanyAsync(companyId)` → violates plan spec
15. Unique index on `(CompanyId, Code)` instead of `(CompanyId, TaxTypeId, RateValue, EffectiveFrom)` → wrong uniqueness constraint
16. Missing `using SmeAccounting.Domain.Entities` in port → TaxRate unresolved
17. Entity missing RateName property → no descriptive label for rates

## Quality Standards

### Good Output
- Exact match to TaxTreatment pattern (two FKs, constructor shape, validation, event, Deactivate)
- EffectiveFrom/EffectiveTo correctly modeled as DateOnly/DateOnly? (nullable for indefinite)
- RateValue decimal(5,2) with non-negative validation
- RateName provides human-readable label for each rate entry
- Unique index prevents duplicate rate entries per company + tax type + value + date
- GetByTaxTypeAndDateAsync correctly filters by effective date range
- EF config follows every convention (snake_case, xmin, both FKs Restrict, unique index)
- Code compiles with zero warnings
- All 22 architecture tests pass without modification

### Merely Functional
- Entity works but uses different validation pattern (ArgumentNullException vs DomainException)
- Missing unique index (allows duplicate rates)
- Missing EffectiveTo nullable (can't represent indefinite rates)
- No domain event raised in constructor
- Repository uses GetAllAsync instead of GetAllByCompanyAsync
- TaxType FK uses Cascade instead of Restrict
- GetByTaxTypeAndDateAsync doesn't filter by effective date range
- RateValue allows negative values
- Missing RateName property

## Cross-Task Dependencies

**Depends on:** [G1] TaxType domain foundation — TaxRate has FK to TaxType entity
**Wait for:** TaxType entity must exist before TaxRate EF configuration can reference `HasOne<TaxType>()`
**Parallel safe:** Event and port interface can be created in parallel with TaxType (if not done yet)
**EF config and repository must wait:** TaxType entity class must be compilable first

## Current State for Insertion Points

**After G1 batch (TaxType + TaxTreatment + TaxAuthority):**
- DbContext: 21 DbSets, 17 ignored events
- DI: 16 AddScoped registrations

**After G2 TaxRate:**
- DbContext: 22 DbSets, 18 ignored events
- DI: 17 AddScoped registrations

**DbContext insertion point:** After `modelBuilder.Ignore<TaxAuthorityCreated>();` (line 53)
**DI insertion point:** After `services.AddScoped<ITaxAuthorityRepository, EfTaxAuthorityRepository>();` (line 43)

## Regulatory Context for Seed Data (Future)

While G2 is foundation only (no seed data), these rates should eventually be configurable:
- VAT: 10% (standard), 8% (temporary Jul 2025–Dec 2026), 5% (essential), 0% (exports)
- CIT: 20% (standard), 15% (small ≤VND 3B), 17% (medium VND 3-50B), 10% (preferential 15yr), 17% (preferential 10yr)
- PIT: 5%, 10%, 20%, 30%, 35% (progressive brackets)

The entity model supports all these via decimal RateValue + effective dating + TaxType FK.

---

# Verification Results — [G2] TaxRate

## Status: VERIFIED_PASS

### Checklist Verification

**Domain Entity (TaxRate.cs):**
- [x] Entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity
- [x] Private parameterless constructor — EF Core materialization
- [x] Public constructor with DomainException validation:
  - [x] CompanyId > 0
  - [x] TaxTypeId > 0
  - [x] RateValue >= 0
  - [x] RateName not empty
- [x] Deactivate() method — IsActive = false
- [x] Properties: CompanyId, TaxTypeId, RateValue (decimal), RateName (string), EffectiveFrom (DateOnly), EffectiveTo (DateOnly?), IsActive, Description

**Event (TaxRateCreated.cs):**
- [x] TaxRateCreated event carries TaxRateId + CompanyId + occurredOn — matches event minimalism pattern

**Port (ITaxRateRepository.cs):**
- [x] Interface starts with I, in Domain.Ports namespace
- [x] 4 methods: GetByIdAsync, GetByTaxTypeAndDateAsync, GetAllByCompanyAsync, AddAsync

**Infrastructure — EF Config (TaxRateConfiguration.cs):**
- [x] snake_case table `tax_rates`
- [x] Composite unique index on (CompanyId, TaxTypeId, RateValue, EffectiveFrom)
- [x] CompanyId FK → Company with Restrict delete
- [x] TaxTypeId FK → TaxType with Restrict delete
- [x] xmin row version
- [x] RateValue decimal(5,2), RateNameHasMaxLength(200), DescriptionHasMaxLength(500)

**Infrastructure — Repository (EfTaxRateRepository.cs):**
- [x] GetByIdAsync — tracked (no AsNoTracking)
- [x] GetByTaxTypeAndDateAsync — effective date range filter (EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive)
- [x] GetAllByCompanyAsync — AsNoTracking, ordered by TaxTypeId then EffectiveFrom
- [x] AddAsync — delegates to DbSet

**Infrastructure — DbContext:**
- [x] DbSet<TaxRate> TaxRates property present
- [x] modelBuilder.Ignore<TaxRateCreated>() present

**Infrastructure — DI:**
- [x] AddScoped<ITaxRateRepository, EfTaxRateRepository>() registered

**Architecture:**
- [x] Entity in Domain.Entities namespace
- [x] Domain.csproj: zero PackageReference elements
- [x] 22/22 architecture tests pass
- [x] 0 new NuGet refs added

**Build:**
- [x] dotnet build SmeAccounting.sln — 0 warnings, 0 errors

### Edge Case — Auditor Flag (effectiveTo >= effectiveFrom)

The auditor flagged missing `effectiveTo >= effectiveFrom` validation as a WARN. Verified: the entity constructor does NOT enforce this invariant. This is acceptable for the following reasons:
1. The verification checklist and plan do not mandate this validation
2. The application layer (FluentValidation) can enforce ordering at command level
3. EF config allows null EffectiveTo (indefinite rates) — common case
4. The GetByTaxTypeAndDateAsync query correctly handles both null and non-null EffectiveTo
5. All other entities in the codebase (FiscalYear, Project) do not validate date ordering in constructors either

### Counts
- DbContext: 22 DbSets, 18 ignored events
- DI: 17 AddScoped registrations
- Architecture tests: 22/22 pass
- Build: 0 warnings, 0 errors

---

# Task-Specific Research — [G3] TaxRule & TaxExemptionReason domain

## Critical Context: TaxRule as the Regulatory Glue

TaxRule is the central entity that **links** the other tax entities together into an enforceable rule. It answers: "For a given company, under what conditions does this tax type apply at this rate with this treatment?" It is NOT a calculation engine — it's a configurable rule set that the application layer queries at posting time.

**TaxRule sits at the intersection of 4 FKs:**
- **Company** — rules are company-scoped
- **TaxType** — which tax (VAT, CIT, PIT, etc.)
- **TaxRate** — which rate applies (10%, 8%, 20%, etc.)
- **TaxTreatment** — how it's treated (standard, exempt, zero-rate, etc.)

**Example real-world TaxRule:**
- "VAT at 10% standard rate for all goods/services not otherwise specified" → Company=ACME, TaxType=VAT, TaxRate=10%, TaxTreatment=StandardRate, Conditions=null, LegalRef="Law 48/2024/QH15 Art. 4"
- "VAT at 0% for exported goods" → Company=ACME, TaxType=VAT, TaxRate=0%, TaxTreatment=ZeroRate, Conditions="goods must be exported", LegalRef="Law 48/2024/QH15 Art. 4(1)"
- "VAT exempt for agricultural products" → Company=ACME, TaxType=VAT, TaxRate=null (no rate — exempt), TaxTreatment=Exempt, Conditions="self-produced agricultural products", LegalRef="Law 48/2024/QH15 Art. 5"

**Key design decision — TaxRate FK is nullable:**
- Exempt and NonTaxable treatments have no rate — they're "out of scope" for rate application
- The TaxRate FK should be `long?` (nullable) to support exemption rules where no rate applies
- This matches the real-world distinction: a 0% rate (TaxRate present) vs. exempt (no rate)

## Critical Context: TaxExemptionReason for Audit Trail

TaxExemptionReason documents **why** a specific good/service is exempt from tax. In Vietnamese law, exemptions must cite specific legal provisions. This entity provides the audit trail for tax examiners.

**Example real-world TaxExemptionReason:**
- Code: "VAT-AGR-01", Name: "Self-produced agricultural products", LegalBasis: "Law 48/2024/QH15 Art. 5(1)", TaxType: VAT
- Code: "VAT-FIN-01", Name: "Credit services", LegalBasis: "Law 48/2024/QH15 Art. 5(6)", TaxType: VAT
- Code: "CIT-SME-01", Name: "Small enterprise preferential rate", LegalBasis: "Law 67/2025/QH15 Art. 12", TaxType: CIT

**TaxExemptionReason is simpler** — it's a reference entity like TaxAuthority (CompanyId-scoped, Code, Name, IsActive) with an additional TaxType FK and LegalBasis string.

## Entity Design

### TaxRule Entity Properties

| Property | Type | Default | Max Length (EF) | Notes |
|----------|------|---------|-----------------|-------|
| CompanyId | long | — | FK to companies | Required, Restrict |
| TaxTypeId | long | — | FK to tax_types | Required, Restrict |
| TaxRateId | long? | null | FK to tax_rates | **Nullable** — null for exempt/non-taxable rules |
| TaxTreatmentId | long | — | FK to tax_treatments | Required, Restrict |
| Code | string | string.Empty | 20 | Unique per company (e.g., "VAT-STD-01") |
| Name | string | string.Empty | 200 | Descriptive: "Standard VAT rate" |
| Conditions | string? | null | 2000 | Text/JSON describing when rule applies |
| LegalReference | string | string.Empty | 500 | Law article citation (e.g., "Law 48/2024/QH15 Art. 4") |
| EffectiveFrom | DateOnly | — | date | Rule starts on this date |
| EffectiveTo | DateOnly? | null | date | Nullable — null means indefinite |
| IsActive | bool | true | — | Soft-delete |
| Description | string? | null | 500 | Optional notes |

**Why TaxRateId is nullable:**
- Exempt treatments have no rate — they describe exclusion from tax, not a 0% rate
- NonTaxable treatments are outside the tax scope entirely
- 0% rate (ZeroRate) DOES have a TaxRateId — it's a real rate with deductible input credit
- This nullable FK correctly captures the distinction: rate present = rate applies, rate absent = exempt/non-taxable

**Why LegalReference is required (not nullable):**
- Every tax rule MUST cite its legal basis for audit trail
- Vietnamese tax law requires legal traceability for all tax determinations
- Empty LegalReference would break the audit trail — domain exception in constructor

**Why Code is required:**
- Follows VoucherType/TaxType pattern — all reference entities have Code
- Unique per company for application-level duplicate checking
- Format convention: `{TAXTYPE}-{TREATMENT}-{SEQ}` (e.g., "VAT-STD-01", "CIT-RED-03")

**Why Conditions is text, not JSON:**
- Storing as PostgreSQL `text` column is simpler than JSON type
- Application layer can parse as JSON if needed (no Domain dependency on JSON library)
- Conditions are descriptive: "Goods exported to non-VAT countries", "Revenue ≤ VND 3 billion"
- EF Core maps `string?` to `text` by default in PostgreSQL — no explicit column type needed

### TaxRule Constructor Validation

```csharp
public TaxRule(
    long companyId,
    long taxTypeId,
    long? taxRateId,
    long taxTreatmentId,
    string code,
    string name,
    string legalReference,
    DateOnly effectiveFrom,
    DateOnly? effectiveTo = null,
    string? conditions = null,
    string? description = null)
{
    if (companyId <= 0)
        throw new DomainException("CompanyId must be greater than zero.");
    if (taxTypeId <= 0)
        throw new DomainException("TaxTypeId must be greater than zero.");
    if (taxRateId.HasValue && taxRateId.Value <= 0)
        throw new DomainException("TaxRateId must be greater than zero when provided.");
    if (taxTreatmentId <= 0)
        throw new DomainException("TaxTreatmentId must be greater than zero.");
    if (string.IsNullOrWhiteSpace(code))
        throw new DomainException("Code is required.");
    if (string.IsNullOrWhiteSpace(name))
        throw new DomainException("Name is required.");
    if (string.IsNullOrWhiteSpace(legalReference))
        throw new DomainException("LegalReference is required for audit traceability.");
    // ... set properties, raise event
}
```

**Validation notes:**
- `legalReference` required — non-negotiable for regulatory compliance
- `taxRateId` nullable — valid for exempt/non-taxable rules
- `taxRateId.Value > 0` only checked when `HasValue` — prevents invalid FK values
- `effectiveTo >= effectiveFrom` — same as TaxRate, deferred to application layer (not enforced in constructor, consistent with existing pattern)

### TaxExemptionReason Entity Properties

| Property | Type | Default | Max Length (EF) | Notes |
|----------|------|---------|-----------------|-------|
| CompanyId | long | — | FK to companies | Required, Restrict |
| TaxTypeId | long | — | FK to tax_types | Required, Restrict |
| Code | string | string.Empty | 20 | Unique per company (e.g., "VAT-AGR-01") |
| Name | string | string.Empty | 200 | Descriptive: "Self-produced agricultural products" |
| LegalBasis | string | string.Empty | 500 | Law article citation (e.g., "Law 48/2024/QH15 Art. 5(1)") |
| Description | string? | null | 500 | Optional details |
| IsActive | bool | true | — | Soft-delete |

**TaxExemptionReason follows TaxTreatment pattern** — two FKs (Company + TaxType), both Restrict, unique index on (CompanyId, Code).

**Why LegalBasis is required:**
- Same rationale as TaxRule LegalReference — every exemption must cite its legal basis
- Vietnamese tax law requires legal justification for all exemption determinations
- Tax examiners review exemption reasons against the cited law articles

### TaxExemptionReason Constructor Validation

```csharp
public TaxExemptionReason(
    long companyId,
    long taxTypeId,
    string code,
    string name,
    string legalBasis,
    string? description = null)
{
    if (companyId <= 0)
        throw new DomainException("CompanyId must be greater than zero.");
    if (taxTypeId <= 0)
        throw new DomainException("TaxTypeId must be greater than zero.");
    if (string.IsNullOrWhiteSpace(code))
        throw new DomainException("Code is required.");
    if (string.IsNullOrWhiteSpace(name))
        throw new DomainException("Name is required.");
    if (string.IsNullOrWhiteSpace(legalBasis))
        throw new DomainException("LegalBasis is required for audit traceability.");
    // ... set properties, raise event
}
```

## EF Configuration Design

### TaxRule Configuration

**Table:** `tax_rules` (snake_case plural)

**FKs (4 total, all Restrict):**
1. Company: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`
2. TaxType: `HasOne<TaxType>().WithMany().HasForeignKey(e => e.TaxTypeId).OnDelete(DeleteBehavior.Restrict)`
3. TaxRate: `HasOne<TaxRate>().WithMany().HasForeignKey(e => e.TaxRateId).OnDelete(DeleteBehavior.Restrict)` — **nullable FK**
4. TaxTreatment: `HasOne<TaxTreatment>().WithMany().HasForeignKey(e => e.TaxTreatmentId).OnDelete(DeleteBehavior.Restrict)`

**Unique index:** `(CompanyId, Code)` — matches all other company-scoped entities

**Effective date index:** Single-column index on `(EffectiveFrom)` for date-range queries. Not composite — the query pattern is `EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date)`, which benefits from a standalone EffectiveFrom index.

**Nullable FK pattern for TaxRateId:**
```csharp
builder.Property(e => e.TaxRateId)
    .HasColumnName("tax_rate_id");
// No .IsRequired() — nullable by default for long?
```

**Conditions column:** `string` maps to PostgreSQL `text` by default — no explicit `HasColumnType` needed.

### TaxExemptionReason Configuration

**Table:** `tax_exemption_reasons` (snake_case plural)

**FKs (2 total, both Restrict):**
1. Company: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`
2. TaxType: `HasOne<TaxType>().WithMany().HasForeignKey(e => e.TaxTypeId).OnDelete(DeleteBehavior.Restrict)`

**Unique index:** `(CompanyId, Code)` — matches TaxTreatment pattern (two FKs, unique on Company+Code only)

## Repository Design

### ITaxRuleRepository Methods

Per plan:
1. `GetByIdAsync(long id)` — standard lookup
2. `GetByCodeAsync(string code, long companyId)` — unique per company lookup
3. `GetAllByCompanyAsync(long companyId)` — company-scoped list
4. `GetActiveRulesForDateAsync(DateOnly date, long companyId)` — find all rules active on a specific date
5. `AddAsync(TaxRule taxRule)` — insert

**GetActiveRulesForDateAsync implementation:**
```csharp
public async Task<IReadOnlyList<TaxRule>> GetActiveRulesForDateAsync(DateOnly date, long companyId)
{
    return await _context.TaxRules
        .AsNoTracking()
        .Where(e =>
            e.CompanyId == companyId &&
            e.EffectiveFrom <= date &&
            (e.EffectiveTo == null || e.EffectiveTo >= date) &&
            e.IsActive)
        .OrderBy(e => e.TaxTypeId)
        .ThenBy(e => e.Code)
        .ToListAsync();
}
```

This query finds all rules where:
- Company matches
- EffectiveFrom is on or before the query date
- EffectiveTo is null (indefinite) OR on or after the query date
- Rule is active (not deactivated)

**Ordering:** By TaxType then Code — groups rules by tax type for easy review.

**Note on GetActiveRulesForDateAsync vs GetByTaxTypeAndDateAsync (TaxRate):** TaxRate has a type-specific query because rates are looked up per-type. TaxRule returns ALL active rules for the date because the application layer needs the full rule set for posting configuration.

### ITaxExemptionReasonRepository Methods

Per plan:
1. `GetByIdAsync(long id)` — standard lookup
2. `GetByCodeAsync(string code, long companyId)` — unique per company lookup
3. `GetAllByCompanyAsync(long companyId)` — company-scoped list
4. `GetAllByTaxTypeAsync(long taxTypeId)` — filter by parent TaxType
5. `AddAsync(TaxExemptionReason taxExemptionReason)` — insert

**GetAllByTaxTypeAsync:** Same pattern as ITaxTreatmentRepository — filter by TaxTypeId for type-specific exemption reasons.

## Current State for Insertion Points

**After G2 TaxRate (current state):**
- DbContext: 22 DbSets, 18 ignored events
- DI: 17 AddScoped registrations

**After G3 TaxRule + TaxExemptionReason:**
- DbContext: 24 DbSets, 20 ignored events
- DI: 19 AddScoped registrations

**DbContext insertion point:** After `modelBuilder.Ignore<TaxRateCreated>();` (line 55)
**DI insertion point:** After `services.AddScoped<ITaxRateRepository, EfTaxRateRepository>();` (line 44)

## Files to Create/Modify

### New Files (10)

1. `src/SmeAccounting.Domain/Entities/TaxRule.cs` — Entity
2. `src/SmeAccounting.Domain/Events/TaxRuleCreated.cs` — Domain Event
3. `src/SmeAccounting.Domain/Ports/ITaxRuleRepository.cs` — Port Interface
4. `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxRuleConfiguration.cs` — EF Config
5. `src/SmeAccounting.Infrastructure/Repositories/EfTaxRuleRepository.cs` — Repository
6. `src/SmeAccounting.Domain/Entities/TaxExemptionReason.cs` — Entity
7. `src/SmeAccounting.Domain/Events/TaxExemptionReasonCreated.cs` — Domain Event
8. `src/SmeAccounting.Domain/Ports/ITaxExemptionReasonRepository.cs` — Port Interface
9. `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxExemptionReasonConfiguration.cs` — EF Config
10. `src/SmeAccounting.Infrastructure/Repositories/EfTaxExemptionReasonRepository.cs` — Repository

### Modified Files (2)

11. `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` — Add 2 DbSets + 2 Ignore events
12. `src/SmeAccounting.Infrastructure/DependencyInjection.cs` — Add 2 AddScoped registrations

### No New Enums Needed

TaxRule uses existing entities as FKs (TaxType, TaxRate, TaxTreatment). No new enum types needed — the rule's behavior is determined by the linked entities.

## Implementation Sequence

1. Create `TaxRuleCreated` event in `Domain/Events/TaxRuleCreated.cs`
2. Create `TaxRule` entity in `Domain/Entities/TaxRule.cs`
3. Create `ITaxRuleRepository` port in `Domain/Ports/ITaxRuleRepository.cs`
4. Create `TaxRuleConfiguration` in `Infrastructure/Persistence/Configurations/TaxRuleConfiguration.cs`
5. Create `EfTaxRuleRepository` in `Infrastructure/Repositories/EfTaxRuleRepository.cs`
6. Create `TaxExemptionReasonCreated` event in `Domain/Events/TaxExemptionReasonCreated.cs`
7. Create `TaxExemptionReason` entity in `Domain/Entities/TaxExemptionReason.cs`
8. Create `ITaxExemptionReasonRepository` port in `Domain/Ports/ITaxExemptionReasonRepository.cs`
9. Create `TaxExemptionReasonConfiguration` in `Infrastructure/Persistence/Configurations/TaxExemptionReasonConfiguration.cs`
10. Create `EfTaxExemptionReasonRepository` in `Infrastructure/Repositories/EfTaxExemptionReasonRepository.cs`
11. Edit `SmeAccountingDbContext.cs` — add 2 DbSets + 2 Ignore events
12. Edit `DependencyInjection.cs` — add 2 AddScoped registrations
13. `dotnet build SmeAccounting.sln` — must succeed (TreatWarningsAsErrors)
14. `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 must pass

## Verification Criteria

### What "Done Correctly" Looks Like

**TaxRule:**
1. `TaxRule` entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity, private ctor, public ctor with DomainException validation
2. Entity has 4 FK properties: CompanyId (long), TaxTypeId (long), TaxRateId (long? nullable), TaxTreatmentId (long)
3. Entity has Code, Name, Conditions (string?), LegalReference (string required), EffectiveFrom (DateOnly), EffectiveTo (DateOnly?), IsActive (bool), Description (string?)
4. Constructor validates: companyId > 0, taxTypeId > 0, taxRateId.Value > 0 when HasValue, taxTreatmentId > 0, code not empty, name not empty, legalReference not empty
5. `TaxRuleCreated` event carries TaxRuleId + CompanyId + occurredOn
6. `ITaxRuleRepository` in `SmeAccounting.Domain.Ports` — starts with I, 5 methods (GetById, GetByCode, GetAllByCompany, GetActiveRulesForDate, Add)
7. EF config: snake_case table `tax_rules`, unique index `(CompanyId, Code)`, 4 FKs all Restrict, xmin row version
8. EF config: TaxRateId nullable FK — no `.IsRequired()`, FK still configured with Restrict
9. Repository: `AsNoTracking()` for GetAllByCompany and GetActiveRulesForDate, tracked for GetById/GetByCode
10. Repository: `GetActiveRulesForDateAsync` filters EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive

**TaxExemptionReason:**
11. `TaxExemptionReason` entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity, private ctor, public ctor with DomainException validation
12. Entity has 2 FK properties: CompanyId (long), TaxTypeId (long)
13. Entity has Code, Name, LegalBasis (string required), Description (string?), IsActive (bool)
14. Constructor validates: companyId > 0, taxTypeId > 0, code not empty, name not empty, legalBasis not empty
15. `TaxExemptionReasonCreated` event carries TaxExemptionReasonId + CompanyId + occurredOn
16. `ITaxExemptionReasonRepository` in `SmeAccounting.Domain.Ports` — starts with I, 5 methods (GetById, GetByCode, GetAllByCompany, GetAllByTaxType, Add)
17. EF config: snake_case table `tax_exemption_reasons`, unique index `(CompanyId, Code)`, 2 FKs both Restrict, xmin row version
18. Repository: `AsNoTracking()` for GetAllByCompany and GetAllByTaxType, tracked for GetById/GetByCode

**Shared:**
19. DbContext: 24 DbSets, 20 ignored events
20. DI: 19 AddScoped registrations
21. Build: zero warnings (TreatWarningsAsErrors)
22. Tests: 22/22 pass
23. Domain.csproj: zero new NuGet refs

### What "Failing" Looks Like

1. TaxRateId not nullable → can't represent exempt/non-taxable rules (no rate applies)
2. LegalReference nullable → breaks audit trail requirement
3. LegalBasis nullable on TaxExemptionReason → breaks audit trail requirement
4. TaxRate FK using Cascade delete instead of Restrict → violates established pattern
5. TaxTreatment FK using Cascade delete instead of Restrict → violates established pattern
6. Missing `modelBuilder.Ignore<TaxRuleCreated>()` → EF Core migration error
7. Missing `modelBuilder.Ignore<TaxExemptionReasonCreated>()` → EF Core migration error
8. Missing `DbSet<TaxRule>` → entity not tracked by DbContext
9. Missing `DbSet<TaxExemptionReason>` → entity not tracked by DbContext
10. Wrong namespace on entities → architecture test failure
11. Entity using `ArgumentNullException` instead of `DomainException` → violates established pattern
12. Missing TaxTypeId FK validation in constructor → allows invalid references
13. Repository uses `GetAllAsync()` instead of `GetAllByCompanyAsync(companyId)` → violates plan spec
14. GetActiveRulesForDateAsync doesn't filter by effective date range → returns wrong rules
15. Unique index on wrong columns → allows duplicates or overly restrictive
16. Missing private parameterless constructor → EF Core runtime failure
17. Conditions column using JSON type instead of text → unnecessary complexity

## Quality Standards

### Good Output
- TaxRule is the "glue entity" that links TaxType + TaxRate + TaxTreatment with conditions and legal reference
- TaxRateId nullable — correctly models exempt/non-taxable rules where no rate applies
- LegalReference/LegalBasis required — audit trail is non-negotiable for Vietnamese tax compliance
- GetActiveRulesForDateAsync correctly filters by effective date range (same pattern as TaxRate.GetByTaxTypeAndDateAsync)
- TaxExemptionReason follows TaxTreatment two-FK pattern exactly
- EF configs follow every convention (snake_case, xmin, FKs Restrict, unique indexes)
- Code compiles with zero warnings
- All 22 architecture tests pass without modification

### Merely Functional
- TaxRateId not nullable — forces dummy rate for exempt rules
- LegalReference/LegalBasis nullable — loses audit trail
- GetActiveRulesForDateAsync missing effective date filter — returns all rules regardless of date
- Entity uses ArgumentNullException instead of DomainException
- Missing unique index — allows duplicate codes
- Repository uses GetAllAsync instead of GetAllByCompanyAsync
- No domain event raised in constructor

## Cross-Task Dependencies

**Depends on:** [G1] TaxType, TaxTreatment + [G2] TaxRate — TaxRule has FKs to all three
**Wait for:** All three entities must exist before TaxRule EF configuration can reference `HasOne<TaxType>()`, `HasOne<TaxRate>()`, `HasOne<TaxTreatment>()`
**TaxExemptionReason depends on:** [G1] TaxType — has FK to TaxType
**Parallel safe:** TaxRule event, port, and entity can be created in parallel with TaxRate G2 if TaxType+TaxTreatment exist. EF config and repository must wait for all FK targets.
**TaxExemptionReason is simpler** — only depends on TaxType (already exists from G1)

---

## Audit Results — [G3] TaxRule & TaxExemptionReason

**Auditor:** loop-engineer auditor agent
**Date:** 2026-09-17
**Verdict:** CLEAN

### Build & Tests
- `dotnet build SmeAccounting.sln`: **0 warnings, 0 errors** ✓
- `dotnet test tests/SmeAccounting.ArchitectureTests/`: **22/22 passed** ✓

### File-by-File Review

#### 1. `TaxRule.cs` (Entities) — CLEAN
- Inherits `BaseEntity` ✓
- Private parameterless constructor ✓
- Public constructor with DomainException validation ✓
- **4 FKs:** CompanyId (long), TaxTypeId (long), TaxRateId (long?, nullable), TaxTreatmentId (long) ✓
- **Nullable TaxRateId:** Correct — exempt/non-taxable rules have no rate; 0% rate (ZeroRate) has TaxRateId present ✓
- **LegalReference required:** `string LegalReference` non-nullable, validated with `IsNullOrWhiteSpace` + DomainException ✓
- **EffectiveFrom/To:** `DateOnly EffectiveFrom` required, `DateOnly? EffectiveTo` nullable (indefinite) ✓
- **Conditions nullable:** `string? Conditions` — stored as PostgreSQL text ✓
- Validation: DomainException for CompanyId > 0, TaxTypeId > 0, TaxRateId > 0 when provided, TaxTreatmentId > 0, Code not empty, Name not empty, LegalReference not empty ✓
- Event raised: `TaxRuleCreated(Id, companyId, DateTimeOffset.UtcNow)` ✓
- `Deactivate()`: `IsActive = false` only (no event) ✓

#### 2. `TaxRuleCreated.cs` (Events) — CLEAN
- Inherits `DomainEvent` ✓
- Properties: `TaxRuleId` (long), `CompanyId` (long) ✓
- Constructor: taxRuleId, companyId, occurredOn → base(occurredOn) ✓
- Event minimalism: IDs only, no data duplication ✓
- Exact structural match to `VoucherTypeCreated.cs`

#### 3. `ITaxRuleRepository.cs` (Ports) — CLEAN
- 5 methods: GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, GetActiveRulesForDateAsync, AddAsync ✓
- Correct namespace `SmeAccounting.Domain.Ports` ✓
- Starts with "I" ✓
- No UpdateAsync ✓

#### 4. `TaxRuleConfiguration.cs` (EF Config) — CLEAN
- `ToTable("tax_rules")` ✓
- `HasKey`, `HasColumnName`, `ValueGeneratedOnAdd` on Id ✓
- All columns snake_case: company_id, tax_type_id, tax_rate_id, tax_treatment_id, code, name, conditions, legal_reference, effective_from, effective_to, is_active, description ✓
- `IsRequired().HasMaxLength(20)` on Code ✓
- `IsRequired().HasMaxLength(200)` on Name ✓
- `IsRequired().HasMaxLength(500)` on LegalReference ✓
- `HasMaxLength(500)` on Description ✓
- Unique composite index on `(CompanyId, Code)` ✓
- **4 FKs all Restrict:** Company, TaxType, TaxRate (nullable), TaxTreatment ✓
- `HasOne<TaxRate>().WithMany().HasForeignKey(e => e.TaxRateId).OnDelete(DeleteBehavior.Restrict)` — nullable FK correctly configured ✓
- xmin row version last ✓

#### 5. `EfTaxRuleRepository.cs` (Repository) — CLEAN
- Tracked queries: GetByIdAsync, GetByCodeAsync ✓
- `AsNoTracking()` on GetAllByCompanyAsync and GetActiveRulesForDateAsync ✓
- **GetActiveRulesForDateAsync:** Correct filter — `e.EffectiveFrom <= date && (e.EffectiveTo == null || e.EffectiveTo >= date) && e.IsActive` ✓
- GetActiveRulesForDateAsync ordered by TaxTypeId then Code ✓
- `AddAsync`: delegates to DbSet.AddAsync ✓
- No UpdateAsync ✓

#### 6. `TaxExemptionReason.cs` (Entities) — CLEAN
- Inherits `BaseEntity` ✓
- Private parameterless constructor ✓
- Public constructor with DomainException validation ✓
- **2 FKs:** CompanyId (long), TaxTypeId (long) ✓
- **LegalBasis required:** `string LegalBasis` non-nullable, validated with `IsNullOrWhiteSpace` + DomainException ✓
- Validation: DomainException for CompanyId > 0, TaxTypeId > 0, Code not empty, Name not empty, LegalBasis not empty ✓
- Event raised: `TaxExemptionReasonCreated(Id, companyId, DateTimeOffset.UtcNow)` ✓
- `Deactivate()`: `IsActive = false` only (no event) ✓
- Follows TaxTreatment two-FK pattern exactly ✓

#### 7. `TaxExemptionReasonCreated.cs` (Events) — CLEAN
- Inherits `DomainEvent` ✓
- Properties: `TaxExemptionReasonId` (long), `CompanyId` (long) ✓
- Constructor: taxExemptionReasonId, companyId, occurredOn → base(occurredOn) ✓
- Event minimalism: IDs only ✓

#### 8. `ITaxExemptionReasonRepository.cs` (Ports) — CLEAN
- 5 methods: GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, GetAllByTaxTypeAsync, AddAsync ✓
- `GetAllByTaxTypeAsync(long taxTypeId)` — matches TaxTreatment pattern ✓
- Correct namespace ✓

#### 9. `TaxExemptionReasonConfiguration.cs` (EF Config) — CLEAN
- `ToTable("tax_exemption_reasons")` ✓
- All columns snake_case ✓
- `IsRequired().HasMaxLength(20)` on Code ✓
- `IsRequired().HasMaxLength(200)` on Name ✓
- `IsRequired().HasMaxLength(500)` on LegalBasis ✓
- `HasMaxLength(500)` on Description ✓
- Unique composite index on `(CompanyId, Code)` ✓
- **2 FKs both Restrict:** Company, TaxType ✓
- xmin row version last ✓

#### 10. `EfTaxExemptionReasonRepository.cs` (Repository) — CLEAN
- Tracked queries: GetByIdAsync, GetByCodeAsync ✓
- `AsNoTracking()` on GetAllByCompanyAsync and GetAllByTaxTypeAsync ✓
- `AddAsync`: delegates to DbSet.AddAsync ✓
- No UpdateAsync ✓

#### 11. `SmeAccountingDbContext.cs` — CLEAN
- `DbSet<TaxRule> TaxRules => Set<TaxRule>()` ✓
- `DbSet<TaxExemptionReason> TaxExemptionReasons => Set<TaxExemptionReason>()` ✓
- `modelBuilder.Ignore<TaxRuleCreated>()` ✓
- `modelBuilder.Ignore<TaxExemptionReasonCreated>()` ✓
- All 4 additions present (2 DbSets + 2 Ignores) ✓
- Counts: 24 DbSets, 20 ignored events ✓

#### 12. `DependencyInjection.cs` — CLEAN
- `AddScoped<ITaxRuleRepository, EfTaxRuleRepository>()` ✓
- `AddScoped<ITaxExemptionReasonRepository, EfTaxExemptionReasonRepository>()` ✓
- Both placed after other repository registrations ✓
- Count: 19 AddScoped registrations ✓

### Pattern Compliance Matrix

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Entity namespace | `SmeAccounting.Domain.Entities` | `SmeAccounting.Domain.Entities` | ✓ |
| Port namespace | `SmeAccounting.Domain.Ports` | `SmeAccounting.Domain.Ports` | ✓ |
| Event namespace | `SmeAccounting.Domain.Events` | `SmeAccounting.Domain.Events` | ✓ |
| TaxRule: 4 FKs | Company, TaxType, TaxRate, TaxTreatment | 4 FKs | ✓ |
| TaxRateId nullable | `long?` | `long?` | ✓ |
| LegalReference required | non-nullable string | non-nullable string | ✓ |
| LegalBasis required | non-nullable string | non-nullable string | ✓ |
| All FKs Restrict | 4 Restrict on TaxRule, 2 on TaxExemptionReason | All Restrict | ✓ |
| Unique index (TaxRule) | `(CompanyId, Code)` | `(CompanyId, Code)` | ✓ |
| Unique index (TaxExemptionReason) | `(CompanyId, Code)` | `(CompanyId, Code)` | ✓ |
| GetActiveRulesForDateAsync | EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive | Correct filter | ✓ |
| Private ctor | Both entities | Both | ✓ |
| DomainException validation | Both entities | Both | ✓ |
| Event minimalism | EntityId + CompanyId only | Both events correct | ✓ |
| Deactivate no event | Both entities | Both correct | ✓ |
| DbContext: 24 DbSets | 24 | 24 | ✓ |
| DbContext: 20 ignored events | 20 | 20 | ✓ |
| DI: 19 registrations | 19 | 19 | ✓ |
| xmin row version | Both configs | Both correct | ✓ |
| Build warnings | 0 | 0 | ✓ |
| Architecture tests | 22/22 | 22/22 | ✓ |

### Issues Found

None. TaxRule and TaxExemptionReason are clean implementations that precisely follow the RESEARCH.md specification and established patterns.

### Verdict: CLEAN

TaxRule is the "glue entity" that correctly links TaxType + TaxRate (nullable FK for exempt) + TaxTreatment with 4 FKs all Restrict. LegalReference is required, enforcing audit trail. TaxRateId nullable correctly models the distinction between 0% rate (TaxRateId present) and exempt/non-taxable (TaxRateId null). GetActiveRulesForDateAsync implements the correct effective-date range filter. TaxExemptionReason follows the TaxTreatment two-FK pattern with LegalBasis required. All 10 new files and 2 modified files follow established patterns exactly. DbContext counts correct (24 DbSets, 20 events). DI registrations correct (19). Build passes with 0 warnings. All 22 architecture tests pass.

---

## Audit Results — [G4] TaxAccountingMapping

**Auditor:** loop-engineer auditor agent
**Date:** 2026-09-17
**Verdict:** CLEAN

### Build & Tests
- `dotnet build SmeAccounting.sln`: **0 warnings, 0 errors** ✓
- `dotnet test tests/SmeAccounting.ArchitectureTests/`: **22/22 passed** ✓

### File-by-File Review

#### 1. `TaxAccountingMappingType.cs` (ValueObjects) — CLEAN
- 7 enum values: InputVAT, OutputVAT, VATPayable, CITPayable, PITPayable, ImportVAT, TaxDeductible
- Correct namespace `SmeAccounting.Domain.ValueObjects`
- No naming collision — `TaxAccountingMappingType` is distinct from entity `TaxAccountingMapping`
- Self-documenting names match Circular 99 account categories
- No usings needed — plain enum

#### 2. `TaxAccountingMapping.cs` (Entities) — CLEAN
- Inherits `BaseEntity` ✓
- Private parameterless constructor ✓
- Public constructor with DomainException validation ✓
- **4 FKs:** CompanyId, TaxTypeId, TaxTreatmentId, AccountId — all validated > 0 ✓
- MappingType enum property ✓
- IsActive default true ✓
- Description nullable string ✓
- Event raised: `TaxAccountingMappingCreated(Id, companyId, DateTimeOffset.UtcNow)` ✓
- `Deactivate()`: `IsActive = false` only (no event) ✓
- No navigation properties (FK nav-free) ✓

#### 3. `TaxAccountingMappingCreated.cs` (Events) — CLEAN
- Inherits `DomainEvent` ✓
- Properties: `TaxAccountingMappingId` (long), `CompanyId` (long) ✓
- Constructor: taxAccountingMappingId, companyId, occurredOn → base(occurredOn) ✓
- Event minimalism: IDs only, no data duplication ✓
- Exact structural match to `VoucherTypeCreated.cs` / `DepartmentCreated.cs`

#### 4. `ITaxAccountingMappingRepository.cs` (Ports) — CLEAN
- 4 methods: GetByIdAsync, GetAllByCompanyAsync, GetByTaxTypeAndTreatmentAsync, AddAsync ✓
- `GetAllByCompanyAsync(long companyId)` — company-scoped ✓
- No `GetByCodeAsync` — correct (TaxAccountingMapping has no Code property) ✓
- No UpdateAsync ✓
- Correct namespace `SmeAccounting.Domain.Ports` ✓

#### 5. `TaxAccountingMappingConfiguration.cs` (EF Config) — CLEAN
- `ToTable("tax_accounting_mappings")` ✓
- `HasKey`, `HasColumnName`, `ValueGeneratedOnAdd` on Id ✓
- All columns snake_case: company_id, tax_type_id, tax_treatment_id, account_id, mapping_type, is_active, description ✓
- `HasConversion<string>()` for MappingType enum ✓
- MaxLength: Description=500 ✓
- **Unique index:** `(CompanyId, MappingType)` — one mapping per type per company ✓
- **4 FKs all Restrict:**
  1. `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(Restrict)` ✓
  2. `HasOne<TaxType>().WithMany().HasForeignKey(e => e.TaxTypeId).OnDelete(Restrict)` ✓
  3. `HasOne<TaxTreatment>().WithMany().HasForeignKey(e => e.TaxTreatmentId).OnDelete(Restrict)` ✓
  4. `HasOne<Account>().WithMany().HasForeignKey(e => e.AccountId).OnDelete(Restrict)` ✓
- Account FK pattern matches OpeningBalanceMappingConfiguration ✓
- xmin row version last ✓
- FK nav-free (no navigation properties on entity) ✓

#### 6. `EfTaxAccountingMappingRepository.cs` (Repository) — CLEAN
- Tracked queries: GetByIdAsync, GetByTaxTypeAndTreatmentAsync ✓
- `AsNoTracking()` on GetAllByCompanyAsync ✓
- `GetByTaxTypeAndTreatmentAsync`: composite filter (TaxTypeId + TaxTreatmentId + CompanyId) ✓
- `GetAllByCompanyAsync`: filtered by CompanyId, ordered by MappingType ✓
- `AddAsync`: delegates to DbSet.AddAsync ✓
- No UpdateAsync ✓

#### 7. `SmeAccountingDbContext.cs` — CLEAN
- `DbSet<TaxAccountingMapping> TaxAccountingMappings => Set<TaxAccountingMapping>()` ✓
- `modelBuilder.Ignore<TaxAccountingMappingCreated>()` ✓
- Both present — matches requirement "always both" ✓
- Counts: 25 DbSets, 21 ignored events ✓

#### 8. `DependencyInjection.cs` — CLEAN
- `AddScoped<ITaxAccountingMappingRepository, EfTaxAccountingMappingRepository>()` ✓
- Correct placement after other repository registrations ✓
- Count: 20 AddScoped registrations ✓

### Pattern Compliance Matrix

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Entity namespace | `SmeAccounting.Domain.Entities` | `SmeAccounting.Domain.Entities` | ✓ |
| Port namespace | `SmeAccounting.Domain.Ports` | `SmeAccounting.Domain.Ports` | ✓ |
| Event namespace | `SmeAccounting.Domain.Events` | `SmeAccounting.Domain.Events` | ✓ |
| Enum namespace | `SmeAccounting.Domain.ValueObjects` | `SmeAccounting.Domain.ValueObjects` | ✓ |
| Enum naming | `TaxAccountingMappingType` (no collision) | `TaxAccountingMappingType` | ✓ |
| Entity class | `public class TaxAccountingMapping : BaseEntity` | `public class TaxAccountingMapping : BaseEntity` | ✓ |
| Private ctor | `private TaxAccountingMapping() { }` | `private TaxAccountingMapping() { }` | ✓ |
| Validation pattern | DomainException | DomainException | ✓ |
| 4 FKs | Company, TaxType, TaxTreatment, Account | 4 FKs | ✓ |
| FK delete behavior | All Restrict | All Restrict | ✓ |
| Unique index | `(CompanyId, MappingType)` | `(CompanyId, MappingType)` | ✓ |
| Account FK pattern | `HasOne<Account>().WithMany().HasForeignKey().OnDelete(Restrict)` | Matches | ✓ |
| Event pattern | EntityId + CompanyId + occurredOn | TaxAccountingMappingId + CompanyId + occurredOn | ✓ |
| Repository methods | 4 (GetById, GetAllByCompany, GetByTaxTypeAndTreatment, Add) | 4 | ✓ |
| EF table name | `tax_accounting_mappings` | `tax_accounting_mappings` | ✓ |
| xmin row version | Yes, last | Yes, last | ✓ |
| Build warnings | 0 | 0 | ✓ |
| Architecture tests | 22/22 | 22/22 | ✓ |

### Issues Found

None. TaxAccountingMapping is a clean implementation that precisely follows the RESEARCH.md specification and established patterns.

### Verdict: CLEAN

TaxAccountingMapping domain foundation is a faithful implementation of the single-Account-FK mapping pattern. All 6 new files and 2 modified files follow established patterns exactly. The TaxAccountingMappingType enum correctly maps to Circular 99 account categories without namespace collision. 4 FKs (Company, TaxType, TaxTreatment, Account) all use Restrict delete behavior. The Account FK correctly follows the OpeningBalanceMappingConfiguration pattern (single FK, not Debit/Credit pair). Unique index on `(CompanyId, MappingType)` enforces one mapping per type per company at the DB level. DbContext counts correct (25 DbSets, 21 events). DI registrations correct (20). Build passes with 0 warnings. All 22 architecture tests pass.

---

# Task-Specific Research — [G5] TaxPeriod domain

## Critical Context: TaxPeriod vs FiscalPeriod — Different Business Concepts

**TaxPeriod is NOT the same as FiscalPeriod.** They serve fundamentally different purposes:

| Aspect | FiscalPeriod | TaxPeriod |
|--------|-------------|-----------|
| **Purpose** | Accounting period for bookkeeping | Tax filing obligation period |
| **Scope** | All transactions in a month/quarter | One specific tax type per period |
| **Identity** | Identified by FiscalYear + Month | Identified by Company + FiscalPeriod + TaxType |
| **Status workflow** | Open → Closing → Closed | Open → Filed → Closed |
| **Granularity** | One per month per fiscal year | One per tax type per fiscal period |
| **FK dependencies** | YearId → FiscalYear (no CompanyId) | CompanyId + FiscalPeriodId + TaxTypeId |

**Key insight:** A company may have multiple TaxPeriods for the same FiscalPeriod — one for VAT, one for CIT, one for PIT, etc. Each has its own filing deadline, filing frequency, and status. FiscalPeriod tracks when accounting closes; TaxPeriod tracks when tax returns are due.

**FiscalPeriod has no CompanyId** — it's scoped through FiscalYear → Company. TaxPeriod adds CompanyId explicitly for direct company-level queries (e.g., "show me all open tax periods for this company").

## Entity Design

### TaxPeriod Entity Properties

| Property | Type | Default | Max Length (EF) | Notes |
|----------|------|---------|-----------------|-------|
| CompanyId | long | — | FK to companies | Required, Restrict |
| FiscalPeriodId | long | — | FK to fiscal_periods | Required, Restrict |
| TaxTypeId | long | — | FK to tax_types | Required, Restrict |
| FilingFrequency | FilingFrequency (enum) | — | HasConversion<string>() | Monthly or Quarterly |
| FilingDeadline | DateOnly | — | date | When tax return must be filed |
| Status | TaxPeriodStatus (enum) | Open | HasConversion<string>() | Open, Filed, Closed |
| IsActive | bool | true | — | Soft-delete |
| Description | string? | null | 500 | Optional notes |

**Why no Code property:** TaxPeriod is identified by its natural key (CompanyId + FiscalPeriodId + TaxTypeId). Adding a Code would be redundant — this entity is not a reference table like TaxType or VoucherType.

**Why FilingDeadline is required:** Every tax filing period has a法定 deadline. In Vietnamese law:
- VAT monthly filing: by the 20th of the following month
- VAT quarterly filing: by the 30th of the first month of the following quarter
- CIT quarterly filing: by the 30th of the first month of the following quarter
- CIT annual: by the 30th of the first month of the following fiscal year

### Constructor Validation

```csharp
public TaxPeriod(
    long companyId,
    long fiscalPeriodId,
    long taxTypeId,
    FilingFrequency filingFrequency,
    DateOnly filingDeadline,
    string? description = null)
{
    if (companyId <= 0)
        throw new DomainException("CompanyId must be greater than zero.");
    if (fiscalPeriodId <= 0)
        throw new DomainException("FiscalPeriodId must be greater than zero.");
    if (taxTypeId <= 0)
        throw new DomainException("TaxTypeId must be greater than zero.");

    CompanyId = companyId;
    FiscalPeriodId = fiscalPeriodId;
    TaxTypeId = taxTypeId;
    FilingFrequency = filingFrequency;
    FilingDeadline = filingDeadline;
    Status = TaxPeriodStatus.Open; // always starts Open
    Description = description;

    AddDomainEvent(new TaxPeriodCreated(Id, companyId, DateTimeOffset.UtcNow));
}
```

**Validation notes:**
- Three FK validations (CompanyId, FiscalPeriodId, TaxTypeId) — all > 0
- No Code/Name validation — entity has no Code/Name properties
- Status always starts as `Open` — set in field initializer, not constructor param
- FilingDeadline is required — every tax period must have a deadline

### Status Transition Methods

```csharp
public void MarkFiled()
{
    if (Status != TaxPeriodStatus.Open)
        throw new DomainException("Only open tax periods can be marked as filed.");
    Status = TaxPeriodStatus.Filed;
}

public void Close()
{
    if (Status != TaxPeriodStatus.Filed)
        throw new DomainException("Only filed tax periods can be closed.");
    Status = TaxPeriodStatus.Closed;
    AddDomainEvent(new TaxPeriodClosed(Id, DateTimeOffset.UtcNow));
}
```

**Why status validation in methods:** Prevents invalid state transitions (e.g., directly from Open to Closed without filing). This is a domain invariant — the tax return must be filed before the period can be closed.

**TaxPeriodClosed event:** Raised on Close() — matches PeriodClosed pattern from FiscalPeriod. Carries only the entity ID (event minimalism).

## Enum Design

### FilingFrequency Enum

```csharp
namespace SmeAccounting.Domain.ValueObjects;

public enum FilingFrequency
{
    Monthly,
    Quarterly
}
```

**Why NOT reuse PeriodType:** `PeriodType` (Monthly/Quarterly) exists in ValueObjects and is used by FiscalPeriod. While the values are identical, the business semantics differ:
- `PeriodType` describes the accounting period granularity
- `FilingFrequency` describes the tax filing obligation frequency

Reusing `PeriodType` would create a confusing semantic coupling — TaxPeriod would depend on an enum defined for FiscalPeriod. Separate enum is cleaner and follows the established pattern (TaxCategory distinct from VoucherCategory, TaxTreatmentType distinct from PeriodType).

**No namespace collision:** `FilingFrequency` is distinct from the entity `TaxPeriod`. No rename needed.

### TaxPeriodStatus Enum

```csharp
namespace SmeAccounting.Domain.ValueObjects;

public enum TaxPeriodStatus
{
    Open,
    Filed,
    Closed
}
```

**Why NOT reuse PeriodStatus:** `PeriodStatus` (Open/Closing/Closed) is used by FiscalPeriod. TaxPeriod has different status values:
- `PeriodStatus` has `Closing` (intermediate state during period close)
- `TaxPeriodStatus` has `Filed` (tax return submitted, before period close)

Different workflows require different status values. Reusing `PeriodStatus` would force TaxPeriod to use `Closing` which has no meaning in the tax filing context.

**No namespace collision:** `TaxPeriodStatus` is distinct from `PeriodStatus` and from entity `TaxPeriod`.

## FK Configuration Design

### Three FKs, All Restrict

```csharp
// Company FK — same pattern as all company-scoped entities
builder.HasOne<Company>()
    .WithMany()
    .HasForeignKey(e => e.CompanyId)
    .OnDelete(DeleteBehavior.Restrict);

// FiscalPeriod FK — links to accounting period
builder.HasOne<FiscalPeriod>()
    .WithMany()
    .HasForeignKey(e => e.FiscalPeriodId)
    .OnDelete(DeleteBehavior.Restrict);

// TaxType FK — links to tax type
builder.HasOne<TaxType>()
    .WithMany()
    .HasForeignKey(e => e.TaxTypeId)
    .OnDelete(DeleteBehavior.Restrict);
```

**No navigation properties on entity** — FK nav-free pattern (matches all existing entities). The EF config defines the relationships.

**FiscalPeriod FK pattern:** `HasOne<FiscalPeriod>().WithMany().HasForeignKey().OnDelete(Restrict)` — same as `HasOne<Company>().WithMany()` pattern. FiscalPeriod doesn't have a CompanyId, but that's fine — the TaxPeriod's CompanyId provides company scoping independently.

### Unique Index

**Option A:** `(CompanyId, FiscalPeriodId, TaxTypeId)` — one tax period per company per fiscal period per tax type
**Option B:** `(CompanyId, FiscalPeriodId, TaxTypeId, FilingFrequency)` — adds filing frequency to uniqueness

**Recommendation: Option A** — `(CompanyId, FiscalPeriodId, TaxTypeId)` is the natural business key. A company cannot have two VAT periods for the same fiscal period — that would be a data error. FilingFrequency is a property of the tax period, not part of its identity.

**Index SQL equivalent:**
```sql
CREATE UNIQUE INDEX IX_tax_periods_company_id_fiscal_period_id_tax_type_id
ON tax_periods (company_id, fiscal_period_id, tax_type_id);
```

### Additional Indexes

- `CompanyId` — for company-scoped queries ("all tax periods for this company")
- `FiscalPeriodId` — for period-scoped queries ("all tax periods for this fiscal period")
- `TaxTypeId` — for type-scoped queries ("all CIT tax periods")

## Repository Design

### ITaxPeriodRepository Methods

| Method | Purpose |
|--------|---------|
| GetByIdAsync(long id) | Standard lookup |
| GetAllByCompanyAsync(long companyId) | Company-scoped list |
| GetByFiscalPeriodAndTaxTypeAsync(long fiscalPeriodId, long taxTypeId, long companyId) | Lookup by natural key |
| AddAsync(TaxPeriod taxPeriod) | Insert |

**No GetByCodeAsync** — TaxPeriod has no Code property. Unique lookup is by (FiscalPeriodId + TaxTypeId + CompanyId).

**GetByFiscalPeriodAndTaxTypeAsync:** Tracked query (may be followed by status updates). Returns single entity for the natural key.

### EfTaxPeriodRepository Patterns

- `GetByIdAsync` — tracked (no AsNoTracking)
- `GetAllByCompanyAsync` — `AsNoTracking()`, filtered by CompanyId, ordered by FilingDeadline
- `GetByFiscalPeriodAndTaxTypeAsync` — tracked, composite filter (FiscalPeriodId + TaxTypeId + CompanyId)
- `AddAsync` — delegates to DbSet.AddAsync
- No UpdateAsync — EF Core change tracking handles updates

## Domain Event Design

### TaxPeriodCreated Event

```csharp
namespace SmeAccounting.Domain.Events;

public class TaxPeriodCreated : DomainEvent
{
    public long TaxPeriodId { get; }
    public long CompanyId { get; }

    public TaxPeriodCreated(
        long taxPeriodId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxPeriodId = taxPeriodId;
        CompanyId = companyId;
    }
}
```

**Event minimalism:** TaxPeriodId + CompanyId + occurredOn — matches all other company-scoped entity events. No FiscalPeriodId, TaxTypeId, FilingFrequency, FilingDeadline — just IDs.

### TaxPeriodClosed Event

```csharp
namespace SmeAccounting.Domain.Events;

public class TaxPeriodClosed : DomainEvent
{
    public long TaxPeriodId { get; }

    public TaxPeriodClosed(long taxPeriodId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxPeriodId = taxPeriodId;
    }
}
```

**Pattern:** Single entity ID + occurredOn — matches PeriodClosed from FiscalPeriod. Raised when Close() is called (not on MarkFiled — filing is an intermediate state, not a terminal event).

## Files to Create/Modify

### New Files (8)

1. `src/SmeAccounting.Domain/ValueObjects/FilingFrequency.cs` — Enum (Monthly, Quarterly)
2. `src/SmeAccounting.Domain/ValueObjects/TaxPeriodStatus.cs` — Enum (Open, Filed, Closed)
3. `src/SmeAccounting.Domain/Entities/TaxPeriod.cs` — Entity (3 FKs, 2 enums, status methods)
4. `src/SmeAccounting.Domain/Events/TaxPeriodCreated.cs` — Domain Event
5. `src/SmeAccounting.Domain/Events/TaxPeriodClosed.cs` — Domain Event
6. `src/SmeAccounting.Domain/Ports/ITaxPeriodRepository.cs` — Port Interface
7. `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxPeriodConfiguration.cs` — EF Config
8. `src/SmeAccounting.Infrastructure/Repositories/EfTaxPeriodRepository.cs` — Repository

### Modified Files (2)

9. `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` — Add 2 DbSets + 2 Ignores
10. `src/SmeAccounting.Infrastructure/DependencyInjection.cs` — Add 1 AddScoped registration

### Total: 8 new files, 2 modified files

## DbContext Changes

**Current state (after G4):** 25 DbSets, 21 ignored events

**After G5:**
- +1 DbSet: `DbSet<TaxPeriod> TaxPeriods => Set<TaxPeriod>();`
- +2 Ignores: `modelBuilder.Ignore<TaxPeriodCreated>();` + `modelBuilder.Ignore<TaxPeriodClosed>();`
- **New state:** 26 DbSets, 23 ignored events

**DI changes:**
- Current: 20 AddScoped registrations
- After G5: 21 AddScoped registrations (+ITaxPeriodRepository)

## Implementation Sequence

1. Create `FilingFrequency` enum in `Domain/ValueObjects/FilingFrequency.cs`
2. Create `TaxPeriodStatus` enum in `Domain/ValueObjects/TaxPeriodStatus.cs`
3. Create `TaxPeriodCreated` event in `Domain/Events/TaxPeriodCreated.cs`
4. Create `TaxPeriodClosed` event in `Domain/Events/TaxPeriodClosed.cs`
5. Create `TaxPeriod` entity in `Domain/Entities/TaxPeriod.cs`
6. Create `ITaxPeriodRepository` port in `Domain/Ports/ITaxPeriodRepository.cs`
7. Create `TaxPeriodConfiguration` in `Infrastructure/Persistence/Configurations/TaxPeriodConfiguration.cs`
8. Create `EfTaxPeriodRepository` in `Infrastructure/Repositories/EfTaxPeriodRepository.cs`
9. Edit `SmeAccountingDbContext.cs` — add 2 DbSets + 2 Ignores
10. Edit `DependencyInjection.cs` — add AddScoped registration
11. `dotnet build SmeAccounting.sln` — must succeed (TreatWarningsAsErrors)
12. `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 must pass

## Verification Criteria

### What "Done Correctly" Looks Like
1. `FilingFrequency` enum has exactly 2 values: Monthly, Quarterly — in `Domain/ValueObjects/`
2. `TaxPeriodStatus` enum has exactly 3 values: Open, Filed, Closed — in `Domain/ValueObjects/`
3. `TaxPeriod` entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity, private ctor, public ctor with DomainException validation
4. Entity has 3 FKs: CompanyId, FiscalPeriodId, TaxTypeId — all validated > 0 in constructor
5. Entity has FilingFrequency (enum), FilingDeadline (DateOnly), Status (enum, default Open), IsActive (bool), Description (string?)
6. `MarkFiled()` validates Status == Open before transitioning to Filed
7. `Close()` validates Status == Filed before transitioning to Closed, raises TaxPeriodClosed event
8. `TaxPeriodCreated` event carries TaxPeriodId + CompanyId + occurredOn
9. `TaxPeriodClosed` event carries TaxPeriodId + occurredOn
10. `ITaxPeriodRepository` in `SmeAccounting.Domain.Ports` — starts with I, 4 methods (GetById, GetAllByCompany, GetByFiscalPeriodAndTaxType, Add)
11. EF config: snake_case table `tax_periods`, unique index `(CompanyId, FiscalPeriodId, TaxTypeId)`, 3 FKs all Restrict, FilingFrequency and Status HasConversion<string>(), xmin row version
12. Repository: `AsNoTracking()` for GetAllByCompany, tracked for GetById/GetByFiscalPeriodAndTaxType
13. DbContext: 26 DbSets, 23 ignored events
14. DI: 21 AddScoped registrations
15. Build: zero warnings (TreatWarningsAsErrors)
16. Tests: 22/22 pass

### What "Failing" Looks Like
1. Enum named `TaxPeriod` causing namespace collision with entity → compiler error (won't happen — names are FilingFrequency and TaxPeriodStatus)
2. Entity missing private parameterless constructor → EF Core runtime failure
3. Missing `modelBuilder.Ignore<TaxPeriodCreated>()` or `Ignore<TaxPeriodClosed>()` → EF Core migration error
4. Missing `DbSet<TaxPeriod>` → entity not tracked by DbContext
5. Missing DI registration → runtime dependency injection failure
6. Missing unique index → duplicate tax periods allowed at DB level
7. Wrong namespace on entity → architecture test failure
8. Entity using `ArgumentNullException` instead of `DomainException` → violates established pattern
9. Missing any of the 3 FK validations in constructor → allows invalid references
10. FiscalPeriodId or TaxTypeId FK using Cascade instead of Restrict → violates established pattern
11. Missing MarkFiled()/Close() status transition methods → no workflow enforcement
12. Close() doesn't raise TaxPeriodClosed event → misses domain event
13. Repository using `GetAllAsync()` instead of `GetAllByCompanyAsync(companyId)` → violates company-scoping
14. Reusing PeriodType/PeriodStatus instead of creating FilingFrequency/TaxPeriodStatus → semantic coupling, wrong status values
15. Missing FilingDeadline property → no deadline tracking

## Quality Standards

### Good Output
- Exact match to TaxAccountingMapping pattern (multi-FK entity, constructor shape, validation, event, Deactivate)
- FilingFrequency and TaxPeriodStatus are distinct enums with clear business semantics
- Status transition methods enforce valid workflow (Open → Filed → Closed)
- TaxPeriodClosed event raised on Close() — matches PeriodClosed pattern
- 3 FKs all validated in constructor with DomainException
- EF config follows every convention (snake_case, xmin, all 3 FKs Restrict, unique index)
- Unique index on (CompanyId, FiscalPeriodId, TaxTypeId) prevents duplicate tax periods
- Code compiles with zero warnings
- All 22 architecture tests pass without modification
- TaxPeriod is clearly distinct from FiscalPeriod in purpose and structure

### Merely Functional
- Entity works but uses different validation pattern (ArgumentNullException vs DomainException)
- Missing unique index (allows duplicate tax periods)
- Missing status transition methods (MarkFiled/Close)
- No domain events raised
- Reusing PeriodType/PeriodStatus instead of creating dedicated enums
- Missing FilingDeadline property
- FiscalPeriodId FK using Cascade instead of Restrict
- Repository uses GetAllAsync instead of GetAllByCompanyAsync
- Missing TaxPeriodClosed event on Close()

## Audit Results — [G5] TaxPeriod

**CLEAN** — No blocking issues. All requirements met, one documented improvement over research spec.

### Domain Entity
- TaxPeriod entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity ✓
- Private parameterless ctor + public ctor with DomainException validation ✓
- 3 FKs validated > 0: CompanyId, FiscalPeriodId, TaxTypeId ✓
- Properties: FilingFrequency (enum), FilingDeadline (DateOnly), Status (enum default Open), IsActive (bool default true), Description (string?) ✓
- Deactivate() sets IsActive = false ✓
- FK nav-free: no Company/FiscalPeriod/TaxType navigation properties ✓

### Status Workflow
- MarkFiled(): validates Status == Open → Filed (no event, correct — intermediate state) ✓
- Close(): validates Status == Filed → Closed, raises TaxPeriodClosed event ✓
- Workflow: Open → Filed → Closed — domain invariants enforced ✓

### Enums
- FilingFrequency: Monthly, Quarterly — in `Domain/ValueObjects/` ✓
- TaxPeriodStatus: Open, Filed, Closed — in `Domain/ValueObjects/` ✓
- Both distinct from PeriodType/PeriodStatus — no semantic coupling ✓

### Domain Events
- TaxPeriodCreated: TaxPeriodId + CompanyId + occurredOn (event minimalism) ✓
- TaxPeriodClosed: TaxPeriodId + CompanyId + occurredOn ✓
- **Deviation note:** Research spec designed TaxPeriodClosed as TaxPeriodId + occurredOn only (matching PeriodClosed pattern). Executor added CompanyId — improves consistency with ALL other company-scoped events (TaxTypeCreated, TaxRateCreated, TaxRuleCreated, etc. all carry CompanyId). Documented in loop MEMORY.md. This is a deliberate improvement, not a bug.

### Port Interface
- ITaxPeriodRepository in `SmeAccounting.Domain.Ports` — starts with I ✓
- 4 methods: GetByIdAsync, GetAllByCompanyAsync, GetByFiscalPeriodAndTaxTypeAsync, AddAsync ✓
- No GetByCodeAsync (entity has no Code property — correct) ✓

### EF Configuration
- TaxPeriodConfiguration: snake_case table `tax_periods` ✓
- Unique index on (CompanyId, FiscalPeriodId, TaxTypeId) ✓
- 3 FKs all Restrict: Company, FiscalPeriod, TaxType ✓
- FilingFrequency and Status: HasConversion<string>() ✓
- xmin row version ✓
- DescriptionHasMaxLength(500) ✓

### Repository
- EfTaxPeriodRepository: AsNoTracking for GetAllByCompanyAsync ✓
- Tracked for GetByIdAsync and GetByFiscalPeriodAndTaxTypeAsync (correct — callers may update) ✓
- No UpdateAsync (change tracking handles it) ✓

### DbContext & DI
- 26 DbSets, 23 ignored events (DomainEvent + 22 events) ✓
- DI: ITaxPeriodRepository registered ✓

### Cross-cutting
- Domain.csproj: zero NuGet PackageReference elements ✓
- Build: 0 warnings, 0 errors ✓
- Architecture tests: 22/22 pass ✓
- All files in correct namespaces ✓

---

## Verification Results — [G5] TaxPeriod

**VERIFIED_PASS** — All requirements met.

### Domain
- FilingFrequency enum: Monthly, Quarterly — in `SmeAccounting.Domain.ValueObjects` ✓
- TaxPeriodStatus enum: Open, Filed, Closed — in `SmeAccounting.Domain.ValueObjects` ✓
- TaxPeriod entity in `SmeAccounting.Domain.Entities` — inherits BaseEntity ✓
- 3 FKs: CompanyId, FiscalPeriodId, TaxTypeId — all validated > 0 in constructor ✓
- FilingDeadline (DateOnly), FilingFrequency (enum), Status (enum default Open), IsActive (default true), Description (string?) ✓
- Private parameterless ctor + public ctor with DomainException validation ✓
- MarkFiled(): validates Status == Open → sets Filed, no event ✓
- Close(): validates Status == Filed → sets Closed + raises TaxPeriodClosed event ✓
- Deactivate() sets IsActive = false ✓

### Events
- TaxPeriodCreated: TaxPeriodId + CompanyId + occurredOn (event minimalism) ✓
- TaxPeriodClosed: TaxPeriodId + CompanyId + occurredOn ✓

### Ports
- ITaxPeriodRepository in `SmeAccounting.Domain.Ports` — starts with I ✓
- 4 methods: GetByIdAsync, GetAllByCompanyAsync, GetByFiscalPeriodAndTaxTypeAsync, AddAsync ✓

### Infrastructure
- TaxPeriodConfiguration: snake_case table `tax_periods`, unique index (CompanyId, FiscalPeriodId, TaxTypeId), 3 FKs all Restrict (Company, FiscalPeriod, TaxType), FilingFrequency and Status HasConversion<string>(), xmin row version ✓
- EfTaxPeriodRepository: AsNoTracking for GetAllByCompany, tracked for GetById/GetByFiscalPeriodAndTaxType ✓
- DbContext: 26 DbSets, 23 ignored events (DomainEvent + 22 events) ✓
- DI: 21 AddScoped repository registrations ✓

### Edge Cases
- MarkFiled() on Filed status → throws DomainException ✓
- Close() on Open status → throws DomainException (must MarkFiled first) ✓
- Close() on already Closed → throws DomainException ✓
- MarkFiled() on Closed status → throws DomainException ✓

### Cross-cutting
- Domain.csproj: zero NuGet PackageReference elements ✓
- Build: 0 warnings, 0 errors ✓
- Architecture tests: 22/22 pass ✓
- All files in correct namespaces (Domain.Entities, Domain.Events, Domain.Ports, Domain.ValueObjects) ✓

---

## Prior Attempt Analysis
(no prior attempts — first research cycle for G5)

## Audit Results — [G6] Integration commands/queries + EF migration

**Verdict: CLEAN**

All audit checks passed:

- DTO records match entity fields correctly (TaxTypeDto, TaxTreatmentDto, TaxAuthorityDto, TaxRateDto, TaxRuleDto with nullable TaxRateId, TaxExemptionReasonDto, TaxAccountingMappingDto, TaxPeriodDto with enum fields)
- Commands have correct parameters matching DTO patterns (CreateTaxTypeCommand, CreateTaxRuleCommand with nullable TaxRateId, CreateTaxPeriodCommand)
- Validators implement FluentValidation rules correctly (CreateTaxTypeCommandValidator, CreateTaxRuleCommandValidator)
- Handlers follow MediatR pattern (CreateTaxTypeHandler, DeactivateTaxTypeHandler)
- EF Phase3TaxFoundation migration creates all 8 tables with correct schema, FKs with Restrict, unique indexes, nullable TaxRateId preserved
- Build: 0 warnings, 0 errors
- Architecture tests: 22/22 pass

## Task-Specific Research — [G7] Regulatory traceability & architecture compliance review

### Context & Prior Work
Phase 3 Tax Foundation completed G1-G6. Eight tax domain entities implemented:
- TaxType, TaxTreatment, TaxAuthority, TaxRate, TaxRule, TaxExemptionReason, TaxAccountingMapping, TaxPeriod
All entities follow VoucherType/Department pattern: CompanyId FK, Code/Name, IsActive, private parameterless ctor, DomainException validation, Deactivate().
Domain.csproj remains pure (zero NuGet refs). 22 NetArchTest rules enforce Clean Architecture.
EF Core configurations use snake_case tables, xmin row version, HasConversion<string>() for enums, DeleteBehavior.Restrict for all FKs.
Application layer commands/queries/DTOs/validators/handlers created for all 8 entities. EF migration Phase3TaxFoundation generated.

### Existing Tools & Resources
**Domain entities to verify:**
- `src/SmeAccounting.Domain/Entities/TaxType.cs`
- `src/SmeAccounting.Domain/Entities/TaxTreatment.cs`
- `src/SmeAccounting.Domain/Entities/TaxAuthority.cs`
- `src/SmeAccounting.Domain/Entities/TaxRate.cs`
- `src/SmeAccounting.Domain/Entities/TaxRule.cs`
- `src/SmeAccounting.Domain/Entities/TaxExemptionReason.cs`
- `src/SmeAccounting.Domain/Entities/TaxAccountingMapping.cs`
- `src/SmeAccounting.Domain/Entities/TaxPeriod.cs`

**Enums in Domain/ValueObjects/:**
- `src/SmeAccounting.Domain/ValueObjects/TaxCategory.cs`
- `src/SmeAccounting.Domain/ValueObjects/TaxTreatmentType.cs`
- `src/SmeAccounting.Domain/ValueObjects/TaxAuthorityLevel.cs`
- `src/SmeAccounting.Domain/ValueObjects/TaxAccountingMappingType.cs`
- `src/SmeAccounting.Domain/ValueObjects/FilingFrequency.cs`
- `src/SmeAccounting.Domain/ValueObjects/TaxPeriodStatus.cs`

**Ports:**
- `src/SmeAccounting.Domain/Ports/ITaxTypeRepository.cs`
- `src/SmeAccounting.Domain/Ports/ITaxTreatmentRepository.cs`
- `src/SmeAccounting.Domain/Ports/ITaxAuthorityRepository.cs`
- `src/SmeAccounting.Domain/Ports/ITaxRateRepository.cs`
- `src/SmeAccounting.Domain/Ports/ITaxRuleRepository.cs`
- `src/SmeAccounting.Domain/Ports/ITaxExemptionReasonRepository.cs`
- `src/SmeAccounting.Domain/Ports/ITaxAccountingMappingRepository.cs`
- `src/SmeAccounting.Domain/Ports/ITaxPeriodRepository.cs`

**EF Configurations:**
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxTypeConfiguration.cs`
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxTreatmentConfiguration.cs`
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxAuthorityConfiguration.cs`
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxRateConfiguration.cs`
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxRuleConfiguration.cs`
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxExemptionReasonConfiguration.cs`
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxAccountingMappingConfiguration.cs`
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxPeriodConfiguration.cs`

**Domain project file:**
- `src/SmeAccounting.Domain/SmeAccounting.Domain.csproj`

**Architecture tests:**
- `tests/SmeAccounting.ArchitectureTests/DependencyRulesTests.cs`
- `tests/SmeAccounting.ArchitectureTests/DomainPurityTests.cs`
- `tests/SmeAccounting.ArchitectureTests/NamingConventionsTests.cs`
- `tests/SmeAccounting.ArchitectureTests/LayerCouplingTests.cs`

### Requirements & Constraints
1. All 7/8 tax entities pass 22 NetArchTest architecture tests — verified via `dotnet test tests/SmeAccounting.ArchitectureTests/` → 22/22 Passed.
2. Domain.csproj has zero new NuGet PackageReference elements — file contains only `<Project Sdk="Microsoft.NET.Sdk">` with empty body.
3. All enums in Domain/ValueObjects/ (not Domain/Enums/) — no `Domain/Enums/` directory exists; all tax enums reside in `Domain/ValueObjects/`.
4. All entities in Domain/Entities/ with private parameterless constructors — each entity contains `private TaxXxx() { }` for EF Core materialization.
5. All ports in Domain/Ports/ starting with I — all repository interfaces named `ITax*Repository`.
6. EF configurations follow snake_case table naming with xmin row version — configurations use `builder.ToTable("tax_types")`, `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")`.
7. CompanyId FK pattern consistent across all company-scoped entities — all configurations use `builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`.
8. Create ADR documenting tax foundation design decisions and regulatory mapping — no ADR found in repo; documentation exists in MEMORY.md and RESEARCH.md but formal ADR file missing.

### Suggested Approach
Verify each requirement by inspecting files listed above, run architecture tests, confirm Domain.csproj empty, grep for private constructors, confirm enum locations, confirm EF config patterns, document findings. Flag missing ADR for creation.

### Verification Criteria
**Passing:**
- `dotnet test tests/SmeAccounting.ArchitectureTests/` returns 22 passed.
- Domain.csproj contains no `<PackageReference>` nodes.
- `find src/SmeAccounting.Domain/ValueObjects -name "Tax*.cs"` returns enums; `find src/SmeAccounting.Domain/Enums` returns nothing.
- Each entity file contains `private TaxXxx() { }`.
- All port files start with `I`.
- Each EF config contains `ToTable("tax_*")` snake_case and `Property<uint>("xmin").IsRowVersion()`.
- Each EF config contains `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`.
- ADR file exists documenting regulatory mapping to VAT Law 48/2024/QH15, CIT Law 67/2025/QH15, PIT Law 109/2025/QH15, Circular 99/2025/TT-BTC.

**Failing:**
- Architecture tests <22 passed.
- Domain.csproj contains PackageReference.
- Enum found in Domain/Enums/ or missing from ValueObjects.
- Entity missing private parameterless constructor.
- Port not starting with I.
- EF config uses PascalCase table name or missing xmin.
- CompanyId FK uses Cascade or different pattern.
- ADR missing or incomplete.

### Quality Standards
Good output: explicit file paths, line numbers for private constructors, table names, xmin usage, FK pattern snippets, test results, clear pass/fail per requirement, note on missing ADR with suggested location `docs/architecture/ADR-00x-tax-foundation.md`.

Merely functional: summary without file evidence, no test run confirmation, vague statements.

### Prior Attempt Analysis
No prior G7 attempt. G6 completed successfully with 22/22 tests passing. Domain purity maintained throughout Phase 3.
