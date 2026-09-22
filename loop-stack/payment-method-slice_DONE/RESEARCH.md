# Research Log
## Context & Prior Work
### PaymentTerm — direct template for PaymentMethod (closest sibling, same payment subdomain)
- Entity: `src/SmeAccounting.Domain/Entities/PaymentTerm.cs` — `class PaymentTerm : BaseEntity`, props `CompanyId, Code, Name, PaymentTermType, Days(int?), IsActive=true, Description?`; private paramless ctor (EF); public ctor validates `companyId>0`, `Code/Name` non-empty, `Days>=0` via `DomainException`; raises `PaymentTermCreated(Id, companyId, UtcNow)`; `Deactivate()` sets `IsActive=false`, no event.
- Enum: `src/SmeAccounting.Domain/ValueObjects/PaymentTermType.cs` — `Net, DueOnReceipt, DaysAfterInvoice, EndOfMonth`; stored as string (`HasConversion<string>()`). PaymentMethod will likely need own enum in same folder (e.g. `PaymentMethodType`: Cash/BankTransfer/Card/etc. — no existing enum, design decision).
- Event: `src/SmeAccounting.Domain/Events/PaymentTermCreated.cs` — minimal `(PaymentTermId, CompanyId, occurredOn) : DomainEvent`. Copy as `PaymentMethodCreated`.
- Port: `src/SmeAccounting.Domain/Ports/IPaymentTermRepository.cs` — `GetByIdAsync, GetByCodeAsync(code,companyId), GetAllByCompanyAsync(companyId), AddAsync` (no Update/Delete; change-tracking). Copy as `IPaymentMethodRepository`.
- EF config: `src/SmeAccounting.Infrastructure/Persistence/Configurations/PaymentTermConfiguration.cs` — `internal sealed : IEntityTypeConfiguration<PaymentTerm>`; `ToTable("payment_terms")`; snake_case columns; `Code` req max20, `Name` req max200, `Description` max500; enum string conversion; unique index `(CompanyId, Code)`; `HasOne<Company>().WithMany().HasForeignKey(CompanyId).OnDelete(Restrict)` (no nav prop on entity); `xmin` rowversion last. Copy as `PaymentMethodConfiguration` → `payment_methods`.
- Repository: `src/SmeAccounting.Infrastructure/Repositories/EfPaymentTermRepository.cs` — `Set<PaymentTerm>` (no dedicated DbSet), tracked `GetById/GetByCode`, `AsNoTracking + Where(CompanyId) + OrderBy(Code)` for list, `AddAsync` delegates. Copy as `EfPaymentMethodRepository`.
- Application: `Commands/CreatePaymentTermCommand.cs` (record `CompanyId,Code,Name,PaymentTermType,Days?,Description? → CreatePaymentTermResult(Id)`), `Commands/DeactivatePaymentTermCommand.cs`, `Queries/GetPaymentTermQuery.cs`, `Queries/GetPaymentTermsByCompanyQuery.cs`, `Handlers/CreatePaymentTermHandler.cs` (construct domain → AddAsync → SaveChanges → return Id), `Handlers/DeactivatePaymentTermHandler.cs` (GetById → throw InvalidOperationException if null → Deactivate → SaveChanges), `Handlers/GetPaymentTermHandler.cs` + `GetPaymentTermsByCompanyHandler.cs` (manual DTO mapping, enum via `.ToString()`), `Validators/CreatePaymentTermCommandValidator.cs` (CompanyId>0, Code 20, Name 200, IsInEnum, Days>=0 when present, Description 500), `DTOs/PaymentTermDto.cs` (record `Id,CompanyId,Code,Name,PaymentTermType:string,Days?,IsActive,Description?`).
- API: `src/SmeAccounting.Api/Controllers/PaymentTermController.cs` (MVC `Controller`, MediatR only, no Domain refs; `Index(companyId)` → `GetPaymentTermsByCompanyQuery`; `Create GET/POST` with `CreatePaymentTermViewModel` + `Enum.Parse<PaymentTermType>` + ValidationException→ModelState; `Deactivate POST`), `ViewModels/CreatePaymentTermViewModel.cs` (DataAnnotations Required/StringLength mirrors validator).
- Wiring: DI `src/SmeAccounting.Infrastructure/DependencyInjection.cs:54` `AddScoped<IPaymentTermRepository, EfPaymentTermRepository>()`; DbContext `SmeAccountingDbContext.cs:87` only `modelBuilder.Ignore<PaymentTermCreated>()` — NO `DbSet<PaymentTerm>` (convention `Set<T>` used; configs auto-applied via `ApplyConfigurationsFromAssembly`). Same applies to Customer/Supplier/Employee. PaymentMethod needs only `Ignore<PaymentMethodCreated>` + DI line, no DbSet required.

### PaymentMethod references — none exist (greenfield)
- Grep `PaymentMethod|PayMethod|MethodOfPayment|payment_method` over `src/` → 0 matches. No stubs, no synonyms, no migration residue. Safe to add without collision.
- Only payment-adjacent entity is `PaymentTerm`; `BankExchangeRateProvider` adapter name-collision note applies to `Bank*` prefix, not `Payment*`.

### Bank/BankAccount relation check — no relation to add yet
- `Entities/Bank.cs`: company-scoped `CompanyId+Code+Name+IsActive+Description`, `BankCreated` event — same base pattern, no payment link.
- `Entities/BankAccount.cs`: `CompanyId, BankId, BankBranchId?, Code, AccountNumber, AccountName, IsActive, Description?, CurrencyCode?` — currency as string code (not FK), no PaymentMethod/PaymentTerm FK. `BankAccountConfiguration.cs` shows multi-FK Restrict pattern (Company, Bank, BankBranch) + dual uniques `(CompanyId,BankId,BankBranchId,Code)` and `(CompanyId,AccountNumber)` — reusable if PaymentMethod ever links BankAccount, but out of scope unless PLAN demands it.
- `Entities/Supplier.cs` + `Configurations/SupplierConfiguration.cs`: only existing consumer of PaymentTerm — `long? PaymentTermId` nullable + `HasOne<PaymentTerm>().WithMany().HasForeignKey(PaymentTermId).OnDelete(Restrict)`. `Customer.cs` has NO PaymentTermId. If PaymentMethod needs Supplier/Customer linkage, follow Supplier nullable-FK-Restrict pattern; otherwise standalone company-scoped master like Bank.

### Docs — no payment-method design notes
- `docs/Discovery-GeneralAccounting-Entities-2026.md`: lists PaymentTerm as sole payment entity, IPaymentTermRepository port, PaymentTermConfiguration; gaps section notes "PaymentTerm exists, no Bank integration".
- `docs/Discovery-Bank-PostingReference-Gaps-2026.md:31,97`: "PaymentTerm entity exists with company isolation, but no bank integration" — confirms no PaymentMethod design exists.
- `docs/Patterns-CompanyIsolation-EffectiveDating-2026.md:155`: PaymentTermType listed among string-stored enums — confirms enum-location convention (`Domain/ValueObjects/`, not `Domain/Enums/`).

### New-file checklist for PaymentMethod (from T1 VoucherType + T3 TransactionReason learnings in global MEMORY)
Domain: `Entities/PaymentMethod.cs`, `ValueObjects/PaymentMethodType.cs` (if enum needed), `Events/PaymentMethodCreated.cs`, `Ports/IPaymentMethodRepository.cs`; Infrastructure: `Persistence/Configurations/PaymentMethodConfiguration.cs`, `Repositories/EfPaymentMethodRepository.cs`; edits: DbContext `Ignore<PaymentMethodCreated>`, DI `AddScoped`. Application/Api follow only if PLAN scope includes CQRS slice (commands/queries/validators/DTO/controller/viewmodel per PaymentTerm files above).
## External Knowledge & Resources
### Repo docs — no PaymentMethod design exists
- `docs/Discovery-GeneralAccounting-Entities-2026.md:47,105,139,233`: PaymentTerm is sole payment entity (entity + `IPaymentTermRepository` + `PaymentTermConfiguration` listed); gaps note "PaymentTerm exists, no Bank integration". No method/category/design notes.
- `docs/Discovery-Bank-PostingReference-Gaps-2026.md:31,97`: "PaymentTerm entity exists with company isolation, but no bank integration" — confirms no PaymentMethod precedent; Bank slice adds Bank/Branch/Account but no payment linkage.
- `docs/Patterns-CompanyIsolation-EffectiveDating-2026.md:155`: enum convention reference — `AccountType, NormalBalance, PeriodType, PeriodStatus, FiscalYearStatus, ExchangeRateType, TaxCategory, PaymentTermType` all string-stored via `HasConversion<string>()`, all live in `Domain/ValueObjects/` (no `Domain/Enums/` dir). New PaymentMethod enum (if any) goes there.
- `docs/company-company-setting-design-summary.md:84-90`, `docs/architecture/ADR-010-tax-foundation-regulatory-traceability.md:15-20`: VAS/Circular 99 compliance is generic regime reference (Art. 28 → COA mappings), NOT prescriptive of payment-method values. Tax rates/conditions must come from tax legislation, not Circular 99 alone — same applies: do not invent VAS-mandated method list; method values are master-data design decision.
- Regulatory driver (from global MEMORY, Vietnamese Tax Legislation): non-cash payment evidence required for input VAT credit on purchases ≥ VND 5M. Supports a Cash-vs-non-cash category distinction on PaymentMethod, but repo docs prescribe no concrete enum members — planner decides (suggest Cash/BankTransfer/Card/Other or defer enum entirely to free-text Code/Name master).

### No method-category enum exists — greenfield decision
- All 14 enums in `Domain/ValueObjects/`: NormalBalance, PeriodType, FilingFrequency, TaxTreatmentType, VoucherCategory, AccountType, PeriodStatus, TaxAccountingMappingType, TaxCategory, PaymentTermType, ExchangeRateType, FiscalYearStatus, TaxPeriodStatus, TaxAuthorityLevel. None is Cash/Bank/Transfer/category-like.
- Grep `PaymentMethod` over `src/` → 0 matches. No stubs, synonyms, migration residue. Safe greenfield add.
- `PaymentTermType` (`Net, DueOnReceipt, DaysAfterInvoice, EndOfMonth`) is closest sibling enum — shows 4-member flat-enum style; PaymentMethod enum (e.g. `PaymentMethodType`) would mirror this shape if planner wants one.

### Verified copy-templates (exact file paths)
- EF composite-unique + FK-Restrict + enum-as-string: `src/SmeAccounting.Infrastructure/Persistence/Configurations/PaymentTermConfiguration.cs` (ToTable `payment_terms`, Code req max20, Name req max200, Description max500, enum `HasConversion<string>()`, unique `(CompanyId, Code)`, `HasOne<Company>().WithMany().HasForeignKey(CompanyId).OnDelete(Restrict)`, `xmin` rowversion last). `BankConfiguration.cs` identical minus enum.
- Nullable consumer-FK precedent: `SupplierConfiguration.cs:68-71` — `HasOne<PaymentTerm>().WithMany().HasForeignKey(PaymentTermId).OnDelete(Restrict)` with nullable `long? PaymentTermId`. If Supplier/Customer ever reference PaymentMethod, follow this exact pattern; out of scope unless PLAN demands it.
- DbContext: `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` — 45 DbSets + `modelBuilder.Ignore<PaymentTermCreated>()` at line 87, `Ignore<BankCreated/BankBranchCreated/BankAccountCreated>` at 105-107, `ApplyConfigurationsFromAssembly` at 109. Note: PaymentTerm/Customer/Supplier/Employee have NO dedicated DbSet (convention `Set<T>` used) — PaymentMethod needs only `Ignore<PaymentMethodCreated>`, no DbSet required. Bank slice used explicit DbSets; either passes, but Ignore-only matches the payment subdomain.
- DI: `src/SmeAccounting.Infrastructure/DependencyInjection.cs:54,65-67` — `AddScoped<IPaymentTermRepository, EfPaymentTermRepository>()`, `AddScoped<IBankRepository, EfBankRepository>()` etc. PaymentMethod adds one line `AddScoped<IPaymentMethodRepository, EfPaymentMethodRepository>()`.
- Connection: `src/SmeAccounting.Api/appsettings.json` — `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`. DI fallback `Host=localhost;...` if missing — migration/dev DB target confirmer for executor.

### JournalEntry/SourceType linkage — no FK needed
- `JournalEntry.cs:13-14,32-36`: `string? SourceType` + `long? SourceId` set via `SetSource(sourceType, sourceId)` — free-text discriminator, no FK, no enum. `PostingReference.cs:6-7`: same `string SourceType + long SourceId` + `JournalEntryId` FK. Payments would link via SourceType="PaymentMethod:..." string convention, never a hard FK — PaymentMethod stays standalone master, no JournalEntry change required.
## Requirements & Constraints
### Must-follow patterns (from PaymentTerm + Bank slice + global MEMORY)
- Company-scoped master shape: `CompanyId(long) + Code + Name + IsActive(true default) + Description?` (+ optional type enum). Private paramless ctor (EF), public ctor validates `companyId>0`, Code/Name non-empty via `DomainException` (never ArgumentNullException), raises minimal `PaymentMethodCreated(Id, CompanyId, UtcNow)`; `Deactivate()` sets false, no event.
- EF config `internal sealed : IEntityTypeConfiguration<PaymentMethod>`: `ToTable("payment_methods")`, snake_case columns, Code req max20, Name req max200, Description max500, enum (if any) `HasConversion<string>()`, composite unique index `(CompanyId, Code)`, `HasOne<Company>().WithMany().HasForeignKey(CompanyId).OnDelete(Restrict)` (never Cascade/SetNull for master data), no `Company` nav prop on entity, `xmin` IsRowVersion last.
- Port `IPaymentMethodRepository`: `GetByIdAsync, GetByCodeAsync(code,companyId), GetAllByCompanyAsync(companyId), AddAsync` — no Update/Delete (change tracking). Repository: tracked GetById/GetByCode, `AsNoTracking + Where(CompanyId) + OrderBy(Code)` list.
- Wiring: DbContext `modelBuilder.Ignore<PaymentMethodCreated>()` only (no DbSet needed); DI one `AddScoped` line; configs auto-applied via `ApplyConfigurationsFromAssembly`.
- Enum (if planner wants one): new file `Domain/ValueObjects/PaymentMethodType.cs` (NOT `Domain/Enums/`); if entity+enum share name, enum gets suffix per G1 rule. Members are design decision — repo prescribes none.
- Arch/build: Domain zero NuGet refs; Api controllers MediatR-only, no `Domain.Entities` refs; `dotnet build SmeAccounting.sln` 0 warn (TreatWarningsAsErrors=true); 22/22 NetArchTest pass; migration only after green build.

### Explicit non-goals (unless PLAN says otherwise)
- No FK to Bank/BankAccount, no JournalEntry/SourceType change (string linkage suffices), no Supplier/Customer `PaymentMethodId` FK (follow Supplier nullable-Restrict pattern only if later requested), no hard-coded VAS method list (no source prescribes one).
## Task-Specific Research — [G1] PaymentMethod field design
### Proposed field list (modeled exactly on PaymentTerm.cs + PaymentTermConfiguration.cs)
| Field | Type | EF column / constraint | Source |
|---|---|---|---|
| CompanyId | `long`, required | `company_id`, FK `HasOne<Company>().WithMany().HasForeignKey(CompanyId).OnDelete(Restrict)`, no nav prop on entity | PaymentTerm.cs:9, PaymentTermConfiguration.cs:48-51 |
| Code | `string`, required non-empty | `code`, `IsRequired().HasMaxLength(20)` | PaymentTerm.cs:10, PaymentTermConfiguration.cs:21-24 |
| Name | `string`, required non-empty | `name`, `IsRequired().HasMaxLength(200)` | PaymentTerm.cs:11, PaymentTermConfiguration.cs:26-29 |
| Category enum (see below) | enum, required | `payment_method_category` (or `payment_method_type`), `HasConversion<string>()` | PaymentTermType pattern: PaymentTerm.cs:12 + PaymentTermConfiguration.cs:31-33 |
| IsActive | `bool = true` | `is_active` | PaymentTerm.cs:14 |
| Description | `string?`, optional | `description`, `HasMaxLength(500)`, nullable | PaymentTerm.cs:15, PaymentTermConfiguration.cs:41-43 |
| Id / xmin | `BaseEntity.Id long` + `uint xmin IsRowVersion` | `id ValueGeneratedOnAdd`, `xmin` rowversion last | PaymentTermConfiguration.cs:14-16,53-55 |

- Constructor validates `companyId > 0`, Code/Name non-empty via `DomainException` (never ArgumentNullException); private paramless ctor for EF; raises minimal `PaymentMethodCreated(Id, CompanyId, UtcNow)`; `Deactivate()` sets false, no event — PaymentTerm.cs:17-43 verbatim pattern.
- DB constraints: composite unique index `(CompanyId, Code)`; Company FK Restrict (never Cascade/SetNull for master data).
- Port: `IPaymentMethodRepository` with `GetByIdAsync, GetByCodeAsync(code,companyId), GetAllByCompanyAsync(companyId), AddAsync` — no Update/Delete.
- EF config: `internal sealed class PaymentMethodConfiguration : IEntityTypeConfiguration<PaymentMethod>`, `ToTable("payment_methods")`.

### Category enum proposal
- Name: `PaymentMethodCategory` per task brief, file `src/SmeAccounting.Domain/ValueObjects/PaymentMethodCategory.cs`. Note: sibling uses `PaymentTermType` (entity PaymentTerm + enum PaymentTermType share stem with Type suffix); `PaymentMethodType` would mirror that convention more closely — planner picks one, executor uses exactly what DESIGN.md says. No collision either way (G1 enum-suffix rule only triggers on identical names).
- Members (minimal, NOT from any VAS list — no source prescribes one; see Regulatory note in External Knowledge section): `Cash, BankTransfer, Card, EWallet, Other`.
- Closest precedent: `PaymentTermType` flat 4-member enum (`Net, DueOnReceipt, DaysAfterInvoice, EndOfMonth`), stored as string. All 14 existing VOs live in `Domain/ValueObjects/` — never `Domain/Enums/`.
- Regulatory support for at least Cash-vs-non-cash distinction: input VAT credit on purchases ≥ VND 5M requires non-cash payment evidence (global MEMORY, Vietnamese Tax Legislation) — but repo docs prescribe no concrete members; values remain planner decision.

### RequiresBankAccount bool vs nullable BankAccountId FK — recommend bool flag, no FK
- Recommend: `bool RequiresBankAccount` scalar on PaymentMethod (default false; exact default = planner decision, see UNKNOWN-3). No `BankAccountId` FK in G1.
- Why not nullable FK: (1) PaymentMethod is standalone company-scoped master like Bank/VoucherType — no consumer FK exists except Supplier→PaymentTerm (`long? PaymentTermId`, Restrict). (2) Granularity is wrong: one method (e.g. BankTransfer) is used across many bank accounts; pinning a method row to a single BankAccountId mis-models the domain. (3) BankAccount already carries `CompanyId + BankId + BankBranchId? + Code/AccountNumber(max50) + AccountName(max200) + CurrencyCode string(max3)` — reusable lengths if linkage is ever added, but linkage belongs on the transaction/document side (Supplier nullable-FK-Restrict pattern), not on the method master.
- If a future task needs method↔account linkage, follow `SupplierConfiguration` nullable-FK-Restrict precedent (`HasOne<BankAccount>().WithMany().HasForeignKey(...).OnDelete(Restrict)` with `long?`), never Cascade/SetNull.

### Suggested approach
Copy PaymentTerm files 1:1 (entity, enum, event, port, EF config, repository), rename to PaymentMethod, swap `PaymentTermType/Days` for `PaymentMethodCategory/RequiresBankAccount`, keep all lengths/constraints/index/FK/xmin identical; emit DESIGN.md before any code.

### Verification criteria (for verifier/auditor)
- Pass: DESIGN.md lists every field with C# type + EF max length + nullability matching table above; enum file path is `Domain/ValueObjects/`; bool-vs-FK decision recorded with Supplier/BankAccount rationale; UNKNOWNs stated as UNKNOWN (no invented VAS list, no guessed defaults presented as fact).
- Fail: enum placed in `Domain/Enums/`; Code/Name lengths other than 20/200/500 without cited source; `BankAccountId` FK added without PLAN mandate; VAS/Circular 99 cited as prescribing method values; missing unique `(CompanyId, Code)` or Restrict FK.

### Quality standards
- Good: every value traceable to a file:line read above; PaymentTerm↔PaymentMethod diff is explicit (what was kept, what was swapped); open questions cleanly separated as UNKNOWN.
- Merely functional: field list without types/lengths/sources — forces executor to re-research.

### Open questions — stated as UNKNOWN, not invented
- UNKNOWN-1: Whether G1 ships the category enum at all vs free-text Code/Name master only (planner decision; both satisfy company-scoped master pattern).
- UNKNOWN-2: Enum type name — `PaymentMethodCategory` (task brief) vs `PaymentMethodType` (sibling convention). Executor must use DESIGN.md's pick verbatim.
- UNKNOWN-3: `RequiresBankAccount` default (`false` recommended, unconfirmed) and whether the flag is even in G1 scope vs deferred.
- UNKNOWN-4: Description required vs optional (PaymentTerm precedent: optional nullable — assumed unless DESIGN.md says otherwise).
- UNKNOWN-5: Any future FK from Supplier/Customer/documents to PaymentMethod — out of G1 scope; follow Supplier nullable-FK-Restrict pattern only if later requested.

## Task-Specific Research — [G1] verification criteria
### Scope note
- G1 output is DESIGN.md only (no code). Criteria below define what makes that design acceptable so G2 executor has zero ambiguity and verifier judges design text, not implementation. Sources verified 2026-09-22: `src/SmeAccounting.Domain/SmeAccounting.Domain.csproj` (empty, zero refs), `Domain/Entities/PaymentTerm.cs:7-43`, `Infrastructure/Persistence/Configurations/PaymentTermConfiguration.cs:7-56`, `Domain/Ports/IPaymentTermRepository.cs:5-11`, `Domain/Events/PaymentTermCreated.cs:3-14`, `Domain/ValueObjects/PaymentTermType.cs:3-9`, `Application/Validators/CreatePaymentTermCommandValidator.cs:8-29`, `tests/SmeAccounting.ArchitectureTests/DomainPurityTests.cs:18-57` + `LayerCouplingTests.cs:12-38`, `Domain/ValueObjects/` listing (18 files, no `Domain/Enums/` dir).

### Verification Criteria checklist (verifier uses verbatim — all must pass)
**A. Architecture / placement (design must state these paths exactly)**
- [ ] A1. Entity at `src/SmeAccounting.Domain/Entities/PaymentMethod.cs`, `class PaymentMethod : BaseEntity`, namespace `SmeAccounting.Domain.Entities`.
- [ ] A2. Enum (if shipped) at `src/SmeAccounting.Domain/ValueObjects/PaymentMethod{Category|Type}.cs`, namespace `SmeAccounting.Domain.ValueObjects` — FAIL if `Domain/Enums/` or any other folder.
- [ ] A3. Event at `src/SmeAccounting.Domain/Events/PaymentMethodCreated.cs : DomainEvent`, minimal payload `(PaymentMethodId, CompanyId, occurredOn)` only — FAIL if extra payload (names, codes, type).
- [ ] A4. Port at `src/SmeAccounting.Domain/Ports/IPaymentMethodRepository.cs`, `I`-prefixed, methods `GetByIdAsync, GetByCodeAsync(code,companyId), GetAllByCompanyAsync(companyId), AddAsync` — FAIL if `UpdateAsync/DeleteAsync` or `GetAllAsync` (unscoped) specified.
- [ ] A5. Domain zero refs: design adds no NuGet/PackageReference to Domain csproj (currently empty `<Project Sdk>` — verified); no `Microsoft.EntityFrameworkCore` using in Domain files.
- [ ] A6. EF config at `Infrastructure/Persistence/Configurations/PaymentMethodConfiguration.cs`, `internal sealed : IEntityTypeConfiguration<PaymentMethod>`; repository at `Infrastructure/Repositories/EfPaymentMethodRepository.cs`.
- [ ] A7. Wiring: DbContext `modelBuilder.Ignore<PaymentMethodCreated>()` only (no DbSet required — matches PaymentTerm/Customer/Supplier/Employee convention); DI one line `AddScoped<IPaymentMethodRepository, EfPaymentMethodRepository>()`.
- [ ] A8. Entity carries NO `Company` navigation property (`HasOne<Company>().WithMany()` lives in EF config only).

**B. DB / EF rules (design must state each explicitly)**
- [ ] B1. Table `payment_methods`, all columns snake_case (`id, company_id, code, name, {category_col}, is_active, description, xmin`).
- [ ] B2. Lengths: Code required max 20, Name required max 200, Description optional max 500 — FAIL if any other length without cited source file:line.
- [ ] B3. Enum column `HasConversion<string>()` (string-stored, matches all 14 existing enums).
- [ ] B4. Composite unique index `(CompanyId, Code)` — FAIL if missing or scoped differently (e.g. Code-alone or with extra FK).
- [ ] B5. FK `HasOne<Company>().WithMany().HasForeignKey(CompanyId).OnDelete(Restrict)` — FAIL if Cascade/SetNull.
- [ ] B6. `xmin` row-version (`Property<uint>("xmin").IsRowVersion()`) declared last in config.
- [ ] B7. No `BankAccountId` FK on PaymentMethod in G1 — FAIL if added without PLAN mandate (bool flag `RequiresBankAccount` is the approved alternative; granularity rationale: one method spans many accounts).

**C. Validation rules (design must enumerate both layers)**
- [ ] C1. Domain ctor (`DomainException`, never ArgumentNullException): `companyId>0`, Code non-empty, Name non-empty; private parameterless ctor for EF; `IsActive=true` default; `Deactivate()` sets false with no event; ctor raises `PaymentMethodCreated(Id, companyId, UtcNow)` (provisional Id=0 accepted per transient-aggregate pattern).
- [ ] C2. FluentValidation (`CreatePaymentMethodCommandValidator : AbstractValidator<CreatePaymentMethodCommand>`): CompanyId>0, Code NotEmpty+Max20, Name NotEmpty+Max200, enum `IsInEnum()` (if enum shipped), Description Max500. FAIL if lengths diverge from B2.
- [ ] C3. No invented VAS/Circular 99 method list — FAIL if DESIGN.md cites VAS or Circular 99 Art. 28 as prescribing enum members (verified: no repo doc prescribes any; enum members are planner master-data decision).

**D. Enum decision record (design must close all three)**
- [ ] D1. Ship-vs-defer recorded (enum vs free-text Code/Name only).
- [ ] D2. Exact enum type name recorded (`PaymentMethodCategory` per brief vs `PaymentMethodType` per sibling convention) — G2 executor must use it verbatim; G1 suffix rule only triggers on identical entity/enum names so neither collides.
- [ ] D3. Full member list recorded verbatim (proposal `Cash, BankTransfer, Card, EWallet, Other` is unconfirmed until DESIGN.md signs it); `RequiresBankAccount` bool in/out + default recorded (false recommended, unconfirmed).

**E. Test surface (design must state so G2/G3 know what to build)**
- [ ] E1. Build gate: `dotnet build SmeAccounting.sln` 0 warnings (TreatWarningsAsErrors=true).
- [ ] E2. Arch gate: `dotnet test tests/SmeAccounting.ArchitectureTests/` 22/22 pass (covers A5 + controller non-reference rules).
- [ ] E3. New tests per BankTests minimal-test pattern (Domain ctor DomainException cases + validator cases + handler happy path with List-backed fake, no new EF InMemory packages); BankTests regression still passes.
- [ ] E4. Migration SQL check only after green build (EF reads compiled assemblies); migration naming descriptive, Down reversal verified.

### What passing / failing looks like
- PASS: verifier can tick every A–E box from DESIGN.md text alone; every length/constraint/path traces to a source above; UNKNOWNs from prior section are either resolved with planner decision or carried forward labeled UNKNOWN.
- FAIL (any one): enum in `Domain/Enums/`; Code/Name/Description lengths ≠ 20/200/500 unsourced; missing unique `(CompanyId, Code)` or Restrict; `BankAccountId` FK added; VAS cited as prescribing values; port with Update/Delete or unscoped GetAll; event carrying payload beyond IDs+timestamp; Domain NuGet/EF reference introduced.

### Quality bar (good vs merely functional)
- Good: PaymentTerm↔PaymentMethod diff explicit (kept vs swapped: `PaymentTermType/Days` → `{Enum}/RequiresBankAccount`); each field row has C# type + EF length + nullability + source file:line; bool-vs-FK rationale cites Supplier nullable-Restrict + BankAccount granularity.
- Merely functional: field list without types/lengths/sources — forces G2 executor to re-research; reject and send back.

## Task-Specific Research — [G2] file checklist
### Scope note
- Verified 2026-09-22 by reading every template file listed below (exact paths + line refs). Layout rule: PaymentMethod follows PaymentTerm FLAT Application layout (`Application/Commands/`, `Handlers/`, `Queries/`, `Validators/`, `DTOs/`) — NOT the Bank feature-folder layout (`Application/Banks/Commands/` etc.). Design locks from docs/PaymentMethod-Design-2026.md: enum `PaymentMethodCategory` (Cash/BankTransfer/Card/EWallet/Other), ctor `(companyId,code,name,category,requiresBankAccount=false,description=null)`, category column `category`, lengths 20/200/500, unique (CompanyId,Code) + Company FK Restrict + xmin.

### Files to CREATE (12 new, all copy-rename from PaymentTerm template → swap PaymentTermType/Days for PaymentMethodCategory/RequiresBankAccount)
**Domain (4):**
1. `src/SmeAccounting.Domain/Entities/PaymentMethod.cs` ← template `Domain/Entities/PaymentTerm.cs:7-43` (`class PaymentMethod : BaseEntity`; props CompanyId/Code/Name/Category/RequiresBankAccount/IsActive=true/Description?; private paramless ctor; public ctor DomainException validation; `AddDomainEvent(new PaymentMethodCreated(Id, companyId, DateTimeOffset.UtcNow))`; `Deactivate()` no event).
2. `src/SmeAccounting.Domain/ValueObjects/PaymentMethodCategory.cs` ← template `Domain/ValueObjects/PaymentTermType.cs:1-9` (verbatim shape: `namespace SmeAccounting.Domain.ValueObjects;` + `public enum PaymentMethodCategory { Cash = 0, BankTransfer = 1, Card = 2, EWallet = 3, Other = 4 }` per Design §3:54-71). FAIL if placed in `Domain/Enums/` (no such dir).
3. `src/SmeAccounting.Domain/Events/PaymentMethodCreated.cs` ← template `Domain/Events/PaymentTermCreated.cs:1-14` AND `Domain/Events/BankCreated.cs:1-14` (identical minimal pattern: `public class PaymentMethodCreated : DomainEvent { PaymentMethodId, CompanyId }`, ctor `(long paymentMethodId, long companyId, DateTimeOffset occurredOn) : base(occurredOn)`).
4. `src/SmeAccounting.Domain/Ports/IPaymentMethodRepository.cs` ← template `Domain/Ports/IPaymentTermRepository.cs:5-11` verbatim method set (`GetByIdAsync, GetByCodeAsync(code,companyId), GetAllByCompanyAsync(companyId), AddAsync`; no Update/Delete; `using SmeAccounting.Domain.Entities;`, `namespace SmeAccounting.Domain.Ports;`).

**Infrastructure (2):**
5. `src/SmeAccounting.Infrastructure/Persistence/Configurations/PaymentMethodConfiguration.cs` ← template `Infrastructure/Persistence/Configurations/PaymentTermConfiguration.cs:7-56` (`internal sealed : IEntityTypeConfiguration<PaymentMethod>`; `ToTable("payment_methods")`; Id id/ValueGeneratedOnAdd; company_id; code req max20; name req max200; `Category` → `HasColumnName("category").HasConversion<string>()` (locked per Design UNKNOWN-6); `RequiresBankAccount` → `HasColumnName("requires_bank_account")`; is_active; description max500 nullable; unique index `(CompanyId, Code)`; `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(Restrict)`; `xmin` IsRowVersion LAST).
6. `src/SmeAccounting.Infrastructure/Repositories/EfPaymentMethodRepository.cs` ← template `Infrastructure/Repositories/EfPaymentTermRepository.cs:1-39` verbatim (public class, DbContext ctor, `Set<PaymentMethod>` — no dedicated DbSet; tracked GetById/GetByCode, `AsNoTracking + Where(CompanyId) + OrderBy(Code)` list, AddAsync delegates).

**Application (8; flat layout):**
7. `src/SmeAccounting.Application/Commands/CreatePaymentMethodCommand.cs` ← template `Application/Commands/CreatePaymentTermCommand.cs:6-14` (`record CreatePaymentMethodCommand(long CompanyId, string Code, string Name, PaymentMethodCategory Category, bool RequiresBankAccount = false, string? Description = null) : IRequest<CreatePaymentMethodResult>` + `record CreatePaymentMethodResult(long Id)`; `using MediatR; using SmeAccounting.Domain.ValueObjects;`; `namespace SmeAccounting.Application.Commands;`).
8. `src/SmeAccounting.Application/Commands/DeactivatePaymentMethodCommand.cs` ← template `Application/Commands/DeactivatePaymentTermCommand.cs:5-7` (`record DeactivatePaymentMethodCommand(long PaymentMethodId) : IRequest<DeactivatePaymentMethodResult>` + empty result record).
9. `src/SmeAccounting.Application/Handlers/CreatePaymentMethodHandler.cs` ← template `Application/Handlers/CreatePaymentTermHandler.cs:8-30` (`internal sealed class CreatePaymentMethodHandler(IPaymentMethodRepository, IUnitOfWork) : IRequestHandler<...>`; construct domain → AddAsync → SaveChanges → return Id).
10. `src/SmeAccounting.Application/Handlers/DeactivatePaymentMethodHandler.cs` ← template `Application/Handlers/DeactivatePaymentTermHandler.cs:8-25` (GetById → `throw InvalidOperationException` if null → Deactivate → SaveChanges).
11. `src/SmeAccounting.Application/Validators/CreatePaymentMethodCommandValidator.cs` ← template `Application/Validators/CreatePaymentTermCommandValidator.cs:8-29` (CompanyId GreaterThan(0); Code NotEmpty+Max20; Name NotEmpty+Max200; Category `IsInEnum()`; Description Max500; NO Days rule).
12. `src/SmeAccounting.Application/Queries/GetPaymentMethodQuery.cs` ← template `Application/Queries/GetPaymentTermQuery.cs:6` (`record GetPaymentMethodQuery(long PaymentMethodId) : IRequest<PaymentMethodDto?>`).
13. `src/SmeAccounting.Application/Queries/GetPaymentMethodsByCompanyQuery.cs` ← template `Application/Queries/GetPaymentTermsByCompanyQuery.cs:6` (`record GetPaymentMethodsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<PaymentMethodDto>>`).
14. `src/SmeAccounting.Application/Handlers/GetPaymentMethodHandler.cs` + `GetPaymentMethodsByCompanyHandler.cs` ← templates `Application/Handlers/GetPaymentTermHandler.cs:8-27` + `GetPaymentTermsByCompanyHandler.cs:8-29` (manual DTO mapping, enum via `.ToString()`; query handlers take repository only).

**DTO (1 file, SINGLE-DEFINITION rule):**
15. `src/SmeAccounting.Application/DTOs/PaymentMethodDto.cs` ← template `Application/DTOs/PaymentTermDto.cs:1-11` (`record PaymentMethodDto(long Id, long CompanyId, string Code, string Name, string Category, bool RequiresBankAccount, bool IsActive, string? Description)` — enum as STRING via `.ToString()`; `namespace SmeAccounting.Application.DTOs;`). CS8955 lesson (global MEMORY Bank Hierarchy): ONE DTO record per file — never two records sharing one file.

**Api (2):**
16. `src/SmeAccounting.Api/Controllers/PaymentMethodController.cs` ← template `Api/Controllers/PaymentTermController.cs:1-64` (see thinness rule + example below).
17. `src/SmeAccounting.Api/ViewModels/CreatePaymentMethodViewModel.cs` ← template `Api/ViewModels/CreatePaymentTermViewModel.cs:1-25` (DataAnnotations Required/StringLength 20/200/500 mirror validator; `PaymentMethodCategory` as string + `bool RequiresBankAccount`; `namespace SmeAccounting.Api.ViewModels;`).

### Files to EDIT (3 lines total — Bank slice wiring pattern)
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:87` — add `modelBuilder.Ignore<PaymentMethodCreated>();` after `Ignore<PaymentTermCreated>()` line 87. NO `DbSet<PaymentMethod>` (Ignore-only, matches PaymentTerm/Customer/Supplier/Employee convention; Bank slice lines 46-48 used explicit DbSets but either passes — payment subdomain = Ignore-only). Configs auto-apply via `ApplyConfigurationsFromAssembly` line 109.
- `src/SmeAccounting.Infrastructure/DependencyInjection.cs:54` — add `services.AddScoped<IPaymentMethodRepository, EfPaymentMethodRepository>();` after PaymentTerm line 54 (Bank lines 65-67 show same one-line-per-repo pattern).
- `src/SmeAccounting.Application/SmeAccounting.Application.csproj:14` — `<InternalsVisibleTo Include="SmeAccounting.BankTests" />` already exists; all handlers are `internal sealed` so tests MUST resolve visibility: either add new test assembly name alongside (e.g. `<InternalsVisibleTo Include="SmeAccounting.PaymentMethodTests" />`) or put new tests in BankTests project. Executor checks PLAN/G3 scope before adding; never test internal handlers without this line.

### Api controller thinness rule + example (MediatR dispatch only, no Domain.Entities refs)
- Rule (TOOLS.md Key Architecture Constraints + LayerCouplingTests): controller references ONLY `MediatR`, `Microsoft.AspNetCore.Mvc`, `SmeAccounting.Api.ViewModels`, `SmeAccounting.Application.Commands/Queries`, `SmeAccounting.Domain.ValueObjects` (for `Enum.Parse<Category>` only) + `FluentValidation` (for catch). NEVER `using SmeAccounting.Domain.Entities;` or `Domain.Repositories/Ports` — arch tests fail the build on violation.
- Copy pattern from `PaymentTermController.cs:20-63`: `Index(companyId)` → `Send(new GetPaymentMethodsByCompanyQuery(companyId))`; `Create GET` returns empty VM; `Create POST` checks ModelState → `Enum.Parse<PaymentMethodCategory>(model.Category)` → `new CreatePaymentMethodCommand(...)` → Send → RedirectToAction Index; catch `ValidationException` → ModelState errors → View(model); `Deactivate POST(id, companyId)` → Send Deactivate command → Redirect.

### File-scoped namespace rule (CS8955 lesson) + DTO single-definition rule
- Every template file uses FILE-SCOPED namespace (`namespace Foo.Bar;` with trailing semicolon, zero-indent body): PaymentTermType.cs:1, BankCreated.cs:1, PaymentTermController.cs:9, CreatePaymentTermCommand.cs:4, EfPaymentTermRepository.cs:6, PaymentTermConfiguration.cs:5, PaymentTermDto.cs:1, BankDto.cs:1. New files MUST use same form — block-scoped `namespace X { ... }` diverges from codebase style and risks warnings-as-errors friction (TreatWarningsAsErrors=true).
- DTO single-definition (Bank Hierarchy lesson, global MEMORY): ONE record per DTO file. PaymentTermDto.cs holds exactly one record; BankDto.cs holds exactly one record (`Application/Banks/DTOs/BankDto.cs:1-9`). Do NOT co-locate `CreatePaymentMethodResult` or query result types into the DTO file — result records live with their command file (CreatePaymentTermCommand.cs:14 pattern).

### Suggested approach
Copy the 17 PaymentTerm template files 1:1 to PaymentMethod names in the flat Application layout, swapping `PaymentTermType/Days(int?)` for `PaymentMethodCategory/RequiresBankAccount(bool=false)` per Design §2-§3, then apply the 3 wiring lines (Ignore + AddScoped + InternalsVisibleTo decision); discovery-first TDD order: Domain entity+enum+event+port → EF config+repository → commands/validators/queries/DTO → controller+viewmodel, building after each layer.

### Verification criteria (for verifier/auditor)
- Pass: all 15 new files exist at exact paths above with file-scoped namespaces; Application files in FLAT folders (not `Application/PaymentMethods/...`); DTO file holds single record with Category as string; DbContext diff is exactly one `Ignore<PaymentMethodCreated>()` line and no DbSet; DI diff is exactly one AddScoped line; controller has no `Domain.Entities` using (grep); `dotnet build SmeAccounting.sln` 0 warnings; 22/22 arch tests pass.
- Fail: enum in `Domain/Enums/`; feature-folder Application layout; two records in DTO file; block-scoped namespace; DbSet added AND config double-registration conflict; controller referencing Domain.Entities/Ports; validator lengths ≠ 20/200/500 or missing `IsInEnum()`; `BankAccountId` FK added; internal handler tested without InternalsVisibleTo.

### Quality standards
- Good: each new file traceable to its template file:line above with the PaymentTerm→PaymentMethod diff explicit per file (kept vs swapped); wiring diffs are one line each with anchor line numbers (DbContext:87, DI:54, csproj:14).
- Merely functional: file list without template sources — forces executor to re-discover; reject and send back.

## Task-Specific Research — [G2] TDD test plan
### Scope note
- Verified 2026-09-22 by reading `tests/SmeAccounting.BankTests/Fakes.cs:1-37`, `BankAggregateTests.cs:1-123`, `BankTests.csproj:1-23`, `Application/Handlers/CreatePaymentTermHandler.cs:8-30`, `Application/SmeAccounting.Application.csproj:14`, `Domain/Entities/PaymentTerm.cs:7-43`, `Application/Validators/CreatePaymentTermCommandValidator.cs:8-29`, design locks in `docs/PaymentMethod-Design-2026.md` §2-§3/§7/§10. Discovery-first TDD: tests written FIRST against not-yet-existing PaymentMethod types (red), slice implemented to green.
- Design locks assumed: ctor `(companyId,code,name,category,requiresBankAccount=false,description=null)`, enum `PaymentMethodCategory {Cash=0,BankTransfer=1,Card=2,EWallet=3,Other=4}`, `DomainException` on `companyId<=0`/empty Code/Name, `Deactivate()` no event, minimal `PaymentMethodCreated(Id,CompanyId,UtcNow)` event, validator rules CompanyId>0 / Code 20 / Name 200 / `IsInEnum()` / Description 500.

### Where tests live — RECOMMEND: extend BankTests, do NOT create new project
- Add `tests/SmeAccounting.BankTests/PaymentMethodAggregateTests.cs` (new file, ~13 Facts mirroring `BankAggregateTests.cs` shape) + append `FakePaymentMethodRepository` to existing `tests/SmeAccounting.BankTests/Fakes.cs`, reusing `FakeUnitOfWork` as-is (no change needed — `IUnitOfWork` is aggregate-agnostic).
- Why extend: `SmeAccounting.Application.csproj:14` already has `<InternalsVisibleTo Include="SmeAccounting.BankTests" />` and all handlers are `internal sealed` (`CreatePaymentTermHandler.cs:8`) — handler happy-path test compiles with zero csproj edits. BankTests csproj already refs Domain+Application only (`BankTests.csproj:14-17`, xunit 2.9.3 + TestSdk + coverlet) — exact minimal-test pattern from global MEMORY.
- New-project alternative (`tests/SmeAccounting.PaymentMethodTests/`): requires `dotnet new xunit` + `dotnet sln add` + new `InternalsVisibleTo` line in Application csproj — 3 extra churn steps, zero extra isolation benefit (both projects ref Domain+Application only). Reject unless PLAN mandates separate suite.
- Arch-test impact of either choice: NONE. The 22 NetArchTest rules scan `src/` assemblies only (Domain purity + layer coupling); test-project layout changes cannot break them. Regression gate is `dotnet test tests/SmeAccounting.BankTests/` still passing (existing 13 Bank Facts untouched).

### Fakes to add — copy `Fakes.cs:6-26` verbatim, swap Bank→PaymentMethod
```csharp
// Append to tests/SmeAccounting.BankTests/Fakes.cs; reuse FakeUnitOfWork unchanged.
internal sealed class FakePaymentMethodRepository : IPaymentMethodRepository
{
    private readonly List<PaymentMethod> _items = new();
    public Task<PaymentMethod?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));
    public Task<PaymentMethod?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.Code == code && x.CompanyId == companyId));
    public Task<IReadOnlyList<PaymentMethod>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<PaymentMethod>>(_items.Where(x => x.CompanyId == companyId).ToList());
    public Task AddAsync(PaymentMethod m) { _items.Add(m); return Task.CompletedTask; }
    public IReadOnlyList<PaymentMethod> Stored => _items;
}
```
- Mirrors `FakeBankRepository` (List-backed, no EF InMemory package — InMemory ignores unique/FK/xmin per global MEMORY, so hand fake is the sanctioned pattern). Port methods come from `IPaymentMethodRepository` (GetById/GetByCode/GetAllByCompany/AddAsync, no Update/Delete).
- Usings to add in Fakes.cs: `SmeAccounting.Domain.Entities` already present; `SmeAccounting.Domain.Ports` already present — no new usings.

### Failing tests to write FIRST — `PaymentMethodAggregateTests.cs` (~13 Facts)
**Domain ctor (template `BankAggregateTests.cs:10-48`, validation logic `PaymentTerm.cs:21-28`):**
1. `PaymentMethod_Ctor_Valid_RaisesPaymentMethodCreatedWithCompanyId` — arrange: `new PaymentMethod(1,"CASH","Cash",PaymentMethodCategory.Cash)`; act: read `DomainEvents.OfType<PaymentMethodCreated>()`; assert: `CompanyId==1`, `Code=="CASH"`, `IsActive==true`, `RequiresBankAccount==false` (default), `Assert.Single(evt)`, `evt.CompanyId==1`.
2. `PaymentMethod_Ctor_CompanyIdZero_ThrowsDomainException` — arrange: args `(0,"CASH","Cash",Cash)`; act+assert: `Assert.Throws<DomainException>(() => new PaymentMethod(...))`.
3. `PaymentMethod_Ctor_CompanyIdNegative_ThrowsDomainException` — same with `-1` (covers `<=0` branch beyond the zero case).
4. `PaymentMethod_Ctor_EmptyCode_ThrowsDomainException` — arrange `(1, string.Empty, "Cash", Cash)`; assert throws. (Whitespace `"  "` variant optional second fact mirroring `Bank_Ctor_EmptyName` whitespace style at line 37.)
5. `PaymentMethod_Ctor_EmptyName_ThrowsDomainException` — arrange `(1, "CASH", "  ", Cash)`; assert throws.
6. `PaymentMethod_Ctor_InvalidCategory_Caveat` — ⚠️ DEVIATION FLAG: `PaymentTerm.cs:19-28` has NO enum guard (typed enum param is compile-time safe; invalid value only via explicit `(PaymentTermType)999` cast, which the ctor does not reject). Task brief asks "invalid category → DomainException" but the 1:1 PaymentTerm copy will NOT throw. Executor picks one and records it: (a) skip domain invalid-category fact (faithful copy), or (b) add `Enum.IsDefined` guard in ctor (improvement, diverges from template — then fact is `Assert.Throws<DomainException>(() => new PaymentMethod(1,"CASH","Cash",(PaymentMethodCategory)999))`). Recommend (a) + validator `IsInEnum` fact below covers the bad-category path at the Application boundary.
7. `PaymentMethod_Deactivate_SetsIsActiveFalse` — arrange valid instance; act `Deactivate()`; assert `IsActive==false`. Optional extension: assert `DomainEvents.OfType<PaymentMethodDeactivated>()` is empty (locks the no-event rule from Design §5).
8. `PaymentMethod_Ctor_RequiresBankAccountTrue_Persisted` — arrange `(1,"BT","Bank Transfer",BankTransfer, requiresBankAccount: true)`; assert `RequiresBankAccount==true` (locks the bool-over-FK decision; no FK assert needed).

**Validator (template `CreatePaymentTermCommandValidator.cs:8-29`, cases mirror `BankAggregateTests.cs:92-108`):**
9. `CreatePaymentMethodValidator_Valid_Passes` — arrange `new CreatePaymentMethodCommand(1,"CASH","Cash",Cash)` + `new CreatePaymentMethodCommandValidator()`; act `Validate(...)`; assert `result.IsValid`.
10. `CreatePaymentMethodValidator_CompanyIdZero_Fails` — arrange command with `CompanyId: 0`; assert `!result.IsValid`.
11. `CreatePaymentMethodValidator_EmptyCode_Fails` / `EmptyName_Fails` — one fact each (or `[Theory][InlineData]` pair); assert `!result.IsValid`.
12. `CreatePaymentMethodValidator_BadCategory_Fails` — arrange command with `(PaymentMethodCategory)999`; assert `!result.IsValid` (covers `IsInEnum()` rule — the sanctioned bad-category gate given caveat in #6).
13. `CreatePaymentMethodValidator_OverLength_Fails` — `new string('X',21)` Code / `new string('X',201)` Name / `new string('X',501)` Description each fail (locks 20/200/500 lengths; Description needs `Description = ...` named-arg since it is optional-null).

**Handler happy path (template `BankAggregateTests.cs:110-122` + `CreatePaymentTermHandler.cs:13-29`):**
14. `CreatePaymentMethodHandler_HappyPath_AddsAndSaves` — arrange `new FakePaymentMethodRepository()`, `new FakeUnitOfWork()` (reused, not duplicated), `new CreatePaymentMethodHandler(repo, uow)` (internal — compiles via existing InternalsVisibleTo); act `await handler.Handle(new CreatePaymentMethodCommand(1,"CASH","Cash",PaymentMethodCategory.Cash), CancellationToken.None)`; assert `Assert.Single(repo.Stored)`, `repo.Stored[0].Code=="CASH"`, `result.Id == repo.Stored[0].Id`, `uow.SaveCalledCount==1`.
- Optional 15th: `DeactivatePaymentMethodHandler_HappyPath` (GetById→Deactivate→SaveChanges, `InvalidOperationException` on null per `DeactivatePaymentTermHandler` template) — include only if G2 ships the Deactivate handler (file checklist item 10 says yes).

### TDD execution order for executor
1. RED: add `FakePaymentMethodRepository` to Fakes.cs + `PaymentMethodAggregateTests.cs` with all Facts above → `dotnet test tests/SmeAccounting.BankTests/` FAILS to compile (types missing — correct red).
2. GREEN domain: create entity+enum+event+port → domain Facts compile+pass.
3. GREEN application: create commands/validators/queries/handlers/DTO → validator+handler Facts pass (handlers `internal sealed` need no csproj change).
4. FULL GREEN: infra config+repo, DbContext `Ignore<>`, DI `AddScoped`, controller+VM → `dotnet build SmeAccounting.sln` 0 warnings → `dotnet test tests/SmeAccounting.ArchitectureTests/` 22/22 → BankTests all pass (13 old + ~14 new).

### Suggested approach
Extend BankTests with `PaymentMethodAggregateTests.cs` + `FakePaymentMethodRepository` (reuse `FakeUnitOfWork`), writing all ~14 Facts red-first; skip the domain invalid-category fact unless executor adds an `Enum.IsDefined` guard diverging from the PaymentTerm template, covering bad category at the validator `IsInEnum` boundary instead.

### Verification criteria (for verifier/auditor)
- Pass: `Fakes.cs` contains `FakePaymentMethodRepository` with the 4 port methods + `Stored`; `FakeUnitOfWork` untouched/reused; `PaymentMethodAggregateTests.cs` holds domain Facts (zero/negative companyId, empty code/name, Deactivate, Created-event single + CompanyId), validator Facts (0, empty Code/Name, bad-category 999, over-length 21/201/501), handler happy-path Fact asserting `Single(Stored)` + `SaveCalledCount==1`; no new test project, no csproj/sln edits; no EF InMemory package added; `dotnet test tests/SmeAccounting.BankTests/` all green + 22/22 arch pass.
- Fail: new `SmeAccounting.PaymentMethodTests` project without PLAN mandate; `FakeUnitOfWork` duplicated instead of reused; handler tested via EF InMemory instead of hand fake; domain invalid-category fact asserting `DomainException` while ctor is a guard-less PaymentTerm copy (red-forever test); validator lengths ≠ 20/200/500; internal handler tested without InternalsVisibleTo (compile error); existing 13 Bank Facts broken.

### Quality standards
- Good: every fact names the arrange values literally (`(0,...)`, `(PaymentMethodCategory)999`, `new string('X',21)`) so executor writes them without re-reading templates; the #6 caveat is explicit about why bad-category lives at validator not domain; fake code is copy-paste-ready with usings noted as already-present.
- Merely functional: test titles without arrange/act/assert sketches — forces executor to re-derive values from templates; reject and send back.

## Task-Specific Research — [G3] test evidence protocol
### Scope note
- Sources: loop MEMORY [G2]/[G2 verified] lines, global MEMORY (TreatWarningsAsErrors + Bank Hierarchy minimal-test pattern + PaymentMethod Slice 27/27 zero-csproj-edit), TOOLS.md Commands Reference, PLAN.md [G3] text. No web search needed — all gates already defined in-loop.
- Working directory for every command: `/home/projects/sme_acct`. Run in order 1→2→3→4; gate 4 only after 1–3 green (EF reads compiled assemblies; G3 Batch Learnings: build must succeed before migration generation).

### Exact commands (workdir `/home/projects/sme_acct`)
1. `dotnet build SmeAccounting.sln`
2. `dotnet test tests/SmeAccounting.ArchitectureTests/`
3. `dotnet test tests/SmeAccounting.BankTests/`
4. Migration SQL check ONLY after 1–3 green:
   - `dotnet ef migrations list --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
   - `dotnet ef migrations script --idempotent --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api` (read-only check; do NOT `database update` unless PLAN mandates it). If a new `AddPaymentMethod` migration is expected, generation command is `dotnet ef migrations add <DescriptiveName> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api` — descriptive feature name, not per-task numbering (G3 Batch Learnings).

### Expected results
- Cmd 1: `Build succeeded.` + `0 Warning(s)` + `0 Error(s)` (TreatWarningsAsErrors=true; `Directory.Build.props` net10.0/C#13/nullable).
- Cmd 2: `Passed! - Failed: 0, Passed: 22, Skipped: 0, Total: 22` (22 NetArchTest rules: Domain zero NuGet refs, Api→Application→Domain direction, no controller `Domain.Entities` refs).
- Cmd 3: `Passed! - Failed: 0, Passed: 27, Skipped: 0, Total: 27` = 13 pre-existing Bank/Branch/Account Facts untouched + 14 new PaymentMethod Facts (MEMORY [G2]: 13 old + 14 new; zero csproj/sln edits, `FakeUnitOfWork` reused).
- Cmd 4: list shows existing migrations; script output contains `payment_methods` table (PK `id`, snake_case cols incl `category` + `requires_bank_account`, unique `(company_id, code)`, FK `company_id → companies` Restrict, `xmin` rowversion) + correct Down reversal; no `BankAccountId` FK, no stray tables.

### What to record (tail lines, verbatim into executor/verifier evidence)
- Cmd 1: last ~5 lines incl `Build succeeded`, `0 Warning(s)`, `0 Error(s)`, elapsed time.
- Cmd 2: last ~5 lines incl `Passed! - Failed: 0, Passed: 22` + `Total: 22`.
- Cmd 3: last ~5 lines incl `Passed! - Failed: 0, Passed: 27` + `Total: 27`; on any failure also record `Failed: <names>` lines (`Failed <TestName> [...]`).
- Cmd 4: `migrations list` full output (all migration names); `script` excerpt: `CREATE TABLE payment_methods (...)` block + `CREATE UNIQUE INDEX ... (company_id, code)` + `FOREIGN KEY (company_id)` + Down `DROP TABLE payment_methods` block. If no new migration generated yet, record that explicitly (Ignore-only wiring + `ApplyConfigurationsFromAssembly` + `Set<T>` means table appears only after migration is scaffolded — not a failure of cmds 1–3).

### Pre-existing locale warning vs real failure
- Benign (ignore, still PASS): NuGet/SDK locale warning (e.g. locale/encoding notice on restore). Per global MEMORY, `TreatWarningsAsErrors` does NOT promote NuGet package locale warnings to errors — `0 Warning(s) 0 Error(s)` gate still holds; record warning text but do not fail the gate on it.
- Real failure (FAIL): any `error CSxxxx`, `Warning(s): N>0` promoted to error, `Failed: N>0` in either test run, `Build FAILED`, arch-test rule name listed as failed (esp. controller→`Domain.Entities` coupling or Domain NuGet ref), Bank regression break (any of the 13 old Facts failing).

### Bank slice regression scope
- The 13 pre-existing Bank/BankBranch/BankAccount Facts in `tests/SmeAccounting.BankTests/BankAggregateTests.cs` must stay green untouched; PaymentMethod adds `PaymentMethodAggregateTests.cs` (~14 Facts) + `FakePaymentMethodRepository` appended to `Fakes.cs` only. No new test project, no csproj/sln edits, no EF InMemory package (hand List-backed fake is the sanctioned pattern — InMemory ignores unique/FK/xmin). Arch suite unaffected (scans `src/` assemblies only) but must still read 22/22.

### Suggested approach
Run cmds 1→3 in order from `/home/projects/sme_acct`, capture tail lines verbatim; only then run cmd 4 read-only script check for `payment_methods` DDL correctness; treat locale warnings as noise, any Failed>0 or Warning>0-as-error as gate failure with Bank-13-old vs PaymentMethod-14-new split reported.

### Verification Criteria
- Pass: evidence shows `0 Warning(s) 0 Error(s)`, `22/22` arch, `27/27` BankTests (13 old + 14 new split stated), migration script excerpt has `payment_methods` PK/unique/FK-Restrict/xmin/Down-drop with no `BankAccountId` FK; locale warning if present is separately quoted and not counted as failure.
- Fail: any gate count short (build warnings/errors, arch <22, BankTests <27 or any of 13 old failing), missing tail-line evidence, `database update` run without mandate, or locale warning misreported as build failure (or real error dismissed as locale noise).

### Quality Standards
- Good: each command paired with workdir + expected tail text + where it was sourced (MEMORY line / TOOLS command / PLAN gate); Bank-13 vs new-14 split explicit; migration check lists exact DDL tokens to look for (`category`, `requires_bank_account`, `(company_id, code)`, Restrict, `xmin`, Down drop).
- Merely functional: "run build and tests" without exact commands/counts/tail lines — forces verifier to re-derive gates; reject and send back.

## Task-Specific Research — [G3] migration SQL check
### Scope note
- Sources: loop TOOLS.md Commands Reference + global TOOLS.md (dotnet-ef 10.0.12 confirmed LOCAL, not online-only), global MEMORY G3 Batch Learnings (single descriptive migration, build-before-migration, zombie-MSBuild OOM, Down-reversal check), RESEARCH.md PaymentTermConfiguration template (§External Knowledge: ToTable `payment_methods`, unique `(CompanyId,Code)`, Restrict, xmin last) + [G3] test evidence protocol above (cmd 4 read-only). No web search needed — procedure fully defined in-loop.
- No new tools discovered — dotnet-ef 10.0.12 already confirmed installed (`dotnet-ef` command per loop TOOLS.md Global tools). Nothing added to TOOLS.md.

### Context & Prior Work
- PaymentMethod EF config already written per G2: `src/SmeAccounting.Infrastructure/Persistence/Configurations/PaymentMethodConfiguration.cs` (ToTable `payment_methods`, snake_case cols, `category` HasConversion<string>, `requires_bank_account`, unique `(CompanyId,Code)`, Company FK Restrict, xmin last). DbContext wiring is Ignore-only (`modelBuilder.Ignore<PaymentMethodCreated>()`) + `ApplyConfigurationsFromAssembly` auto-applies config + repository uses `Set<T>` — so a fresh migration scaffold picks up `payment_methods` with zero extra wiring.
- Existing migrations: 4 total per loop TOOLS.md (InitialCreate, FixAccountNameColumn, AccountingFoundation, Phase2AccountingControlConfig). New migration file lands in `src/SmeAccounting.Infrastructure/Migrations/<timestamp>_AddPaymentMethod.cs` (+ `.Designer.cs` + updated `SmeAccountingDbContextModelSnapshot.cs`).
- Pre-requisite (G3 Batch Learnings): `dotnet build SmeAccounting.sln` must be GREEN before scaffolding — EF Core reads compiled assemblies. OOM guard: `pkill MSBuild` frees zombie build processes in memory-constrained environments.

### Existing Tools & Resources
- `dotnet-ef 10.0.12` — confirmed LOCAL via loop TOOLS.md Global tools table (`dotnet-ef` command). EF Core 10.0.4 + Npgsql 10.0.3 in Infrastructure, EF Core Design 10.0.12 in Api. No install needed.
- Connection string `src/SmeAccounting.Api/appsettings.json` (`Host=172.21.208.1;...`); `migrations add`/`script` do NOT need a live DB connection (scaffold + SQL render are offline), but `database update` does — which is why update is FORBIDDEN here.

### Requirements & Constraints
- CHECK ONLY. NEVER run `dotnet ef database update` (no DB apply without explicit user approval). Allowed: `migrations add`, `migrations list`, `migrations script`, reading generated `Up()` C# in the migration file.
- All commands from workdir `/home/projects/sme_acct`.

### Suggested Approach
Scaffold `dotnet ef migrations add AddPaymentMethod --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`, then verify via EITHER reading generated `Up()` C# OR `dotnet ef migrations script` SQL output — both must show additive-only `payment_methods` DDL with PK/unique/FK-Restrict/xmin and a clean Down reversal.

### Exact procedure (workdir `/home/projects/sme_acct`, after build+arch+BankTests green)
1. `dotnet ef migrations list --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api` — record baseline list.
2. `dotnet ef migrations add AddPaymentMethod --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api` — descriptive feature name per G3 Batch Learnings (not per-task numbering). Expect output `Done. To undo this action, use 'ef migrations remove'`.
3. Verify Path A (C# — cheapest, preferred): read `src/SmeAccounting.Infrastructure/Migrations/*_AddPaymentMethod.cs` `Up()` method. Must contain exactly one `CreateTable(name: "payment_methods", ...)` + one `CreateIndex(unique on company_id, code)`; `Down()` must contain `DropTable(name: "payment_methods")`.
4. Verify Path B (SQL — either instead of or in addition to A): `dotnet ef migrations script --idempotent --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api` (read-only render; `--idempotent` guards any accidental apply). Look for `CREATE TABLE payment_methods (...)` block + unique index + FK + Down `DROP TABLE payment_methods` block. To scope SQL to just the new migration: `dotnet ef migrations script <PreviousMigrationName> AddPaymentMethod --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`.
5. FORBIDDEN: `dotnet ef database update` under any flag — reject evidence gathered via a live apply; if migration file was scaffolded only for inspection and PLAN does not mandate keeping it, `dotnet ef migrations remove` undoes the scaffold cleanly.

### Expected DDL (pass tokens — from PaymentTermConfiguration template + Design locks)
- Table: `payment_methods` (snake_case, plural). Columns snake_case: `id` (bigint, identity PK), `company_id` (bigint NOT NULL), `code` (varchar(20) NOT NULL), `name` (varchar(200) NOT NULL), `category` (string-converted enum — text/varchar), `requires_bank_account` (boolean NOT NULL), `is_active` (boolean NOT NULL), `description` (varchar(500) nullable), `xmin` (xid row-version, declared last in config).
- `PRIMARY KEY (id)` on `payment_methods`.
- `FOREIGN KEY (company_id) REFERENCES companies(id)` with Restrict semantics — Npgsql Restrict emits NO `ON DELETE CASCADE` clause; absence of CASCADE is the pass signal.
- `CREATE UNIQUE INDEX ... ON payment_methods (company_id, code)`.
- `xmin` concurrency token present.
- Down reversal: `DROP TABLE payment_methods` (+ drop of its unique index) — clean undo, no residue.
- Up() touches NOTHING else: no Alter/Create/Drop on any existing table.

### Reject criteria (any one = FAIL, executor stops, verifier fails the gate)
- R1 destructive ops: `Up()` contains `DropTable`/`DropColumn`/`AlterColumn`/`RenameTable`/`RenameColumn`/`Sql("DROP...")` targeting any EXISTING table (only `CreateTable payment_methods` + its `CreateIndex` allowed).
- R2 missing unique: no unique index/constraint on `(company_id, code)` (Code-alone unique or no unique at all = fail).
- R3 Cascade delete: `ON DELETE CASCADE` anywhere in the new migration's FK (SQL), or `OnDelete(DeleteBehavior.Cascade)` if reading C# (must be Restrict).
- R4 wrong names: table other than `payment_methods`; column other than `category` for the enum (Design UNKNOWN-6 locked to `category`) or other than `requires_bank_account` for the flag; any camelCase identifier (snake_case enforced by EFCore.NamingConventions).
- R5 BankAccountId FK: any `bank_account_id` column/FK on `payment_methods` (bool-over-FK decision — G1/G2 locked, no FK).
- R6 missing xmin: no `xmin` row-version column in CreateTable.
- R7 database applied: evidence shows `database update` was run, or live DB state changed — procedural violation regardless of DDL correctness.

### Verification Criteria
- Pass: tail-line evidence shows scaffold `Done` + file `Migrations/*_AddPaymentMethod.cs` exists; Path A excerpt quotes `CreateTable("payment_methods")` + unique `(CompanyId, Code)` + `OnDelete(Restrict)` + `xmin` + `Down()` DropTable with no other-table ops; and/or Path B excerpt quotes `CREATE TABLE payment_methods`, `UNIQUE (company_id, code)`, `FOREIGN KEY (company_id)`, `xmin`, absence of `ON DELETE CASCADE`, Down `DROP TABLE payment_methods`; explicit statement `database update` NOT run; all R1–R7 checked with verdict per item.
- Fail: any R1–R7 triggered; scaffold skipped with "assumed correct" (no Up()/script excerpt quoted); `database update` run; excerpt shows wrong table/column names, missing unique/xmin, CASCADE, or BankAccountId FK.

### Quality Standards
- Good: each verification item pairs the exact token looked for (`payment_methods`, `category`, `requires_bank_account`, `(company_id, code)`, Restrict-absence-of-CASCADE, `xmin`, Down drop) with the quoted line from Up()/script where it was found; 7 reject criteria reported as individual PASS/FAIL lines so auditor ticks without re-reading the migration.
- Merely functional: "migration looks good" without quoted excerpts or per-criterion verdicts — forces verifier to re-scaffold; reject and send back.
