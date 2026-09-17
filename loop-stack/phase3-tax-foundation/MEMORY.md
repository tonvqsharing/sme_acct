# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings

### Vietnamese Tax Legislation (Sep 2026)
- **VAT Law 48/2024/QH15** effective July 1, 2025 — rates: 10% standard, 8% temporary (until Dec 31, 2026), 5% essential, 0% exports
- **CIT Law 67/2025/QH15** effective October 1, 2025 — rates: 20% standard, 15% small enterprise (≤VND 3B), 17% medium (VND 3-50B)
- **PIT Law 109/2025/QH15** effective July 1, 2026 — 5 brackets: 5%, 10%, 20%, 30%, 35% (reduced from 7 brackets)
- **Circular 99/2025/TT-BTC** effective January 1, 2026 — tax accounts: 1331 (VAT deductible goods), 1332 (VAT deductible fixed assets), 3331 (VAT payable), 33311 (output VAT), 33312 (import VAT), 3334 (CIT), 3335 (PIT)
- **Decree 70/2025/NĐ-CP** effective June 1, 2025 — e-invoice requirements, XML format mandatory
- **Key distinction:** 0% VAT rate (deductible input credit) vs. VAT-exempt (non-deductible input credit)
- **Temporary 8% VAT reduction** via Resolution 204/2025/QH15 — excludes telecom, finance, real estate, etc.
- **Non-cash payment evidence** required for input VAT credit on purchases ≥ VND 5 million

### G1 TaxType Implementation (Sep 2026)
- **Enum named TaxCategory** (not TaxType) to avoid namespace collision with entity class — same pattern as VoucherCategory/VoucherType
- **8 enum values:** VAT, CIT, PIT, SpecialConsumption, Resource, Environmental, ImportDuty, ExportDuty — map to Circular 99 accounts 3331-3338
- **Entity follows VoucherType pattern exactly:** CompanyId + Code + Name + TaxCategory + IsActive + Description
- **No domain event on Deactivate()** — matches VoucherType/Department/CostCenter/Project pattern
- **ITaxTypeRepository uses GetAllByCompanyAsync** (not GetAllAsync) — tax types are company-scoped
- **EF config:** composite unique index on (CompanyId, Code), CompanyId FK Restrict, TaxCategory HasConversion<string>()
- **DbContext:** 19 DbSets, 15 ignored events after G1 TaxType
- **DI:** 14 AddScoped registrations after G1 TaxType
