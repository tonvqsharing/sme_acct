# Loop Plan
## Mode
build
## Goal
Phase 2 — Accounting Control & Posting Configuration: implement Journal/Voucher Type, Document Numbering Series, Posting Profile/Configuration, Transaction Reason, and Opening Balance Mapping on top of Phase 1 Accounting Foundation.
## Stop Condition
all tasks in loop-stack/accounting-control-config/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks

### [x] [G1] Task 1 — Voucher Type Domain + Infrastructure

**Slice:** Journal / Voucher Type
**Depends on:** nothing (foundation for all subsequent slices)

Create domain entity, enum, repository port, EF configuration, repository implementation, and DI registration.

**Domain layer:**
- `VoucherType` entity in `Domain/Entities/VoucherType.cs` — inherits `BaseEntity`
  - Properties: `Id`, `Code` (string, max 20, required), `Name` (string, max 200, required), `VoucherCategory` (enum: Receipt/Payment/Journal/Adjustment/Opening), `CompanyId` (long, FK to Company), `IsActive` (bool, default true), `Description` (string?, max 500)
  - Invariants: Code must not be empty (throw `ArgumentNullException`), CompanyId > 0 (throw `ArgumentOutOfRangeException`), `Deactivate()` sets IsActive=false
- `VoucherCategory` enum in `Domain/Enums/VoucherCategory.cs` — Receipt, Payment, Journal, Adjustment, Opening (stored as string in DB)
- `IVoucherTypeRepository` port in `Domain/Ports/IVoucherTypeRepository.cs` — `GetByIdAsync(long)`, `GetByCodeAsync(string code, long companyId)`, `GetAllAsync()`, `AddAsync(VoucherType)`

**Infrastructure layer:**
- `VoucherTypeConfiguration` in `Persistence/Configurations/VoucherTypeConfiguration.cs` — table `voucher_types`, unique index on `(CompanyId, Code)`, Company FK Restrict, xmin concurrency token
- `EfVoucherTypeRepository` in `Persistence/Repositories/EfVoucherTypeRepository.cs`
- Add `DbSet<VoucherType> VoucherTypes` to `SmeAccountingDbContext`
- Register `IVoucherTypeRepository` in `ServiceCollectionExtensions`

**Verification:**
- `dotnet build SmeAccounting.sln` passes
- `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22 tests pass
- Entity follows existing patterns (BaseEntity, xmin, snake_case table, Company FK Restrict)

---

### [G2] Task 2 — Document Numbering Series Domain + Infrastructure

**Slice:** Document Numbering Series
**Depends on:** Task 1 (references VoucherType)

Create domain entity, repository port, EF configuration, repository, and DI.

**Domain layer:**
- `DocumentNumberingSeries` entity in `Domain/Entities/DocumentNumberingSeries.cs` — inherits `BaseEntity`
  - Properties: `Id`, `VoucherTypeId` (long, FK to VoucherType), `CompanyId` (long, FK to Company), `Prefix` (string, max 20), `NextNumber` (int, default 1), `PaddingLength` (int, default 6), `IsDefault` (bool, default false), `IsActive` (bool, default true), `Description` (string?, max 500)
  - Invariants: NextNumber must be >= 1, PaddingLength 1-10, CompanyId > 0, `Increment()` advances NextNumber by 1, `Reset(int startFrom)` resets NextNumber
- `IDocumentNumberingSeriesRepository` port — `GetByIdAsync(long)`, `GetDefaultAsync(long voucherTypeId, long companyId)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(DocumentNumberingSeries)`

**Infrastructure layer:**
- `DocumentNumberingSeriesConfiguration` — table `document_numbering_series`, unique index on `(VoucherTypeId, CompanyId, Prefix)`, Company FK Restrict, VoucherType FK Restrict, xmin
- `EfDocumentNumberingSeriesRepository`
- Add DbSet, register port

**Verification:**
- Build passes, 22 arch tests pass
- Concurrency: xmin token present, Increment() is safe to call in optimistic concurrency flow

---

### [G2] Task 3 — Transaction Reason Domain + Infrastructure

**Slice:** Transaction Reason
**Depends on:** Task 1 (references VoucherType)

Create domain entity, repository port, EF configuration, repository, and DI.

**Domain layer:**
- `TransactionReason` entity in `Domain/Entities/TransactionReason.cs` — inherits `BaseEntity`
  - Properties: `Id`, `Code` (string, max 20, required), `Name` (string, max 200, required), `VoucherTypeId` (long, FK to VoucherType), `CompanyId` (long, FK to Company), `IsActive` (bool, default true), `Description` (string?, max 500)
  - Invariants: Code/Name not empty, CompanyId > 0
- `ITransactionReasonRepository` port — `GetByIdAsync(long)`, `GetByCodeAsync(string code, long companyId)`, `GetAllByVoucherTypeAsync(long voucherTypeId)`, `AddAsync(TransactionReason)`

**Infrastructure layer:**
- `TransactionReasonConfiguration` — table `transaction_reasons`, unique index on `(CompanyId, Code)`, Company FK Restrict, VoucherType FK Restrict, xmin
- `EfTransactionReasonRepository`
- Add DbSet, register port

**Verification:**
- Build passes, 22 arch tests pass

---

### [G3] Task 4 — Posting Configuration Domain + Infrastructure

**Slice:** Posting Profile / Accounting Posting Configuration
**Depends on:** Task 1 (VoucherType), existing Account entity

Create domain entity that maps voucher types to debit/credit account pairs, plus all infrastructure.

**Domain layer:**
- `PostingConfiguration` entity in `Domain/Entities/PostingConfiguration.cs` — inherits `BaseEntity`
  - Properties: `Id`, `VoucherTypeId` (long, FK to VoucherType), `DebitAccountId` (long, FK to Account), `CreditAccountId` (long, FK to Account), `CompanyId` (long, FK to Company), `TransactionReasonId` (long?, FK to TransactionReason — nullable for default posting rules), `DisplayOrder` (int, default 0), `IsActive` (bool, default true), `Description` (string?, max 500)
  - Invariants: DebitAccountId != CreditAccountId (throw `DomainException`), CompanyId > 0, both accounts must belong to same company
- `IPostingConfigurationRepository` port — `GetByIdAsync(long)`, `GetAllByVoucherTypeAsync(long voucherTypeId, long companyId)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(PostingConfiguration)`

**Infrastructure layer:**
- `PostingConfigurationConfiguration` — table `posting_configurations`, composite index on `(VoucherTypeId, TransactionReasonId)`, Company/Account/VoucherType FKs Restrict, xmin
- `EfPostingConfigurationRepository`
- Add DbSet, register port

**Verification:**
- Build passes, 22 arch tests pass
- Domain invariant: debit != credit enforced in entity constructor/method

---

### [G3] Task 5 — Opening Balance Mapping Domain + Infrastructure

**Slice:** Opening Balance Mapping
**Depends on:** Task 1 (VoucherType), existing Account/FiscalPeriod entities

Create entity that maps opening balance accounts for fiscal year transitions.

**Domain layer:**
- `OpeningBalanceMapping` entity in `Domain/Entities/OpeningBalanceMapping.cs` — inherits `BaseEntity`
  - Properties: `Id`, `CompanyId` (long, FK to Company), `VoucherTypeId` (long, FK to VoucherType — the voucher type used for opening balance entries), `DebitAccountId` (long, FK to Account), `CreditAccountId` (long, FK to Account), `IsActive` (bool, default true), `Description` (string?, max 500)
  - Invariants: DebitAccountId != CreditAccountId (throw `DomainException`), CompanyId > 0
- `IOpeningBalanceMappingRepository` port — `GetByIdAsync(long)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(OpeningBalanceMapping)`

**Infrastructure layer:**
- `OpeningBalanceMappingConfiguration` — table `opening_balance_mappings`, unique index on `(CompanyId, VoucherTypeId, DebitAccountId, CreditAccountId)`, Company/VoucherType/Account FKs Restrict, xmin
- `EfOpeningBalanceMappingRepository`
- Add DbSet, register port

**Verification:**
- Build passes, 22 arch tests pass

---

### [G4] Task 6 — Application Layer: Commands + Queries for All 5 Slices

**Slice:** All 5 slices — Application layer
**Depends on:** Tasks 1-5 (all domain + infra complete)

Create MediatR commands, queries, DTOs, validators, and handlers for all 5 domains. One task to wire the full CQRS surface.

**VoucherType:**
- Commands: `CreateVoucherTypeCommand(Code, Name, VoucherCategory, CompanyId, Description?)` → `CreateVoucherTypeResult(long Id)`
- Commands: `DeactivateVoucherTypeCommand(VoucherTypeId)` → `DeactivateVoucherTypeResult`
- Queries: `GetVoucherTypeQuery(VoucherTypeId)` → `VoucherTypeDto?`
- Queries: `GetVoucherTypesByCompanyQuery(CompanyId)` → `IReadOnlyList<VoucherTypeDto>`
- Validators: `CreateVoucherTypeCommandValidator` — Code not empty, Name not empty, CompanyId > 0

**DocumentNumberingSeries:**
- Commands: `CreateDocumentNumberingSeriesCommand(VoucherTypeId, CompanyId, Prefix, PaddingLength, IsDefault, Description?)` → `CreateDocumentNumberingSeriesResult(long Id)`
- Commands: `ResetNumberingSeriesCommand(SeriesId, StartFrom)` → `ResetNumberingSeriesResult`
- Queries: `GetNumberingSeriesQuery(SeriesId)` → `DocumentNumberingSeriesDto?`
- Queries: `GetNumberingSeriesByCompanyQuery(CompanyId)` → `IReadOnlyList<DocumentNumberingSeriesDto>`
- Validators: `CreateDocumentNumberingSeriesCommandValidator`

**TransactionReason:**
- Commands: `CreateTransactionReasonCommand(Code, Name, VoucherTypeId, CompanyId, Description?)` → `CreateTransactionReasonResult(long Id)`
- Commands: `DeactivateTransactionReasonCommand(ReasonId)` → `DeactivateTransactionReasonResult`
- Queries: `GetTransactionReasonQuery(ReasonId)` → `TransactionReasonDto?`
- Queries: `GetTransactionReasonsByVoucherTypeQuery(VoucherTypeId)` → `IReadOnlyList<TransactionReasonDto>`
- Validators: `CreateTransactionReasonCommandValidator`

**PostingConfiguration:**
- Commands: `CreatePostingConfigurationCommand(VoucherTypeId, DebitAccountId, CreditAccountId, CompanyId, TransactionReasonId?, Description?)` → `CreatePostingConfigurationResult(long Id)`
- Commands: `DeactivatePostingConfigurationCommand(ConfigId)` → `DeactivatePostingConfigurationResult`
- Queries: `GetPostingConfigurationQuery(ConfigId)` → `PostingConfigurationDto?`
- Queries: `GetPostingConfigurationsByCompanyQuery(CompanyId)` → `IReadOnlyList<PostingConfigurationDto>`
- Validators: `CreatePostingConfigurationCommandValidator` — DebitAccountId != CreditAccountId, CompanyId > 0

**OpeningBalanceMapping:**
- Commands: `CreateOpeningBalanceMappingCommand(CompanyId, VoucherTypeId, DebitAccountId, CreditAccountId, Description?)` → `CreateOpeningBalanceMappingResult(long Id)`
- Commands: `DeactivateOpeningBalanceMappingCommand(MappingId)` → `DeactivateOpeningBalanceMappingResult`
- Queries: `GetOpeningBalanceMappingQuery(MappingId)` → `OpeningBalanceMappingDto?`
- Queries: `GetOpeningBalanceMappingsByCompanyQuery(CompanyId)` → `IReadOnlyList<OpeningBalanceMappingDto>`
- Validators: `CreateOpeningBalanceMappingCommandValidator` — DebitAccountId != CreditAccountId

**DTOs (records):**
- `VoucherTypeDto`, `DocumentNumberingSeriesDto`, `TransactionReasonDto`, `PostingConfigurationDto`, `OpeningBalanceMappingDto`

**Verification:**
- Build passes, 22 arch tests pass
- All validators follow existing FluentValidation pattern
- No handler references Infrastructure (clean architecture)
- All commands have matching validators registered via DI

---

### [G5] Task 7 — EF Migration + Integration Verification

**Slice:** Database migration + full build verification
**Depends on:** Tasks 1-6 (all domain, infra, and app layers complete)

Create EF Core migration, apply to database, and run final verification.

**Steps:**
- `dotnet ef migrations add Phase2AccountingControlConfig --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- Verify migration file contains all 5 new tables with correct snake_case names, FKs, indexes, and xmin
- `dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- `dotnet build SmeAccounting.sln` — zero warnings, zero errors
- `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 pass

**Verification:**
- Migration applies cleanly to PostgreSQL
- All 5 new tables exist: `voucher_types`, `document_numbering_series`, `transaction_reasons`, `posting_configurations`, `opening_balance_mappings`
- Unique indexes enforced at DB level
- Full solution builds with TreatWarningsAsErrors=true
- Architecture tests: 22/22 pass
