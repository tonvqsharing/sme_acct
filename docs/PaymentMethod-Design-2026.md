# PaymentMethod Design — 2026

**Status:** Design only (G1). No code changes.
**Template:** PaymentTerm vertical slice 1:1 copy (see Sources).
**Date:** 2026-09-22

## 1. Responsibilities / Scope

PaymentMethod is a standalone company-scoped master-data entity in the payment subdomain, sibling to PaymentTerm. It classifies *how* a payment is made (cash vs non-cash channel).

In scope for G1 design:

- Domain: `Entities/PaymentMethod.cs`, `ValueObjects/PaymentMethodCategory.cs`, `Events/PaymentMethodCreated.cs`, `Ports/IPaymentMethodRepository.cs`.
- Infrastructure (for G2): `Persistence/Configurations/PaymentMethodConfiguration.cs`, `Repositories/EfPaymentMethodRepository.cs`, DbContext `modelBuilder.Ignore<PaymentMethodCreated>()` only, DI `AddScoped<IPaymentMethodRepository, EfPaymentMethodRepository>()`.
- Application/Api (for G2): Create/Deactivate/Get-by-id/Get-by-company CQRS + FluentValidation + DTO + MVC controller + viewmodel, mirroring PaymentTerm files.

Out of scope: any transaction posting logic, any amount/currency handling (belongs to Money VO / JournalEntry), any bank-account resolution at payment time (G2+ concern if ever needed).

## 2. Field Table

Modeled exactly on `PaymentTerm.cs:7-43` + `PaymentTermConfiguration.cs:7-56`. Diff from PaymentTerm: `PaymentTermType/Days(int?)` swapped for `PaymentMethodCategory/RequiresBankAccount(bool)`; all lengths/constraints/index/FK/xmin kept identical.

| Field | C# type | Required | EF column / constraint | Source |
|---|---|---|---|---|
| CompanyId | `long`, required | Yes | `company_id`, FK `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`, no navigation property on entity | PaymentTerm.cs:9, PaymentTermConfiguration.cs:48-51 |
| Code | `string`, required non-empty | Yes | `code`, `IsRequired().HasMaxLength(20)` | PaymentTerm.cs:10, PaymentTermConfiguration.cs:21-24 |
| Name | `string`, required non-empty | Yes | `name`, `IsRequired().HasMaxLength(200)` | PaymentTerm.cs:11, PaymentTermConfiguration.cs:26-29 |
| Category | `PaymentMethodCategory` enum, required | Yes | `category`, `HasConversion<string>()`, required | PaymentTermType pattern: PaymentTerm.cs:12 + PaymentTermConfiguration.cs:31-33; column name `category` (alternative `payment_method_category` accepted if G2 keeps it consistent everywhere) |
| RequiresBankAccount | `bool`, required (default `false`) | Yes | `requires_bank_account`, required, default `false` | New scalar for G1 (see §4); no PaymentTerm precedent — bool flag instead of FK per §4 rationale |
| IsActive | `bool = true` | Yes | `is_active`, required | PaymentTerm.cs:14 |
| Description | `string?`, optional | No | `description`, `HasMaxLength(500)`, nullable | PaymentTerm.cs:15, PaymentTermConfiguration.cs:41-43 |
| Id | `long` (via `BaseEntity.Id`) | Yes (generated) | `id`, `HasKey`, `ValueGeneratedOnAdd` | PaymentTermConfiguration.cs:14-16; BaseEntity pattern |
| xmin | `uint` concurrency token | Yes (EF-managed) | `xmin`, `Property<uint>("xmin").IsRowVersion()`, declared last in config | PaymentTermConfiguration.cs:53-55 |

Constructor (verbatim PaymentTerm.cs:17-43 pattern):

- `private PaymentMethod()` parameterless for EF Core materialization only.
- `public PaymentMethod(long companyId, string code, string name, PaymentMethodCategory category, bool requiresBankAccount = false, string? description = null)` validates `companyId > 0`, Code non-empty, Name non-empty via `DomainException` (never `ArgumentNullException`); sets `IsActive = true`; raises `PaymentMethodCreated(Id, companyId, DateTime.UtcNow)` (provisional `Id = 0` accepted per transient-aggregate pattern, same as Company/Department/PaymentTerm).

File placement:

- Entity: `src/SmeAccounting.Domain/Entities/PaymentMethod.cs`, `class PaymentMethod : BaseEntity`, namespace `SmeAccounting.Domain.Entities`.
- Enum: `src/SmeAccounting.Domain/ValueObjects/PaymentMethodCategory.cs`, namespace `SmeAccounting.Domain.ValueObjects` (never `Domain/Enums/` — no such directory; all 14 existing enums live in ValueObjects).
- Event: `src/SmeAccounting.Domain/Events/PaymentMethodCreated.cs : DomainEvent`, minimal payload `(PaymentMethodId, CompanyId, occurredOn)` only.
- Port: `src/SmeAccounting.Domain/Ports/IPaymentMethodRepository.cs` with `GetByIdAsync, GetByCodeAsync(code, companyId), GetAllByCompanyAsync(companyId), AddAsync` — no `UpdateAsync`/`DeleteAsync` (change tracking), no unscoped `GetAllAsync`.
- EF config: `src/SmeAccounting.Infrastructure/Persistence/Configurations/PaymentMethodConfiguration.cs`, `internal sealed : IEntityTypeConfiguration<PaymentMethod>`, `ToTable("payment_methods")`.
- Repository: `src/SmeAccounting.Infrastructure/Repositories/EfPaymentMethodRepository.cs` (tracked GetById/GetByCode, `AsNoTracking + Where(CompanyId) + OrderBy(Code)` list, `AddAsync` delegates to `Set<PaymentMethod>`).
- Wiring: DbContext `modelBuilder.Ignore<PaymentMethodCreated>()` only (no `DbSet<PaymentMethod>` required — matches PaymentTerm/Customer/Supplier/Employee convention via `Set<T>` + `ApplyConfigurationsFromAssembly`); DI one line `AddScoped<IPaymentMethodRepository, EfPaymentMethodRepository>()`.
- Entity carries NO `Company` navigation property (`HasOne<Company>().WithMany()` lives in EF config only).
- Domain adds no NuGet/PackageReference (`SmeAccounting.Domain.csproj` stays empty); no `Microsoft.EntityFrameworkCore` using in Domain files.

## 3. PaymentMethodCategory Enum

- **Name decision (closed for G2):** `PaymentMethodCategory` per task brief. Sibling convention would suggest `PaymentMethodType` (PaymentTerm → PaymentTermType), but the brief mandates `PaymentMethodCategory`; G1 enum-suffix rule only triggers on identical entity/enum names, so neither choice collides. G2 executor uses `PaymentMethodCategory` verbatim.
- **Location:** `src/SmeAccounting.Domain/ValueObjects/PaymentMethodCategory.cs` — FAIL if placed in `Domain/Enums/` or elsewhere.
- **Storage:** string via `HasConversion<string>()`, matching all 14 existing enums (NormalBalance, PeriodType, FilingFrequency, TaxTreatmentType, VoucherCategory, AccountType, PeriodStatus, TaxAccountingMappingType, TaxCategory, PaymentTermType, ExchangeRateType, FiscalYearStatus, TaxPeriodStatus, TaxAuthorityLevel).
- **Ship decision (closed for G2):** SHIP the enum in G1 (not free-text Code/Name only).
- **Members (closed for G2):**

```csharp
namespace SmeAccounting.Domain.ValueObjects;

public enum PaymentMethodCategory
{
    Cash = 0,
    BankTransfer = 1,
    Card = 2,
    EWallet = 3,
    Other = 4
}
```

- Member rationale: minimal master-data set decided by planner. NOT sourced from any VAS/Circular 99 list — no repo doc prescribes payment-method values (verified: `docs/Discovery-GeneralAccounting-Entities-2026.md`, `docs/Discovery-Bank-PostingReference-Gaps-2026.md:31,97`, `docs/Patterns-CompanyIsolation-EffectiveDating-2026.md:155`). Regulatory context supports at least a Cash-vs-non-cash distinction (input VAT credit on purchases ≥ VND 5M requires non-cash payment evidence), but members remain a design decision, not a regulatory mandate. Shape mirrors `PaymentTermType` flat 4-member style (`Net, DueOnReceipt, DaysAfterInvoice, EndOfMonth` in `Domain/ValueObjects/PaymentTermType.cs:3-9`), extended to 5 for card/e-wallet channels.

## 4. Relationships

- **Company:** required FK `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — never Cascade/SetNull for master data. Universal company-scoped pattern (FiscalYear, ExchangeRate, Account, AccountGroup, Department, CostCenter, Project, VoucherType, PaymentTerm).
- **RequiresBankAccount (`bool`, default `false`):** scalar flag on PaymentMethod, NOT a FK. Semantics: `true` means payments using this method are expected to reference a bank account at transaction time (e.g. BankTransfer); `false` means no bank account needed (e.g. Cash). The flag informs UI validation / future application-layer rules; it does not itself link to any row.
- **No FKs in G1:** no `BankAccountId`, no `BankId`, no `JournalEntryId`, no `SupplierId`/`CustomerId`, no `PaymentTermId` on PaymentMethod. Rationale: (1) PaymentMethod is a standalone company-scoped master like Bank/VoucherType — the only consumer-FK precedent is Supplier → PaymentTerm (`long? PaymentTermId`, Restrict in `SupplierConfiguration.cs:68-71`); (2) granularity is wrong — one method row (e.g. BankTransfer) spans many bank accounts, so pinning it to a single `BankAccountId` mis-models the domain (BankAccount carries `CompanyId + BankId + BankBranchId? + Code/AccountNumber(max50) + AccountName(max200) + CurrencyCode string(max3)`); (3) payment linkage to journals already exists via free-text `JournalEntry.SourceType/SourceId` + `SetSource(sourceType, sourceId)` (`JournalEntry.cs:13-14,32-36`, `PostingReference.cs:6-7`) — no hard FK needed.
- **Future linkage rule (if ever requested):** follow the Supplier nullable-FK-Restrict precedent — `long? PaymentMethodId` on the consumer side with `HasOne<PaymentMethod>().WithMany().HasForeignKey(...).OnDelete(Restrict)`, never Cascade/SetNull, never a FK column on PaymentMethod itself.

## 5. Lifecycle

- Created with `IsActive = true` via public constructor; `PaymentMethodCreated(PaymentMethodId, CompanyId, occurredOn)` raised at construction.
- `Deactivate()` sets `IsActive = false`, no event (verbatim PaymentTerm pattern, `PaymentTerm.cs` Deactivate).
- No hard delete: repository exposes no `DeleteAsync`; deactivation is soft-delete only (`Account.Deprecate()` / Department / VoucherType precedent — audit trail preserved).
- No `UpdateAsync` on port — EF change tracking handles mutations; repository list query uses `AsNoTracking`.

## 6. Constraints (DB / EF)

- Table `payment_methods`; all columns snake_case: `id, company_id, code, name, category, requires_bank_account, is_active, description, xmin`.
- Lengths: Code required max 20, Name required max 200, Description optional max 500 — FAIL if any other length without cited source.
- Enum column `HasConversion<string>()` (string-stored).
- Composite unique index `(CompanyId, Code)` — per-company code uniqueness at DB level; FAIL if missing or scoped differently (Code-alone or with extra FK).
- FK to Company `OnDelete(Restrict)` — FAIL if Cascade/SetNull.
- `xmin` row-version (`Property<uint>("xmin").IsRowVersion()`) declared last in config.
- No `BankAccountId` FK in G1 — FAIL if added without PLAN mandate.

## 7. Validation Matrix

### Domain constructor (`DomainException`, never ArgumentNullException)

| Case | Rule | Exception |
|---|---|---|
| CompanyId ≤ 0 | `companyId > 0` | `DomainException` |
| Code empty/whitespace | non-empty | `DomainException` |
| Name empty/whitespace | non-empty | `DomainException` |
| Category | valid enum member (implicitly typed) | n/a (compile-time) |
| Private parameterless ctor | EF only, no validation | n/a |

### FluentValidation (`CreatePaymentMethodCommandValidator : AbstractValidator<CreatePaymentMethodCommand>`; mirrors `CreatePaymentTermCommandValidator.cs:8-29`)

| Field | Rules | Failure |
|---|---|---|
| CompanyId | `GreaterThan(0)` | ValidationException → ModelState |
| Code | `NotEmpty + MaximumLength(20)` | ValidationException → ModelState |
| Name | `NotEmpty + MaximumLength(200)` | ValidationException → ModelState |
| Category | `IsInEnum()` | ValidationException → ModelState |
| Description | `MaximumLength(500)` when present | ValidationException → ModelState |

Validator lengths MUST match §6 (B2); FAIL if they diverge. DTO (`PaymentMethodDto` record `Id, CompanyId, Code, Name, Category:string, RequiresBankAccount, IsActive, Description?`) maps enum via `.ToString()`; no domain entity references from Api (controllers MediatR-only, never reference `Domain.Entities`).

## 8. Open UNKNOWNs

- UNKNOWN-1 (RESOLVED by this design): ship the category enum — YES, ship `PaymentMethodCategory` with 5 members above.
- UNKNOWN-2 (RESOLVED): enum type name — `PaymentMethodCategory` per brief (not `PaymentMethodType`); G2 uses verbatim.
- UNKNOWN-3 (RESOLVED): `RequiresBankAccount` in G1 scope with default `false` — YES, scalar bool, default false, required column.
- UNKNOWN-4 (RESOLVED): Description — optional nullable, max 500 (PaymentTerm precedent).
- UNKNOWN-5 (CARRIED FORWARD): any future FK from Supplier/Customer/documents to PaymentMethod — out of G1/G2 scope; follow Supplier nullable-FK-Restrict pattern only if later requested.
- UNKNOWN-6 (CARRIED FORWARD): category column name `category` vs `payment_method_category` — either accepted provided G2 uses it consistently in config, migration, and queries; verifier checks string-conversion + snake_case, not the exact stem.

## 9. Non-Goals

- No invented VAS/Circular 99 method list — FAIL if any implementation cites VAS or Circular 99 Art. 28 as prescribing enum members. VAS/Art. 28 references in `docs/company-company-setting-design-summary.md:84-90` and `docs/architecture/ADR-010-tax-foundation-regulatory-traceability.md:15-20` are generic regime references, not value prescriptions.
- No `Bank`/`BankAccount`/`BankBranch` FK on PaymentMethod in G1.
- No `JournalEntry.SourceType` change — free-text `SetSource` linkage suffices.
- No `Supplier`/`Customer` `PaymentMethodId` FK in G1.
- No `DbSet<PaymentMethod>` required (Ignore-only wiring matches payment subdomain); no Domain NuGet refs; no `Domain/Enums/` folder.

## 10. Test Surface (for G2/G3)

- Build gate: `dotnet build SmeAccounting.sln` 0 warnings (`TreatWarningsAsErrors=true`).
- Arch gate: `dotnet test tests/SmeAccounting.ArchitectureTests/` 22/22 pass (covers Domain purity + controller non-reference rules in `DomainPurityTests.cs:18-57`, `LayerCouplingTests.cs:12-38`).
- New tests per BankTests minimal-test pattern: Domain ctor `DomainException` cases (CompanyId ≤ 0, empty Code, empty Name) + validator cases (lengths above + `IsInEnum`) + handler happy path with List-backed fake; no new EF InMemory packages; BankTests regression still passes.
- Migration SQL check only after green build (EF reads compiled assemblies); descriptive migration name; Down reversal verified.

## Sources

- `src/SmeAccounting.Domain/Entities/PaymentTerm.cs:7-43` — entity shape, ctor validation, Deactivate, event raise.
- `src/SmeAccounting.Domain/ValueObjects/PaymentTermType.cs:3-9` — sibling enum shape/location.
- `src/SmeAccounting.Domain/Events/PaymentTermCreated.cs:3-14` — minimal event payload.
- `src/SmeAccounting.Domain/Ports/IPaymentTermRepository.cs:5-11` — port method set.
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/PaymentTermConfiguration.cs:7-56` — table, lengths, enum string conversion, unique index, Restrict FK, xmin.
- `src/SmeAccounting.Infrastructure/Repositories/EfPaymentTermRepository.cs` — repository pattern.
- `src/SmeAccounting.Application/Validators/CreatePaymentTermCommandValidator.cs:8-29` — validator rules.
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/SupplierConfiguration.cs:68-71` — nullable consumer-FK-Restrict precedent.
- `src/SmeAccounting.Domain/Entities/BankAccount.cs` + `BankAccountConfiguration.cs` — multi-FK Restrict + granularity rationale.
- `src/SmeAccounting.Domain/Entities/JournalEntry.cs:13-14,32-36`, `Entities/PostingReference.cs:6-7` — free-text source linkage, no FK.
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:87,105-109` — Ignore-only wiring + `ApplyConfigurationsFromAssembly`.
- `src/SmeAccounting.Infrastructure/DependencyInjection.cs:54,65-67` — `AddScoped` wiring.
- `src/SmeAccounting.Domain/SmeAccounting.Domain.csproj` — zero-refs baseline.
- `tests/SmeAccounting.ArchitectureTests/DomainPurityTests.cs:18-57`, `LayerCouplingTests.cs:12-38` — arch gates.
- `docs/Discovery-GeneralAccounting-Entities-2026.md:47,105,139,233`, `docs/Discovery-Bank-PostingReference-Gaps-2026.md:31,97`, `docs/Patterns-CompanyIsolation-EffectiveDating-2026.md:155` — no PaymentMethod precedent; enum convention.
- Grep `PaymentMethod|PayMethod|MethodOfPayment|payment_method` over `src/` → 0 matches (greenfield, verified 2026-09-22).
