# Research — Journal Entry Handlers (Create + Post)

## Context & Prior Work

### 1. Current CQRS surface (Application layer)

**Commands** (both exist, NO handlers exist yet):
- `src/SmeAccounting.Application/Commands/CreateJournalEntryCommand.cs`:
  `record CreateJournalEntryCommand(DateTimeOffset Date, long PeriodId, string? Description, string? SourceType, long? SourceId, IReadOnlyList<JournalEntryLineInput> Lines) : IRequest<CreateJournalEntryResult>`
  - `record JournalEntryLineInput(long AccountId, decimal DebitAmount, decimal CreditAmount, string? Description)`
  - `record CreateJournalEntryResult(long Id, string EntryNumber)`
  - **NO CompanyId, NO VoucherTypeId on the command** — see §5 gap.
- `src/SmeAccounting.Application/Commands/PostJournalEntryCommand.cs`:
  `record PostJournalEntryCommand(long JournalEntryId) : IRequest<PostJournalEntryResult>`
  - `record PostJournalEntryResult(long JournalEntryId, DateTimeOffset PostedAt)`
  - **NO PostedBy, NO PostedAt on the command** — handler must source both (IClock + fixed string).

**Validators** (both exist, complete):
- `CreateJournalEntryCommandValidator`: PeriodId > 0; Lines NotEmpty; per-line AccountId > 0. No Date/Description/amount rules.
- `PostJournalEntryCommandValidator`: JournalEntryId > 0.

**Missing:** `CreateJournalEntryHandler`, `PostJournalEntryHandler` — confirmed absent from `Handlers/` (glob + grep).

### 2. Domain entity `JournalEntry` (`src/SmeAccounting.Domain/Entities/JournalEntry.cs`)

- Ctor: `JournalEntry(string entryNumber, DateTimeOffset date, long periodId, string? description = null)` — entryNumber required (`ArgumentNullException` if null). **EntryNumber is NOT generated in domain — caller passes it in.**
- `AddLine(long accountId, Money debit, Money credit, string? description = null, long? departmentId = null, long? costCenterId = null, long? projectId = null)` — throws `DomainException("Cannot modify a posted journal entry.")` if posted. Line ctor takes `entryId = Id` (transient 0 OK).
- `Post(string postedBy, DateTimeOffset postedAt)`:
  - Throws `DomainException("Journal entry is already posted.")` if IsPosted.
  - **Calls `ValidateBalance()` internally** → throws `InvalidPostingRuleException` if totalDebit != totalCredit. **No prior validation needed before Post().**
  - Sets PostedBy, PostedAt, IsPosted=true; raises `JournalEntryPosted(Id, postedAt)` (already ignored in DbContext line 64).
- `SetSource(sourceType, sourceId)`: guards IsPosted / empty sourceType / sourceId<=0. Not needed for the daily-screen flow (controller passes null source).
- `ValidateBalance()`: sums `l.Debit.Amount` vs `l.Credit.Amount`; throws `InvalidPostingRuleException` with entry number in message.
- **JournalEntry has NO CompanyId property** (schema: entry_number, date, period_id, description, source_type, source_id, posted_by, posted_at, is_posted, xmin).
- `BaseEntity.Id` has a **public setter** — tests set persisted Id directly (e.g. `period.Id = 5`).

### 3. Ports & Infrastructure implementations

| Port | Members | Infrastructure impl |
|---|---|---|
| `IJournalEntryRepository` | `GetByIdAsync(long)`, `GetAllAsync()`, `AddAsync(JournalEntry)` | `EfJournalEntryRepository` — GetById **includes Lines**; GetAll AsNoTracking OrderByDescending(Date); AddAsync delegates. Registered. |
| `IUnitOfWork` | `Task<int> SaveChangesAsync(CancellationToken ct = default)` | `SmeAccountingDbContext` itself (`AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<SmeAccountingDbContext>())`). |
| `IClock` | `DateTimeOffset Now { get; }` | `SystemClock` (UtcNow), registered **singleton**. |
| `IPostingService` | `Task PostAsync(JournalEntry entry)` | **⚠ NO IMPLEMENTATION. NOT REGISTERED IN DI.** Dead port. |

**CRITICAL — IPostingService hole:** grep over `src/SmeAccounting.Infrastructure/` finds only the port definition. `DependencyInjection.cs` has no `IPostingService` registration. Precedent: `PostOpeningBalancesHandler` does **not** inject it — it calls `journalEntry.Post(postedBy, postedAt)` directly (OpeningBalancePeriod.PostOpeningBalances → JournalEntry.Post). **Executor must NOT inject IPostingService into PostJournalEntryHandler (DI would fail at runtime).** Either call `entry.Post()` directly (established pattern) or implement+register `EfPostingService` (extra scope).

### 4. Representative Create-handler pattern (exact)

`CreatePaymentMethodHandler` / `CreateCustomerHandler` / `CreateTaxRateHandler` / `CreateDocumentNumberingSeriesHandler` — identical shape:

```csharp
internal sealed class CreateXxxHandler(
    IXxxRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateXxxCommand, CreateXxxResult>
{
    public async Task<CreateXxxResult> Handle(CreateXxxCommand request, CancellationToken cancellationToken)
    {
        var entity = new Xxx(request.CompanyId, ...);          // domain ctor
        await repository.AddAsync(entity);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateXxxResult(entity.Id);
    }
}
```

- Primary-ctor DI, `internal sealed class`, manual result construction, no try/catch (DomainException propagates).
- `InternalsVisibleTo("SmeAccounting.BankTests")` in Application.csproj — internal handlers directly testable.

### 5. Numbering series — and the design gap

- `DocumentNumberingSeries`: `VoucherTypeId`, `CompanyId`, `Prefix`, `NextNumber` (default 1), `PaddingLength` (default 6), `IsDefault`, `IsActive`, `Description`. `Increment()` → NextNumber++. **No formatting method — handler must format `$"{Prefix}{NextNumber:D{PaddingLength}}"`** (e.g. `JNRL000001`).
- `IDocumentNumberingSeriesRepository`: `GetByIdAsync`, **`GetDefaultAsync(long voucherTypeId, long companyId)`** (filters VoucherTypeId + CompanyId + IsDefault), `GetAllByCompanyAsync`, `AddAsync`. `EfDocumentNumberingSeriesRepository` implements it. Registered.
- Usage precedent: `CreateDocumentNumberingSeriesHandler` (plain create), `ResetNumberingSeriesHandler` (GetById → Reset → Save).
- `VoucherType`: `Code`, `Name`, `VoucherCategory` (enum has `Journal`), `CompanyId`, `IsActive`. `IVoucherTypeRepository.GetByCodeAsync(code, companyId)` exists. Registered.
- **⚠ NO SEED DATA:** `SystemSecuritySeed.cs` is a commented template only (no HasData). Intended codes: RCPT/PMT/**JNRL**/ADJ/OPEN (JNRL = Journal). No VoucherType rows exist in DB unless created via application service.
- **⚠ THE GAP:** `CreateJournalEntryCommand` has **no CompanyId** (and no VoucherTypeId), but `GetDefaultAsync(voucherTypeId, companyId)` requires both. The handler cannot resolve the numbering series as-is. Every other Create command in the codebase carries CompanyId. Options for planner/executor:
  1. **Add `CompanyId` to CreateJournalEntryCommand** (+ ViewModel + controller + validator) — consistent with all ~40 other Create commands. Then resolve voucher type by code `"JNRL"` via `IVoucherTypeRepository.GetByCodeAsync(code, companyId)` (throws if null — no seed exists) and series via `GetDefaultAsync(voucherTypeId, companyId)` (throws if null — no series exists).
  2. Fallback numbering without series (e.g. `JE-{date}-{n}`) — deviates from "numbering series wired" in PLAN.
  - Note: JournalEntry has no CompanyId column, so adding CompanyId to the command is Application/Api-only — **no migration needed**.

### 6. Tests — established RED-GREEN pattern

- `tests/SmeAccounting.BankTests/Fakes.cs`:
  - `FakeJournalEntryRepository : IJournalEntryRepository` — **counter-assigned Id in AddAsync** (`entry.Id = _nextId++`) + `Stored` list. MUST implement all 3 port members (GetByIdAsync, GetAllAsync, AddAsync) — copying a smaller fake shape verbatim → CS0535.
  - `FakeUnitOfWork : IUnitOfWork` — `SaveCalledCount` property, returns 1.
  - Also: FakePostingReferenceRepository, FakeOpeningBalancePeriodRepository, FakeBankRepository, FakePaymentMethodRepository.
- `PostingReferenceCqrsTests.cs` — canonical handler-test pattern: validator facts (valid + each invalid case) + handler happy path asserting `repository.Stored` count, stored props, `result.Id == stored[0].Id`, `unitOfWork.SaveCalledCount == 1`. Constructs internal handlers directly (`new CreatePostingReferenceHandler(repo, uow)`).
- `GetJournalEntriesQueryTests.cs` — 3 facts; builds JournalEntry via ctor + AddLine + Post; asserts DTO mapping incl. Lines and posted state.
- `JournalEntrySourceTests.cs` — SetSource domain facts + PostOpeningBalancesHandler facts (2-save pattern, `SaveCalledCount == 2`).
- **Current bank test count: 61 passing** (verified by run). Gate: `bank >= 61` — new tests push above.
- No existing tests exercise CreateJournalEntry/PostJournalEntry handlers (they don't exist yet).

### 7. Controller & ViewModel

- `src/SmeAccounting.Api/Controllers/JournalEntryController.cs`:
  - `Index` → `GetJournalEntriesQuery` (fixed in commit af94908; previously sent GetFiscalPeriodsQuery → 500).
  - `Create` GET → empty VM. `Create` POST → builds `new CreateJournalEntryCommand(model.Date, model.PeriodId, model.Description, null, null, model.Lines)` — **hardcoded null SourceType/SourceId**; catches `ValidationException` → ModelState; redirects to Index.
  - `Post(long id)` → `PostJournalEntryCommand(id)` → RedirectToAction(Index). **No try/catch** — DomainException (already posted / unbalanced) → 500.
- `CreateJournalEntryViewModel`: `Date` (DateTimeOffset, required, DataType.Date), `PeriodId` (long, required), `Description` (max 500), `Lines` (List<JournalEntryLineInput>). **No CompanyId.**
- Views: `Index.cshtml` (list + "Ghi sổ" Post button for unposted rows), `Create.cshtml` (JS line adder posting `Lines[i].AccountId/DebitAmount/CreditAmount/Description`).

### 8. Gotchas / holes executor must handle

1. **IPostingService is a dead port** — no impl, no DI registration. Do not inject it. Call `entry.Post(postedBy, postedAt)` directly (PostOpeningBalancesHandler precedent).
2. **EntryNumber production** — domain does not generate it. Handler must format from numbering series (`Prefix + NextNumber:D{PaddingLength}`) and `Increment()` + Save. Requires companyId + voucherTypeId the command lacks → **command shape change (add CompanyId) is the primary design decision**; voucher type resolution by code "JNRL" needs a null-guard (no seed rows exist).
3. **Post() self-validates balance** — `ValidateBalance()` inside Post() throws `InvalidPostingRuleException`. No prior validation needed. But controller Post action has no try/catch → consider whether handler should translate or let it 500 (existing Create action only catches ValidationException).
4. **postedBy/postedAt sourcing** — PostJournalEntryCommand carries neither. Use `IClock.Now` for postedAt; postedBy must be a fixed string (e.g. `"system"`) or added to the command. Precedent `PostOpeningBalancesCommand(PeriodId, PostedBy, PostedAt)` carries both explicitly.
5. **Money construction** — line inputs are decimal; domain needs `new Money(amount, "VND")` (Money.Zero is VND; currency literal "VND").
6. **JournalEntry ctor requires non-null entryNumber** — ArgumentNullException if null.
7. **FakeJournalEntryRepository assigns Id in AddAsync** — result.Id comes from fake counter; handler tests must use it (not a pre-set value).
8. **No migration needed** — command/ViewModel/controller changes are Application/Api-only; JournalEntryPosted already ignored in DbContext; no schema change.
9. **EfJournalEntryRepository.GetByIdAsync includes Lines** — Post handler load → Post → Save works with tracked entity.
10. **Build gates:** build 0 warnings/0 errors (TreatWarningsAsErrors), arch 22/22, bank ≥ 61 (currently exactly 61).

## Existing Tools & Resources

- No new tools needed. All repos/ports registered in DI except IPostingService (see above).
- CodeGraph: no `.codegraph/` index — grep/glob/read used (per global TOOLS.md).

## Requirements & Constraints

- Handlers must follow the exact internal-sealed primary-ctor pattern of CreatePaymentMethodHandler etc.
- RED-GREEN: write failing tests first (validator + handler facts per PostingReferenceCqrsTests pattern), then implement.
- Gates: build 0/0, arch 22/22, bank ≥ 61.
- No migration, no schema change, no new NuGet packages, no EF InMemory (List-backed fakes).
- Controllers stay thin MediatR dispatch; no Domain.Entities references from Api.
- Domain untouched unless a guard is genuinely needed (prefer handler-level resolution of numbering).

### Detailed Findings — Researcher 2 (Requirements & Constraints, verified against source 2026-09-23)

#### R1. VoucherType entity — full shape, repo, usage, seeding

- **Entity** (`Domain/Entities/VoucherType.cs`): `Code` (string, max 20), `Name` (max 200), `VoucherCategory` (enum, string-stored), `CompanyId` (long, required), `IsActive` (bool, default true), `Description` (nullable, max 500). Private parameterless ctor (EF) + public ctor `(companyId, code, name, voucherCategory, description?)` with DomainException validation (companyId > 0, code/name non-blank). `Deactivate()` → IsActive=false. Raises `VoucherTypeCreated(Id, companyId, UtcNow)` in ctor (provisional Id=0).
- **Port** `IVoucherTypeRepository`: `GetByIdAsync(long)`, `GetByCodeAsync(string code, long companyId)`, `GetAllAsync()`, `AddAsync`. **No GetByCompanyAsync** — `GetVoucherTypesByCompanyHandler` filters `GetAllAsync()` in memory by CompanyId.
- **Code uniqueness is company-scoped**: composite unique index `(CompanyId, Code)` in VoucherTypeConfiguration. Same code valid across different companies. `GetByCodeAsync(code, companyId)` is the correct lookup.
- **CreateVoucherTypeHandler**: plain create (new → AddAsync → Save → return Id). No duplicate pre-check.
- **NO SEED EXISTS**: `SystemSecuritySeed.cs` is a commented template only; grep confirms **zero `HasData` calls anywhere** in the codebase. Intended codes RCPT/PMT/**JNRL**/ADJ/OPEN; `VoucherCategory.Journal` enum value exists. `CreateCompanyWithDefaultsCommandHandler` referenced in a comment but **does not exist**. A fresh DB has **zero voucher_types rows** → `GetByCodeAsync("JNRL", companyId)` returns null → **handler MUST null-guard** (InvalidOperationException/KeyNotFoundException precedent in ResetNumberingSeriesHandler).

#### R2. Numbering series — semantics, persistence, concurrency

- **Entity** (`Domain/Entities/DocumentNumberingSeries.cs`): `VoucherTypeId`, `CompanyId`, `Prefix` (max 20), `NextNumber` (int, default 1), `PaddingLength` (int, default 6), `IsDefault`, `IsActive`, `Description`. `Increment()` → NextNumber++. `Reset(startFrom)` validates ≥ 1. **No formatting method — handler must format `$"{Prefix}{NextNumber:D{PaddingLength}}"`** (e.g. `JNRL000001`).
- **Port** `IDocumentNumberingSeriesRepository`: `GetByIdAsync`, `GetDefaultAsync(voucherTypeId, companyId)` — Ef impl filters `VoucherTypeId == vt && CompanyId == c && IsDefault` (tracked, no AsNoTracking), `GetAllByCompanyAsync` (AsNoTracking), `AddAsync`.
- **Usage precedents**: `GetNumberingSeriesHandler` (GetById → DTO), `GetNumberingSeriesByCompanyHandler` (GetAllByCompanyAsync → DTOs), `ResetNumberingSeriesHandler` (GetById → **null → `InvalidOperationException($"Numbering series with ID {id} not found.")`** → Reset → Save), `CreateDocumentNumberingSeriesHandler` (plain create).
- **Increment() persistence**: via EF change tracking + `IUnitOfWork.SaveChangesAsync` — port has **no UpdateAsync** (ResetNumberingSeriesHandler proves the pattern: mutate tracked entity → Save). Handler flow: load series (tracked) → format number → `Increment()` → build entry → AddAsync → **single SaveChangesAsync** persists series row + entry atomically.
- **Concurrency**: `journal_entries.entry_number` has a **plain (non-unique) index** — DB does NOT enforce EntryNumber uniqueness. The numbering-series row carries an **xmin row version**; two concurrent creates reading the same NextNumber both format the same number, and the second SaveChanges throws `DbUpdateConcurrencyException` on the series row. The series row is the serialization point; there is **no DB-level last-resort uniqueness** on entry_number. Note as risk — do NOT design a fix (out of scope).
- Series uniqueness: unique index `(VoucherTypeId, CompanyId, Prefix)` — one series per prefix per voucher type per company. IsDefault NOT in the unique index (multiple defaults possible at DB level).

#### R3. DB constraints — journal_entries / journal_entry_lines, migrations

- **JournalEntryConfiguration**: table `journal_entries`; PK `id` bigint identity (`ValueGeneratedOnAdd`); `entry_number` varchar(50) required; `date` timestamptz; `period_id` bigint (**plain column — NO FK to fiscal_periods, no HasOne**); `description` varchar(500) nullable; `source_type` varchar(100); `source_id` bigint; `posted_by` varchar(100); `posted_at`; `is_posted` bool; xmin row version. Indexes: `IX_journal_entries_period_id` + `IX_journal_entries_entry_number` — **both NON-unique**. **No CompanyId column on JournalEntry.**
- **JournalEntryLineConfiguration**: table `journal_entry_lines`; PK id identity; `entry_id`; `account_id`; `description`; OwnsOne Money Debit (`debit_amount` numeric, `debit_currency` varchar(3)) + Credit (`credit_amount`, `credit_currency`); nullable `department_id`/`cost_center_id`/`project_id` with SetNull FKs; indexes on EntryId/AccountId/DepartmentId/CostCenterId/ProjectId; xmin. **No FK to journal_entries in current config** (legacy `JournalEntryId` FK from InitialCreate removed by AccountingFoundation migration).
- **Migrations**: `journal_entries` created in InitialCreate (20260916051341); `journal_entry_lines` altered in AccountingFoundation (20260916083803 — dimension FKs added, legacy FK dropped); latest migration `20260922084832_PostingReferenceHarden` (2026-09-22) only adds an FK on `posting_references` referencing `journal_entries` as principal — **journal_entries table itself untouched**. Latest migration timestamp predates this loop (loop dir untracked in git). **CONFIRMED: no schema change needed — all loop changes are Application/Api-level.**

#### R4. Fiscal period integrity — KNOWN GAP, do not design a fix

- `JournalEntry.Post()` checks **only** IsPosted + `ValidateBalance()` (debit == credit). `ValidateBalance()` sums line amounts only. **No period-open check anywhere in the JE create/post flow.**
- `FiscalPeriod` entity has `Status` (`PeriodStatus.Open/Closing/Closed`, default Open), `Open(openedAt)`, `Close(closedAt)`. `PeriodStatus` enum: Open, Closing, Closed.
- `OpenFiscalPeriodCommand(YearId, Month)` exists + `FiscalPeriodController.Open` sends it — **but NO OpenFiscalPeriodHandler exists** (MediatR would throw at runtime; out of scope).
- `OpeningBalancePeriod.PostOpeningBalances` validates its own Status == Open — that is the opening-balance period, NOT the fiscal period.
- **Known constraint gap**: nothing verifies the JournalEntry's PeriodId refers to an Open fiscal period; `period_id` has no FK. Executor must NOT add period-status checks (would need IFiscalPeriodRepository + new port usage — out of scope). Record as gap only.

#### R5. Api create flow — form fields, currency, CompanyId source

- **CreateJournalEntryViewModel**: `Date` (DateTimeOffset, required, DataType.Date, default UtcNow), `PeriodId` (long, required), `Description` (max 500), `Lines` (List<JournalEntryLineInput>). **No CompanyId.**
- **Create.cshtml**: posts `Date` (type=date), `PeriodId` (number input), `Description`, and JS-added `Lines[i].AccountId/DebitAmount/CreditAmount/Description`. **No currency field — currency is hardcoded VND** (domain `Money.Zero` = VND; handler must build `new Money(amount, "VND")`).
- **JournalEntryController.Create POST**: builds `CreateJournalEntryCommand(model.Date, model.PeriodId, model.Description, null, null, model.Lines)` — hardcoded null SourceType/SourceId; catches `ValidationException` → ModelState; redirects Index. `Post(id)`: sends `PostJournalEntryCommand(id)` — **no try/catch** (DomainException/InvalidPostingRuleException → 500).
- **CompanyId source: NONE in Api layer.** Grep confirms **no HttpContext / ClaimsPrincipal / session / company filter** in any controller. Every other controller takes CompanyId from its ViewModel (`model.CompanyId`). JournalEntry flow must add CompanyId to ViewModel + view (hidden field or number input — no precedent view exists; JournalEntry views are the only MVC views in the Api project). No auth middleware → no current-user resolution available.
- **Index.cshtml** (daily screen): table of EntryNumber, Date, Description, status badge (Đã ghi sổ / Chưa ghi sổ), PostedAt, and a "Ghi sổ" Post button per unposted row (`asp-action="Post" asp-route-id="@entry.Id"`).

#### R6. Validators — exact rules, OpenFiscalPeriod relation

- **CreateJournalEntryCommandValidator EXISTS**: `PeriodId > 0`; `Lines NotEmpty`; per-line `AccountId > 0`. **NO rules on Date, Description, DebitAmount, CreditAmount** — a line with both amounts 0 passes validation; **balance is NOT validated at Create** (domain ctor + AddLine don't check) — an unbalanced entry CAN be persisted and only fails at Post(). Existing behavior — do not change.
- **PostJournalEntryCommandValidator EXISTS**: `JournalEntryId > 0`.
- **OpenFiscalPeriodCommand** exists but has no handler and no relation to the create flow (Create takes PeriodId as free text). Nothing to wire.

#### R7. Test conventions — PostingReferenceCqrsTests + JournalEntrySourceTests

- **Validator facts**: `new XxxValidator()` → `ValidateAsync(command)` → `Assert.True/False(result.IsValid)`; one fact per invalid case (zero/empty/too-long).
- **Handler happy path**: construct internal handler directly with fakes (`new CreatePostingReferenceHandler(repo, uow)`), `Handle(command, CancellationToken.None)`, then assert:
  - `Assert.Single(repository.Stored)` (or `Stored.Count`)
  - stored entity props (e.g. `Stored[0].SourceType`)
  - `Assert.Equal(repository.Stored[0].Id, result.Id)`
  - `Assert.Equal(1, unitOfWork.SaveCalledCount)`
- **JournalEntrySourceTests** (PostOpeningBalancesHandler): 2-save pattern asserts `Assert.Equal(2, unitOfWork.SaveCalledCount)`; `Assert.Single(journalEntryRepository.Stored)`; `stored.IsPosted`; `Assert.True(pr.JournalEntryId > 0)`.
- **GetJournalEntriesQueryTests**: builds JournalEntry via ctor + AddLine + Post; asserts DTO mapping incl. Lines and posted state.
- **Fakes.cs**: `FakeJournalEntryRepository` — counter Id in AddAsync (`entry.Id = _nextId++`), `Stored` list, implements all 3 port members. `FakeUnitOfWork` — `SaveCalledCount`, returns 1. **⚠ NO FakeVoucherTypeRepository or FakeDocumentNumberingSeriesRepository exist yet — executor must add them** (List-backed; GetByCodeAsync/GetDefaultAsync filter pattern per FakeBankRepository/FakePaymentMethodRepository; Stored list).

#### R8. Result Id — AddAsync → Save → return entity.Id (confirmed safe)

- `CreatePaymentMethodHandler` / `CreateVoucherTypeHandler` / `CreateDocumentNumberingSeriesHandler` all: `new Entity(...)` → `AddAsync` → `SaveChangesAsync` → `return new Result(entity.Id)`. In production, EF assigns Id at SaveChanges (identity); with FakeJournalEntryRepository, Id is assigned **in AddAsync** (counter). Either way `entity.Id` is valid at return time — **handlers can return entity.Id before/after SaveChangesAsync in the calling pattern**. For `CreateJournalEntryResult(Id, EntryNumber)`: EntryNumber is known pre-save (formatted from series); Id from entity post-AddAsync. Test assertion `result.Id == stored[0].Id` works with the fake.

#### R9. Executor must-respect checklist

1. **VoucherType code "JNRL"** (VoucherCategory.Journal) resolved via `GetByCodeAsync(code, companyId)` — company-scoped; **null-guard required** (no seed rows exist).
2. **CompanyId plumbing** — command + validator + ViewModel + view + controller (5 places). No claims/session — form field. JournalEntry entity itself has NO CompanyId column — command-level only.
3. **No schema change** — journal_entries untouched since InitialCreate/AccountingFoundation; latest migration 2026-09-22 predates loop.
4. **EntryNumber uniqueness NOT DB-enforced** (plain index) — numbering series is the only guard; series-row xmin is the concurrency serialization point; single SaveChangesAsync persists entry + series increment atomically.
5. **Currency hardcoded VND** — no currency field in form; `new Money(amount, "VND")`.
6. **Validator doesn't check amounts** — unbalanced entries persist at Create; balance enforced only at Post (ValidateBalance inside Post). Existing behavior, don't change.
7. **No period-open check** in JE flow — known gap, do NOT design fix.
8. **IPostingService dead port** — call `entry.Post(postedBy, postedAt)` directly.
9. **postedBy/postedAt**: PostJournalEntryCommand carries neither — use `IClock.Now` for postedAt; postedBy fixed string (e.g. `"system"`) or add to command (PostOpeningBalancesCommand precedent carries both explicitly).
10. **New fakes needed**: FakeVoucherTypeRepository + FakeDocumentNumberingSeriesRepository (don't exist).
11. **FakeJournalEntryRepository assigns Id in AddAsync** — `result.Id == stored[0].Id` assertion works.
12. **Controller Post action no try/catch** — DomainException → 500. Existing behavior.

## Suggested Approach

1. Add `CompanyId` to `CreateJournalEntryCommand` (+ ViewModel + controller + validator) — the minimal command-shape change that makes numbering-series resolution possible.
2. `CreateJournalEntryHandler(IVoucherTypeRepository, IDocumentNumberingSeriesRepository, IJournalEntryRepository, IUnitOfWork)`: resolve voucher type by code "JNRL" → `GetDefaultAsync(voucherTypeId, companyId)` → format entry number → `new JournalEntry(number, date, periodId, description)` → AddLine per input (Money VND) → AddAsync → Save → return `(entry.Id, entry.EntryNumber)`.
3. `PostJournalEntryHandler(IJournalEntryRepository, IUnitOfWork, IClock)`: GetById (throw if null) → `entry.Post("system", clock.Now)` → Save → return `(id, postedAt)`.
4. Tests: validator facts + handler happy-path facts with FakeJournalEntryRepository/FakeUnitOfWork (+ fake voucher-type/series repos if resolved in handler).

## Verification Criteria

- `dotnet build SmeAccounting.sln`: 0 warnings, 0 errors.
- `dotnet test tests/SmeAccounting.ArchitectureTests/`: 22/22.
- `dotnet test tests/SmeAccounting.BankTests/`: ≥ 61 (new facts for both handlers + validators).
- New handler tests assert: Stored entry has formatted EntryNumber, balanced lines persisted, SaveCalledCount == 1 (Create); IsPosted true, PostedAt set, SaveCalledCount == 1 (Post); result.Id == stored[0].Id.
- Controller Create POST still compiles with new command shape (CompanyId wired from ViewModel).
- No new migration files; no Domain/Infrastructure schema changes.

## Quality Standards

- Follow the exact handler shape of CreatePaymentMethodHandler (primary ctor, internal sealed, no try/catch, manual result).
- Entry number format consistent with series: `$"{Prefix}{NextNumber:D{PaddingLength}}"`; series Increment() before/with Save.
- Null guards for voucher-type/series lookups throw meaningful exceptions (KeyNotFoundException/InvalidOperationException precedent in ResetNumberingSeriesHandler).
- Do NOT touch IPostingService (dead port) — call Post() directly.
- Do NOT add CompanyId to JournalEntry entity (no schema change; command-level only).
- Tests use List-backed fakes only; no EF InMemory.

## Task-Specific Research — [G1] CompanyId plumbing

### G1-1. Exact current content of the 5 target files (source-verified 2026-09-23)

**`src/SmeAccounting.Application/Commands/CreateJournalEntryCommand.cs`** (20 lines):
```csharp
public record CreateJournalEntryCommand(
    DateTimeOffset Date,
    long PeriodId,
    string? Description,
    string? SourceType,
    long? SourceId,
    IReadOnlyList<JournalEntryLineInput> Lines) : IRequest<CreateJournalEntryResult>;

public record JournalEntryLineInput(long AccountId, decimal DebitAmount, decimal CreditAmount, string? Description);
public record CreateJournalEntryResult(long Id, string EntryNumber);
```
- CompanyId goes FIRST: `record CreateJournalEntryCommand(long CompanyId, DateTimeOffset Date, long PeriodId, ...)`.

**`src/SmeAccounting.Application/Validators/CreateJournalEntryCommandValidator.cs`** (22 lines): rules `PeriodId > 0` ("Period ID is required."), `Lines NotEmpty`, per-line `AccountId > 0`. **English messages** — matches PaymentMethod validator style. Add `RuleFor(x => x.CompanyId).GreaterThan(0).WithMessage("Company ID is required.")` — verbatim identical to `CreatePaymentMethodCommandValidator.cs:10-11`.

**`src/SmeAccounting.Api/ViewModels/CreateJournalEntryViewModel.cs`** (22 lines): `Date` (`[Required(ErrorMessage = "Ngày hạch toán là bắt buộc")] [DataType(DataType.Date)] [Display(Name = "Ngày hạch toán")]`), `PeriodId` (`[Required(ErrorMessage = "Kỳ kế toán là bắt buộc")] [Display(Name = "Kỳ kế toán")]`), `Description` (`[StringLength(500)] [Display(Name = "Diễn giải")]`), `Lines`. **Vietnamese Display names + Vietnamese ErrorMessages** — local style. Task literal: `[Required] long CompanyId` + `Display("Mã công ty")`. Local-style enhancement (optional): `[Required(ErrorMessage = "Mã công ty là bắt buộc")]`. Place as FIRST property (matches command first-param).

**`src/SmeAccounting.Api/Views/JournalEntry/Create.cshtml`** (75 lines): form `asp-action="Create" method="post"` + `asp-validation-summary="ModelOnly"`. Fields in order: Date (`type="date"`), PeriodId (`<input asp-for="PeriodId" class="form-control" />` — **no type attr**), Description. Then lines table + JS `addLine()` posting `Lines[i].AccountId/DebitAmount/CreditAmount/Description` (inputs use `type="number"`, `step="0.01"` for amounts). **NO hidden inputs anywhere. NO company field.** `_ValidationScriptsPartial` + jQuery in Scripts section. Tag helpers available (`_ViewImports.cshtml` has `@addTagHelper *, Microsoft.AspNetCore.Mvc.TagHelpers`). Task: add `<input asp-for="CompanyId" class="form-control" type="number" />` — **first field in form** (before Date) matches "FIRST" convention; `type="number"` explicit per task ("required number input").

**`src/SmeAccounting.Api/Controllers/JournalEntryController.cs` Create POST** (lines 30-50): `if (!ModelState.IsValid) return View(model);` → try `new CreateJournalEntryCommand(model.Date, model.PeriodId, model.Description, null, null, model.Lines)` → `_mediator.Send(command, ct)` → `RedirectToAction(nameof(Index))`; catch `ValidationException` → `ModelState.AddModelError` per error → `View(model)`. Change to: `new CreateJournalEntryCommand(model.CompanyId, model.Date, model.PeriodId, model.Description, null, null, model.Lines)`.

### G1-2. CompanyId precedent in other ViewModels/views/controllers

- **`CreatePaymentMethodViewModel.cs`** (canonical master-data VM): `[Required] public long CompanyId { get; set; }` — plain `[Required]`, no Display, **FIRST property**. Same in `CreateCustomerViewModel.cs`.
- **`CreateAccountViewModel.cs`**: `[Required(ErrorMessage = "CompanyId là bắt buộc")] [Display(Name = "CompanyId")] public long CompanyId { get; set; }` — only VM with Display, but English "CompanyId" (task wants Vietnamese "Mã công ty" — matches JournalEntry VM's Vietnamese Display style).
- **⚠ NO view in the entire Api project renders a CompanyId input** (grep `Views/` for `CompanyId` = 0 hits). `ChartOfAccounts/Create.cshtml` has CompanyId in its VM but **omits the input** → form posts CompanyId=0 (broken pattern — do NOT copy). **JournalEntry/Create.cshtml will be the FIRST view with a CompanyId input** — no view-level precedent exists; follow the task spec (visible number input, not hidden).
- **Controller precedent** (`PaymentMethodController.cs:39-45`): `new CreatePaymentMethodCommand(model.CompanyId, model.Code, ...)` — `model.CompanyId` as FIRST arg. Redirect uses `new { companyId = model.CompanyId }` (JournalEntry redirects to Index without companyId — keep existing redirect, out of scope).

### G1-3. CompanyId ordering in Create commands — FIRST is the dominant convention

- Grep `long CompanyId,` over `Commands/Create*Command.cs`: **30 of 32** Create commands have CompanyId as FIRST param (line 6-13). Exceptions: `CreateVoucherTypeCommand` (4th), `CreateAccountCommand` (4th). Task says FIRST — matches the dominant convention. `CreatePaymentMethodCommand`/`CreateCustomerCommand` are the canonical examples.

### G1-4. CreateJournalEntryCommand call sites — exactly 2, both in the 5-file list

- Grep whole repo: code references ONLY in `CreateJournalEntryCommandValidator.cs:6` and `JournalEntryController.cs:38`. **No tests reference it** (no test-file hits). **No handler exists yet** (G2 creates it). Remaining hits are docs/loop-stack markdown (non-code). → The 5-file change surface is complete; **no other call sites to update**. G2's handler will be the 3rd call site (constructed in G2, not now).

### G1-5. Form structure details + gotchas

- No hidden inputs, no company field, no currency field (VND hardcoded). Labels render via `asp-for` + Display attributes automatically.
- `[Required]` on non-nullable `long` is a **no-op for client/server validation** (long never null) — the real guard is the validator's `GreaterThan(0)` (server-side, via ValidationBehavior pipeline). Empty number input on POST → model binds CompanyId=0 → validator rejects. This matches how PeriodId already works.
- Validator message style: English ("Period ID is required.") — use "Company ID is required." (verbatim PaymentMethod).
- VM Display style: Vietnamese ("Kỳ kế toán") — `Display(Name = "Mã công ty")` per task.
- No migration, no Domain/Infrastructure edits — command/VM/view/controller only (JournalEntry entity has no CompanyId column; command-level only, per RESEARCH §5/R9.2).

### G1-6. Verification criteria (from PLAN + this research)

- `dotnet build SmeAccounting.sln`: 0 warnings/0 errors (TreatWarningsAsErrors — record positional args must match new signature exactly).
- `dotnet test tests/SmeAccounting.ArchitectureTests/`: 22/22 (no new refs; Api still references Application only).
- `dotnet test tests/SmeAccounting.BankTests/`: **still 61** — no behavior change; no test touches CreateJournalEntryCommand yet (validator rule addition is untested until G2 adds validator facts).
- No migration files; no Domain/Infrastructure file changes (git diff scope check).

## Task-Specific Research — [G2] CreateJournalEntryHandler

### G2-1. IVoucherTypeRepository + VoucherType + VoucherCategory (source-verified 2026-09-23)

**`src/SmeAccounting.Domain/Ports/IVoucherTypeRepository.cs`** (11 lines) — **4 members, ALL must be implemented by the fake**:
```csharp
Task<VoucherType?> GetByIdAsync(long id);
Task<VoucherType?> GetByCodeAsync(string code, long companyId);   // companyId param CONFIRMED
Task<IReadOnlyList<VoucherType>> GetAllAsync();
Task AddAsync(VoucherType voucherType);
```
⚠ MEMORY:254 lesson: FakeVoucherTypeRepository must implement **GetAllAsync too** — copying FakeBankRepository shape verbatim (which lacks GetAllAsync) → CS0535.

**`src/SmeAccounting.Domain/Entities/VoucherType.cs`** (40 lines): `Code` (string), `Name`, `VoucherCategory` (enum), `CompanyId` (long), `IsActive` (bool, default true), `Description` (string?). Public ctor `(long companyId, string code, string name, VoucherCategory voucherCategory, string? description = null)` — DomainException guards (companyId>0, code/name non-blank). Raises VoucherTypeCreated(Id=0, companyId, UtcNow) in ctor — harmless in fakes (no event handling).

**`src/SmeAccounting.Domain/ValueObjects/VoucherCategory.cs`** (10 lines): `enum VoucherCategory { Receipt, Payment, Journal, Adjustment, Opening }` — **`Journal` member EXISTS** (value 2). Test needs `using SmeAccounting.Domain.ValueObjects;` to construct `new VoucherType(1, "JNRL", "Journal", VoucherCategory.Journal)`.

### G2-2. IDocumentNumberingSeriesRepository + DocumentNumberingSeries (source-verified)

**`src/SmeAccounting.Domain/Ports/IDocumentNumberingSeriesRepository.cs`** (11 lines) — **4 members, ALL required by fake**:
```csharp
Task<DocumentNumberingSeries?> GetByIdAsync(long id);
Task<DocumentNumberingSeries?> GetDefaultAsync(long voucherTypeId, long companyId);  // CONFIRMED exact signature
Task<IReadOnlyList<DocumentNumberingSeries>> GetAllByCompanyAsync(long companyId);
Task AddAsync(DocumentNumberingSeries series);
```
⚠ Fake must implement **GetAllByCompanyAsync** too (FakeBankRepository lacks it — CS0535 if copied verbatim).

**`src/SmeAccounting.Domain/Entities/DocumentNumberingSeries.cs`** (55 lines): `VoucherTypeId`, `CompanyId`, `Prefix` (string), `NextNumber` (int, **default 1**), `PaddingLength` (int, **default 6**), `IsDefault` (bool), `IsActive`, `Description`. Public ctor `(long companyId, long voucherTypeId, string prefix, int paddingLength = 6, bool isDefault = false, string? description = null)`. `Increment()` → `NextNumber++` (line 39-42). **No formatting method** — handler formats `$"{Prefix}{NextNumber:D{PaddingLength}}"` → with Prefix="JNRL", NextNumber=1, PaddingLength=6 → **"JNRL000001"** (D6 pads to 6 digits). Test asserts `Stored[0].EntryNumber == "JNRL000001"` and `seriesRepo.Stored[0].NextNumber == 2` (fake stores same object reference; handler's Increment() mutates it).

### G2-3. FakeBankRepository pattern — exact style to copy (Fakes.cs:6-26)

```csharp
internal sealed class FakeBankRepository : IBankRepository
{
    private readonly List<Bank> _banks = new();
    public Task<Bank?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_banks.FirstOrDefault(b => b.Code == code && b.CompanyId == companyId));
    public Task AddAsync(Bank bank) { _banks.Add(bank); return Task.CompletedTask; }
    public IReadOnlyList<Bank> Stored => _banks;
}
```
Style: `internal sealed class`, `private readonly List<T> _items = new();`, `Task.FromResult(FirstOrDefault(...))` filters, `AddAsync` adds + `Task.CompletedTask`, `public IReadOnlyList<T> Stored => _items;`. **New fakes:**
- `FakeVoucherTypeRepository : IVoucherTypeRepository` — GetByCodeAsync filters `Code == code && CompanyId == companyId`; + GetByIdAsync + **GetAllAsync** + AddAsync + Stored.
- `FakeDocumentNumberingSeriesRepository : IDocumentNumberingSeriesRepository` — GetDefaultAsync filters `VoucherTypeId == voucherTypeId && CompanyId == companyId && IsDefault`; + GetByIdAsync + **GetAllByCompanyAsync** + AddAsync + Stored.
- `FakeUnitOfWork` (Fakes.cs:112-121): `SaveCalledCount` property, `SaveChangesAsync` increments + returns 1. Already exists — reuse.
- `FakeJournalEntryRepository` (Fakes.cs:69-88): counter Id in AddAsync (`entry.Id = _nextId++`), Stored. Already exists — reuse. `result.Id == Stored[0].Id` works.

### G2-4. Handler constructor injection + InternalsVisibleTo (confirmed)

- `SmeAccounting.Application.csproj:14`: `<InternalsVisibleTo Include="SmeAccounting.BankTests" />` — internal handler directly testable, **zero csproj edits**.
- Handler shape (CreatePaymentMethodHandler.cs:8-29): `internal sealed class XxxHandler(...primary ctor params...) : IRequestHandler<Command, Result>` + `Handle(Command request, CancellationToken cancellationToken)`.
- G2 handler ctor: `(IVoucherTypeRepository voucherTypeRepository, IDocumentNumberingSeriesRepository numberingSeriesRepository, IJournalEntryRepository journalEntryRepository, IUnitOfWork unitOfWork)` — 4 params, order per PLAN.
- Required usings in handler: `MediatR`, `SmeAccounting.Application.Commands`, `SmeAccounting.Domain.Entities` (JournalEntry), `SmeAccounting.Domain.Ports`, `SmeAccounting.Domain.ValueObjects` (Money).

### G2-5. ResetNumberingSeriesHandler — null-guard + mutate-tracked-entity precedent (read fully, 25 lines)

```csharp
var series = await repository.GetByIdAsync(request.SeriesId);
if (series is null)
    throw new InvalidOperationException($"Numbering series with ID {request.SeriesId} not found.");
series.Reset(request.StartFrom);
await unitOfWork.SaveChangesAsync(cancellationToken);
```
- Null-guard style: `InvalidOperationException` with descriptive message. G2 mirrors: voucherType null → `InvalidOperationException`; series null → `InvalidOperationException`.
- **No UpdateAsync on port** — mutate tracked entity → single SaveChangesAsync persists. G2: series.Increment() mutates tracked series; single SaveChangesAsync persists series + entry atomically (R2 confirmed).

### G2-6. Validator invocation in tests — DIRECT, not pipeline (PostingReferenceCqrsTests.cs:11-54)

```csharp
var validator = new CreatePostingReferenceCommandValidator();
var result = await validator.ValidateAsync(new CreatePostingReferenceCommand(1, 7, "OpeningBalance", 9));
Assert.True(result.IsValid);
```
- **Tests call validator directly** — ValidationBehavior auto-pipeline NOT exercised in unit tests. One fact per invalid case, `Assert.False(result.IsValid)`.
- G2 validator facts (PLAN): valid (CompanyId 1, PeriodId 1, 1+ lines) → True; CompanyId 0 → False; PeriodId 0 → False; empty Lines → False. Command ctor: `new CreateJournalEntryCommand(companyId, date, periodId, description, null, null, lines)` — SourceType/SourceId null OK (record positional).
- Current validator (post-G1, 25 lines): CompanyId > 0 ("Company ID is required."), PeriodId > 0, Lines NotEmpty, per-line AccountId > 0. **No Date/Description/amount rules** — don't add.

### G2-7. Money — confirmed (ValueObjects/Money.cs:10-14)

`public Money(decimal amount, string currency)` — currency null-guard via ArgumentNullException. `Money.Zero => new(0m, "VND")`. Handler: `new Money(line.DebitAmount, "VND")` / `new Money(line.CreditAmount, "VND")`. Test-side precedent (GetJournalEntriesQueryTests.cs:17): `first.AddLine(101, new Money(10m, "VND"), new Money(0m, "VND"))`.

### G2-8. CreatePaymentMethodHandler — canonical shape (read fully, 30 lines)

```csharp
internal sealed class CreatePaymentMethodHandler(
    IPaymentMethodRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreatePaymentMethodCommand, CreatePaymentMethodResult>
{
    public async Task<CreatePaymentMethodResult> Handle(CreatePaymentMethodCommand request, CancellationToken cancellationToken)
    {
        var paymentMethod = new PaymentMethod(request.CompanyId, ...);
        await repository.AddAsync(paymentMethod);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreatePaymentMethodResult(paymentMethod.Id);
    }
}
```
No try/catch (DomainException propagates), manual result construction, primary ctor.

### G2-9. Current command/entity state (post-G1, source-verified)

- **CreateJournalEntryCommand.cs** (21 lines): `record CreateJournalEntryCommand(long CompanyId, DateTimeOffset Date, long PeriodId, string? Description, string? SourceType, long? SourceId, IReadOnlyList<JournalEntryLineInput> Lines) : IRequest<CreateJournalEntryResult>`; `record JournalEntryLineInput(long AccountId, decimal DebitAmount, decimal CreditAmount, string? Description)`; `record CreateJournalEntryResult(long Id, string EntryNumber)`.
- **JournalEntry.cs** (84 lines): ctor `(string entryNumber, DateTimeOffset date, long periodId, string? description = null)` — entryNumber ArgumentNullException if null. `AddLine(long accountId, Money debit, Money credit, string? description = null, long? departmentId = null, long? costCenterId = null, long? projectId = null)` — line ctor takes `entryId = Id` (transient 0 OK). **No SetSource call in G2 plan** (controller passes null source).
- **JournalEntryLine.cs**: `Debit`/`Credit` are `Money` (Amount + Currency).

### G2-10. Test file structure + RED mechanics

- **BankTests.csproj** (23 lines): refs Domain + Application only; xunit 2.9.3; global `Using Include="Xunit"`. Zero csproj edits needed.
- **New file** `tests/SmeAccounting.BankTests/CreateJournalEntryHandlerTests.cs` — usings: `SmeAccounting.Application.Commands`, `SmeAccounting.Application.Handlers`, `SmeAccounting.Application.Validators`, `SmeAccounting.Domain.Entities`, `SmeAccounting.Domain.ValueObjects` (VoucherCategory for fake setup). Class `public sealed class CreateJournalEntryHandlerTests`.
- **RED**: fakes + tests compile against existing ports/entities fine; handler test file references `CreateJournalEntryHandler` which doesn't exist → **CS0246 compile error** (handler missing). Validator facts would pass if reached — compile error blocks all. Record actual error code + lines (MEMORY:254: don't force predicted code).
- **Happy-path test sketch** (from PLAN):
  ```csharp
  var vtRepo = new FakeVoucherTypeRepository();
  await vtRepo.AddAsync(new VoucherType(1, "JNRL", "Journal", VoucherCategory.Journal));
  var seriesRepo = new FakeDocumentNumberingSeriesRepository();
  await seriesRepo.AddAsync(new DocumentNumberingSeries(1, vtRepo.Stored[0].Id, "JNRL", paddingLength: 6, isDefault: true));
  var jeRepo = new FakeJournalEntryRepository();
  var uow = new FakeUnitOfWork();
  var handler = new CreateJournalEntryHandler(vtRepo, seriesRepo, jeRepo, uow);
  var result = await handler.Handle(new CreateJournalEntryCommand(1, TestDate, 1, "desc", null, null,
      [new JournalEntryLineInput(101, 100m, 0m, null), new JournalEntryLineInput(102, 0m, 100m, null)]), CancellationToken.None);
  Assert.Equal("JNRL000001", jeRepo.Stored[0].EntryNumber);
  Assert.Equal(2, seriesRepo.Stored[0].NextNumber);
  Assert.Equal(jeRepo.Stored[0].Id, result.Id);
  Assert.Equal(1, uow.SaveCalledCount);
  ```
- **Null-guard facts**: (a) only series in repo (no voucher type) → `Assert.ThrowsAsync<InvalidOperationException>`; (b) only voucher type (no default series) → InvalidOperationException. Note: series ctor needs voucherTypeId — use any long (e.g. 1) for the missing-voucher-type case; for missing-series case use the real voucherType.Id.
- **Gates**: build 0/0, arch 22/22, bank ≥ 61 (currently exactly 61; G2 adds ~7 facts → 68).

### G2-11. Executor checklist (from PLAN + verified source)

1. Fakes: `FakeVoucherTypeRepository` (4 members incl. GetAllAsync) + `FakeDocumentNumberingSeriesRepository` (4 members incl. GetAllByCompanyAsync) appended to Fakes.cs — style per G2-3.
2. New tests file per G2-10: 4 validator facts + 1 happy path + 2 null-guards = 7 facts.
3. Run `dotnet test tests/SmeAccounting.BankTests/` → record compile-error RED (CS0246 handler missing).
4. GREEN: `src/SmeAccounting.Application/Handlers/CreateJournalEntryHandler.cs` — internal sealed, primary ctor (4 repos), GetByCodeAsync("JNRL", request.CompanyId) → null-guard → GetDefaultAsync(voucherType.Id, request.CompanyId) → null-guard → `$"{series.Prefix}{series.NextNumber:D{series.PaddingLength}}"` → series.Increment() → `new JournalEntry(entryNumber, request.Date, request.PeriodId, request.Description)` → foreach line AddLine(AccountId, new Money(DebitAmount,"VND"), new Money(CreditAmount,"VND"), Description) → AddAsync → **single** SaveChangesAsync → `new CreateJournalEntryResult(entry.Id, entry.EntryNumber)`.
5. Gates: build 0/0, arch 22/22, bank green (61 + 7 = 68).

## Prior Attempt Analysis

- No prior executor attempts in this loop (STATUS.md: planning in progress, 0 attempts).
- Related prior work: commit af94908 fixed Index (GetJournalEntriesQuery + handler + 3 tests, bank 61/61) — the read side is done; this loop completes the write side (Create/Post handlers).
- Global MEMORY lessons directly applicable: transient Id=0 pattern (AddLine with entry Id 0 fine), fakes must simulate EF identity (counter Id in AddAsync), RED-reconstruction canon (revert production file only), no-migration evidence (Migrations count + latest timestamp + zero new files).