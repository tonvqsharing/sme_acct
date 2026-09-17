# Loop Memory
Updated continuously by all agents as they discover things.

## Learnings

### G1 Batch Consolidated Learnings (Sep 2026)

#### Pattern Discoveries
- **Enum naming convention:** When entity and enum share semantic name (e.g., TaxType), enum gets suffix (`TaxCategory`, `TaxTreatmentType`, `TaxAuthorityLevel`) to avoid C# namespace collision — matches existing `VoucherCategory`/`VoucherType` pattern
- **All G1 entities follow VoucherType pattern exactly:** CompanyId + Code + Name + [Enum] + IsActive + optional Description
- **No domain event on Deactivate()** — matches VoucherType/Department/CostCenter/Project pattern (can add Deactivated event later if needed)
- **ITaxType/ITaxTreatment/ITaxAuthority repositories use GetAllByCompanyAsync** (not GetAllAsync) — all G1 entities are company-scoped
- **Unique index always on (CompanyId, Code)** — NOT composite with other FKs — same scope as VoucherType/TransactionReason

#### Regulatory Learnings
- **Vietnamese tax authority 3-tier hierarchy:** National (Tổng cục Thuế/GDT) → Provincial (Cục Thuế/Regional Sub-Departments) → District (Chi cục thuế/District Teams) — per Decision 381/QD-BTC
- **8 tax types for Vietnamese enterprise accounting:** VAT, CIT, PIT, SpecialConsumption, Resource, Environmental, ImportDuty, ExportDuty — map to Circular 99 accounts 3331–3338
- **5 tax treatment categories with regulatory mapping:** StandardRate, ReducedRate, ZeroRate, Exempt, NonTaxable — from Vietnamese VAT Law 48/2024
- **Critical VAT distinction:** ZeroRate (0%) = deductible input credit; Exempt = non-deductible input credit — captured via InputCreditAllowed bool on TaxTreatment entity

#### Technical Learnings
- **DbContext state after G1:** 21 DbSets, 17 ignored events — each G1 entity adds 1 DbSet + 1 Ignore<TaxXxxCreated>
- **DI state after G1:** 16 AddScoped registrations — each G1 entity adds 1 registration
- **TaxAuthority is standalone** — no FK dependencies on TaxType/TaxTreatment/Account/FiscalPeriod (unlike most other entities)
- **TaxAuthorityLevel has no namespace collision** — enum name is TaxAuthorityLevel, entity is TaxAuthority — distinct names unlike TaxType/TaxTreatment cases
- **TaxTreatment entity follows TransactionReason pattern** — two FKs (Company + TaxType) both Restrict, unique index on (CompanyId, Code) NOT composite with TaxTypeId
- **All 22 architecture tests pass** with G1 entities — Domain.csproj zero NuGet refs preserved
- **Build:** 0 warnings, 0 errors after G1 batch

### G2 TaxRate Learnings (Sep 2026)
- **TaxRate entity pattern:** CompanyId + TaxTypeId (FK) + RateValue (decimal) + RateName (string) + EffectiveFrom (DateOnly) + EffectiveTo (DateOnly?) + IsActive + Description —不同于G1 entities which have Code/Name/Enum, TaxRate has RateValue/RateName instead
- **Effective dating:** EffectiveFrom required + EffectiveTo nullable (null = indefinite) — same nullable DateOnly pattern as Project entity (StartDate/EndDate)
- **Unique index:** (CompanyId, TaxTypeId, RateValue, EffectiveFrom) — composite 4-column uniqueness prevents duplicate rates per type per effective date
- **GetByTaxTypeAndDateAsync filter:** EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive — standard effective-date range query
- **Two FKs both Restrict:** Company + TaxType — same pattern as TaxTreatment
- **No Code property:** Unlike G1 entities, TaxRate uses RateName instead of Code — RateName describes the rate (e.g., "Standard 10%", "Temporary 8%")
- **RateValue decimal(5,2):** Supports rates up to 999.99% — sufficient for all Vietnamese tax rates (max 50%)
- **DbContext after G2:** 22 DbSets, 18 ignored events
- **DI state after G2:** 17 AddScoped registrations
- **All 22 architecture tests pass** — no changes to test suite needed
- **Build:** 0 warnings, 0 errors after G2

### G3 TaxRule & TaxExemptionReason Learnings (Sep 2026)
- **TaxRule is the "glue entity"** — links 4 FKs (Company, TaxType, TaxRate nullable, TaxTreatment) with Code + Name + Conditions + LegalReference + EffectiveFrom/To
- **TaxRateId nullable (long?)** — exempt/non-taxable rules have no rate; 0% rate (ZeroRate) DOES have a TaxRateId. Nullable FK correctly captures the distinction.
- **LegalReference required on TaxRule, LegalBasis required on TaxExemptionReason** — audit trail non-negotiable for Vietnamese tax compliance. Constructor throws DomainException if empty.
- **Conditions stored as text** — not JSON. PostgreSQL maps string? to text by default. Application layer can parse as JSON if needed.
- **TaxRule has 4 FKs all Restrict** — Company, TaxType, TaxRate (nullable), TaxTreatment. Unique index on (CompanyId, Code) only.
- **GetActiveRulesForDateAsync** — EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive. Same effective-date range pattern as TaxRate.GetByTaxTypeAndDateAsync.
- **TaxExemptionReason follows TaxTreatment pattern** — two FKs (Company + TaxType), unique index on (CompanyId, Code), LegalBasis required.
- **No new enums needed** — TaxRule uses existing entities as FKs (TaxType, TaxRate, TaxTreatment). Rule behavior determined by linked entities.
- **DbContext after G3:** 24 DbSets, 20 ignored events
- **DI state after G3:** 19 AddScoped registrations
- **Build:** 0 warnings, 0 errors after G3
- **Architecture tests:** 22/22 pass

### G4 TaxAccountingMapping Learnings (Sep 2026)
- **Single AccountId FK** (not Debit/Credit pair like PostingConfiguration/OpeningBalanceMapping) — mapping points to one COA account; debit/credit direction determined at posting time by journal entry template
- **TaxAccountingMappingType enum:** 7 values (InputVAT, OutputVAT, VATPayable, CITPayable, PITPayable, ImportVAT, TaxDeductible) — no namespace collision with entity (distinct names)
- **Unique index on (CompanyId, MappingType)** — one mapping per type per company (simpler than composite with TaxType/TaxTreatment FKs)
- **4 FKs all Restrict:** Company, TaxType, TaxTreatment, Account — same pattern as OpeningBalanceMapping but with TaxType/TaxTreatment instead of VoucherType
- **Account FK pattern:** `HasOne<Account>().WithMany().HasForeignKey().OnDelete(Restrict)` — copied from OpeningBalanceMappingConfiguration
- **Circular 99 account mapping:** InputVAT→1331/1332, OutputVAT→33311, VATPayable→3331, ImportVAT→33312, CITPayable→3334, PITPayable→3335, TaxDeductible→1331
- **Repository:** No GetByCodeAsync (entity has no Code) — uses GetByTaxTypeAndTreatmentAsync instead
- **DbContext after G4:** 25 DbSets, 21 ignored events
- **DI state after G4:** 20 AddScoped registrations
- **All 22 architecture tests pass** — Domain.csproj zero NuGet refs preserved
- **Build:** 0 warnings, 0 errors after G4
- **EF config for Account FK:** `HasOne<Account>().WithMany().HasForeignKey().OnDelete(Restrict)` — no navigation property on entity, FK relationship in EF config only
- **Repository GetByTaxTypeAndTreatmentAsync:** Tracked (no AsNoTracking) — follows GetByIdAsync pattern since it returns single entity for potential update

### G5 TaxPeriod Learnings (Sep 2026)
- **TaxPeriod is NOT FiscalPeriod** — different business concepts. FiscalPeriod = accounting period for bookkeeping (monthly/quarterly). TaxPeriod = tax filing obligation per tax type (when must file returns for VAT, CIT, PIT, etc.)
- **FiscalPeriod has no CompanyId** — scoped through FiscalYear → Company. TaxPeriod adds CompanyId explicitly for direct company-level queries
- **Two new enums, NOT reusing existing:** `FilingFrequency` (Monthly/Quarterly) and `TaxPeriodStatus` (Open/Filed/Closed) — intentionally distinct from `PeriodType` and `PeriodStatus` because: (1) different status values (Filed vs Closing), (2) different business semantics (filing frequency vs period granularity)
- **No Code property** — identified by natural key (CompanyId + FiscalPeriodId + TaxTypeId). Follows TaxRate pattern (no Code, identified by composite key)
- **3 FKs all Restrict:** Company, FiscalPeriod, TaxType — same pattern as TaxAccountingMapping (4 FKs) and TaxRule (4 FKs)
- **Status workflow with domain events:** MarkFiled() validates Open→Filed (no event), Close() validates Filed→Closed + raises TaxPeriodClosed event. Matches PeriodClosed pattern from FiscalPeriod
- **Unique index:** (CompanyId, FiscalPeriodId, TaxTypeId) — one tax period per company per fiscal period per tax type. Matches business rule: cannot have duplicate filing periods
- **FilingFrequency rule:** Monthly if prior-year revenue > VND 50 billion, quarterly otherwise — stored on entity, not computed. Application layer determines frequency before creating TaxPeriod
- **Two domain events:** TaxPeriodCreated (on construction) + TaxPeriodClosed (on Close method). TaxPeriodCreated follows event minimalism (TaxPeriodId + CompanyId + occurredOn). TaxPeriodClosed carries TaxPeriodId + CompanyId + occurredOn (follows plan spec, includes CompanyId for company-level event handling)
- **Executor chose to include CompanyId in TaxPeriodClosed** per plan instructions, even though PeriodClosed (FiscalPeriod) pattern uses single ID — this enables company-level event handlers to filter TaxPeriodClosed events
- **DbContext after G5:** 26 DbSets, 23 ignored events
- **DI state after G5:** 21 AddScoped registrations
- **All 22 architecture tests pass** — no changes to test suite needed
- **Build:** 0 warnings, 0 errors after G5

### Vietnamese Tax Legislation (Sep 2026)
- **VAT Law 48/2024/QH15** effective July 1, 2025 — rates: 10% standard, 8% temporary (until Dec 31, 2026), 5% essential, 0% exports
- **CIT Law 67/2025/QH15** effective October 1, 2025 — rates: 20% standard, 15% small enterprise (≤VND 3B), 17% medium (VND 3-50B)
- **PIT Law 109/2025/QH15** effective July 1, 2026 — 5 brackets: 5%, 10%, 20%, 30%, 35% (reduced from 7 brackets)
- **Circular 99/2025/TT-BTC** effective January 1, 2026 — tax accounts: 1331 (VAT deductible goods), 1332 (VAT deductible fixed assets), 3331 (VAT payable), 33311 (output VAT), 33312 (import VAT), 3334 (CIT), 3335 (PIT)
- **Decree 70/2025/NĐ-CP** effective June 1, 2025 — e-invoice requirements, XML format mandatory
- **Key distinction:** 0% VAT rate (deductible input credit) vs. VAT-exempt (non-deductible input credit)
- **Temporary 8% VAT reduction** via Resolution 204/2025/QH15 — excludes telecom, finance, real estate, etc.
- **Non-cash payment evidence** required for input VAT credit on purchases ≥ VND 5 million
