# Research — Canonical PostingReference Row for OpeningBalance Flow

**Loop:** opening-balance-pr-link
**Date:** 2026-09-23
**Focus:** Context & Prior Work — canonical PostingReference row for OpeningBalance flow

## Context & Prior Work

### Design-doc lineage (binding)

- `docs/OpeningBalance-Persist-Design-2026.md` §1 decision (:10): JE-persist-first — `journalEntryRepository.AddAsync(journalEntry)` then existing `unitOfWork.SaveChangesAsync`; EF assigns JE Id during Save, so JE Id > 0 before any PR link (satisfies PostingReference ctor V2 guard). §5 no-touch (:77): **"PR creation lives in CreatePostingReferenceHandler/CreatePostingReferenceCommand (separate command). The design §7 same-UoW atomic write (JE + canonical posting_references row) is a SEPARATE future task"** — THIS loop is that task.
- `docs/PostingReference-Design-2026.md` §7 timing (:97): "reference row created post-JE-persist when the JE id is assigned — reconciles journalEntryId > 0 / sourceId > 0 guards with the transient-Id=0 pattern". §7 (:95-96): posting_references is **canonical** (idempotency + audit); JE SourceType/SourceId are read-model cache only; "Both written atomically in the same UoW/handler that persists the JE". §9 item 3 (:116): discarded-JE bug was excluded → fixed by persist loop → PR link now unblocked.
- Prior loop `opening-balance-persist_DONE` (MEMORY.md:4, :13): handler now has 3rd ctor param `IJournalEntryRepository` appended end; JE persisted before Save; PR creation explicitly deferred to this loop.

### PostingReference entity — exact ctor + guards

`src/SmeAccounting.Domain/Entities/PostingReference.cs` (33 lines):

- **Ctor `PostingReference(long companyId, long journalEntryId, string sourceType, long sourceId)`** (:15) — CompanyId-first 4-param, exactly as PLAN goal states.
- Guards (all `DomainException`, V1–V4 per design §5):
  - V1 `companyId <= 0` → "CompanyId must be greater than zero." (:17-18)
  - **V2 `journalEntryId <= 0` → "JournalEntryId must be greater than zero." (:19-20)** — the forcing guard: PR cannot be built until JE Id assigned post-Save.
  - V3 `string.IsNullOrWhiteSpace(sourceType)` → "SourceType is required." (:21-22)
  - V4 `sourceId <= 0` → "SourceId must be greater than zero." (:23-24)
- `PostingReferenceCreated` event raised in ctor (:31) — minimal payload (PostingReferenceId, CompanyId, occurredOn), no SourceType/SourceId/JournalEntryId duplication (verified by test PostingReferenceAggregateTests.cs:58-69).
- Private parameterless ctor for EF (:13). No navigation properties.

### SourceType enum — DOES NOT EXIST

- `grep "enum SourceType|SourceTypeEnum" src` = 0 hits. SourceType is a **free string** (design §9 item 5: "keep free string max100 + empty/whitespace guard only").
- Sole `"OpeningBalance"` literal in src: `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:81` (`journalEntry.SetSource("OpeningBalance", Id)`). Design E1 (:22): exactly 1 live SourceType.
- PR SourceType column width: `varchar(100)` (PostingReferenceConfiguration.cs:24-27, `IsRequired().HasMaxLength(100)`).

### IPostingReferenceRepository port — exact signatures

`src/SmeAccounting.Domain/Ports/IPostingReferenceRepository.cs` (10 lines):

- `Task<PostingReference?> GetByIdAsync(long id)` (:7)
- `Task<PostingReference?> GetBySourceAsync(string sourceType, long sourceId, long companyId)` (:8) — triple (SourceType, SourceId, CompanyId)
- `Task AddAsync(PostingReference reference)` (:9)

Ef impl `src/SmeAccounting.Infrastructure/Repositories/EfPostingReferenceRepository.cs`: GetByIdAsync :14-18, GetBySourceAsync :20-24, AddAsync :26-29 (delegates to DbSet, no SaveChanges — UoW owns save).

**DI already registered**: `DependencyInjection.cs:69` `services.AddScoped<IPostingReferenceRepository, EfPostingReferenceRepository>();` — zero DI churn for this loop.

### PostOpeningBalancesHandler — current state

`src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs` (28 lines, `internal sealed`, primary ctor):

- Ctor (:7-10): `(IOpeningBalancePeriodRepository periodRepository, IUnitOfWork unitOfWork, IJournalEntryRepository journalEntryRepository)` — 3 params.
- Flow: `GetByIdAsync(request.PeriodId)` (:17-18) → `period.PostOpeningBalances(...)` (:20) → `journalEntryRepository.AddAsync(journalEntry)` (:22) → `unitOfWork.SaveChangesAsync` (:24) → `return new PostOpeningBalancesResult(true)` (:26).
- **`period.CompanyId` IS in scope**: `period` is `OpeningBalancePeriod` (public `CompanyId` property, OpeningBalancePeriod.cs:9). Handler can build PR with `period.CompanyId` directly — no chain hops needed (design E3 rationale for direct CompanyId).
- **`period.Id` is real** in this path: loaded via GetByIdAsync; domain fail-fast `if (Id <= 0) throw` at OpeningBalancePeriod.cs:76-77 runs before JE construction — so `period.Id > 0` guaranteed when handler reaches PR build.
- **`journalEntry.Id` is real only AFTER :24** (EF assigns identity PK during SaveChangesAsync). PR build must be placed after :24, before return :26.

### PR-link insertion shape (timing-forced two-save)

- Save 1 (:24) persists JE + period flags, assigns `journalEntry.Id`.
- Then build `new PostingReference(period.CompanyId, journalEntry.Id, "OpeningBalance", period.Id)` — all 4 guards pass (CompanyId>0, JE Id>0 post-save, SourceType non-empty, period.Id>0).
- Then `postingReferenceRepository.AddAsync(reference)` + a **second** `unitOfWork.SaveChangesAsync` — PR row cannot ride save 1 (JE Id doesn't exist until save 1 completes). Two saves, same UoW (same DbContext), same handler — matches design §7 "same UoW/handler" + "post-JE-persist when the JE id is assigned". This two-save shape is inherent to the timing constraint; planner should lock it explicitly.

### CreatePostingReferenceHandler — canonical PR-build pattern

`src/SmeAccounting.Application/Handlers/CreatePostingReferenceHandler.cs` (32 lines):

- Ctor `(IPostingReferenceRepository repository, IUnitOfWork unitOfWork)` (:8-10).
- **Duplicate pre-check**: `GetBySourceAsync(request.SourceType, request.SourceId, request.CompanyId)` → throws `InvalidOperationException` "Posting reference for source ... already exists." if non-null (:17-19). Design §7: app pre-check is fast-path only; unique index `(CompanyId, SourceType, SourceId)` is the backstop.
- Build: `new PostingReference(request.CompanyId, request.JournalEntryId, request.SourceType, request.SourceId)` (:21-25).
- `AddAsync` (:27) → `SaveChangesAsync` (:28) → return `reference.Id` (:30).
- Command `CreatePostingReferenceCommand(CompanyId, JournalEntryId, SourceType, SourceId)` record (:5-9); validator CreatePostingReferenceCommandValidator.cs: CompanyId>0, JournalEntryId>0, SourceType NotEmpty+Max100, SourceId>0.
- Controller `PostingReferenceController.cs`: Create POST (:31-51) → `RedirectToAction(nameof(Details), new { id = result.Id })` (:43) — redirect on Send-result Id, not input-model FK (posting-reference-harden G3 lesson, global MEMORY:247).

**Decision for planner**: does PostOpeningBalancesHandler replicate the GetBySourceAsync pre-check + InvalidOperationException, or rely on the in-memory `IsPosted` guard (OpeningBalancePeriod.cs:61-62) + unique index backstop? CreatePostingReferenceHandler precedent does the pre-check; the OpeningBalance flow's period-level IsPosted guard already prevents double-posting within the app. Either is defensible — flag for planner/auditor.

### SetSource duplicate-link question — NO conflict

- `OpeningBalancePeriod.cs:81` `journalEntry.SetSource("OpeningBalance", Id)` sets JE.SourceType/SourceId — read-model cache on `journal_entries` (nullable varchar(100) columns, InitialCreate).
- PR row = canonical persistence on `posting_references` (unique (CompanyId, SourceType, SourceId)).
- Design §1 Option A (:15) explicitly: "JournalEntry.SourceType/SourceId stay as origin-trace cache (read model) only, written atomically in the same UoW/handler that persists the JE." Both are now written in PostOpeningBalancesHandler — complementary layers, not duplicate. SetSource is domain metadata; PR is canonical audit/idempotency row. No conflict, no change to SetSource.

### Tests — existing PR-link coverage

`tests/SmeAccounting.BankTests/` (57/57 green per persist loop):

- **PostingReferenceCqrsTests.cs** (130 lines, 9 facts): validator facts (:12-63), handler happy path (:66-78 — asserts `Stored` Single, SourceType, `Stored[0].Id == result.Id`, `SaveCalledCount == 1`), duplicate-triple throws (:81-92), GetById/GetBySource handler null-passthrough (:95-129). Uses `new PostingReference(1, 7, "OpeningBalance", 9)` literal throughout.
- **PostingReferenceAggregateTests.cs** (70 lines, 6 facts): ctor valid + all 4 guards + event minimal payload.
- **PostingReferenceRepositoryTests.cs** (30 lines, 2 facts): GetBySourceAsync empty-store null + triple-match after Add.
- **Fakes.cs `FakePostingReferenceRepository`** (:50-67): List-backed, `GetByIdAsync`/`GetBySourceAsync`/`AddAsync`/`Stored` — exact port shape, **already exists, no new fake needed**.
- **FakeUnitOfWork** (:110-118): `SaveCalledCount` + `SaveChangesAsync` → `Task.FromResult(1)` — counts saves; a second SaveChangesAsync in the handler will make `SaveCalledCount == 2` in new tests.
- **JournalEntrySourceTests.cs** — will need edits when handler gains 4th ctor param:
  - fact (h) :176 `new PostOpeningBalancesHandler(periodRepository, unitOfWork, journalEntryRepository)` — ctor call site.
  - fact (i) :193-197 reflection asserts ctor has `IJournalEntryRepository` param; :202 ctor call site; :210-214 asserts Stored JE.
  - New PR-link facts will follow the fact (i) shape: set `period.Id = 1` (BaseEntity.Id public setter, per setsource-caller-fix lesson), run handler, assert `postingReferenceRepository.Stored` Single with CompanyId==period.CompanyId, JournalEntryId==stored JE Id, SourceType=="OpeningBalance", SourceId==period.Id, and `unitOfWork.SaveCalledCount == 2`.

### No-touch surface (zero schema/DI/EF churn)

- **No migration**: `posting_references` table + `company_id` + unique (CompanyId, SourceType, SourceId) index + dual Restrict FKs exist since `20260922084832_PostingReferenceHarden` (PostingReferenceConfiguration.cs:32-44). PR row creation touches zero schema.
- **No DI change**: IPostingReferenceRepository registered (DependencyInjection.cs:69).
- **No EF config / DbContext change**: PostingReferenceConfiguration.cs untouched.
- **No new command/handler/controller**: PR creation is handler-internal (design §7 same-UoW atomic write), NOT a new MediatR command — CreatePostingReferenceCommand already exists for the manual path.
- **No domain change**: SetSource (:81) and PostOpeningBalances stay untouched.

## Existing Tools & Resources

- `FakePostingReferenceRepository` (Fakes.cs:50-67) — ready to use, exact port shape.
- `FakeUnitOfWork` (Fakes.cs:110-118) — SaveCalledCount tracks saves.
- `FakeJournalEntryRepository` (Fakes.cs:69-86) — List-backed, GetByIdAsync/GetAllAsync/AddAsync/Stored.
- `FakeOpeningBalancePeriodRepository` (Fakes.cs:88-108) — GetByIdAsync + Stored.
- EfPostingReferenceRepository (Infrastructure/Repositories/) — production impl, registered.
- No new NuGet, no new MCP, no new skill needed. CodeGraph not indexed (global TOOLS.md:174).

## Requirements & Constraints

- PR built with `period.CompanyId` (direct, in scope), `journalEntry.Id` (post-save, >0), `"OpeningBalance"`, `period.Id` (>0 guaranteed by domain fail-fast :76-77).
- PR AddAsync must come AFTER first SaveChangesAsync (:24) — JE Id assigned there; V2 guard `journalEntryId > 0` forces the ordering.
- Same UoW: PR persisted via the handler's existing `unitOfWork` (second SaveChangesAsync), never a second DbContext.
- Handler ctor: 4th param `IPostingReferenceRepository` appended at end (backwards-compatible expansion pattern, global MEMORY:74).
- Gates: `dotnet build` 0 warnings/0 errors (TreatWarningsAsErrors); BankTests ≥ 57 + new facts; ArchitectureTests 22/22 (test-project changes never affect count).
- No migration, no DI, no EF config, no controller, no new command — no-touch list per design §5 + this loop's scope.
- No VAS / Circular 99 compliance claims (design E9: reference shape is integrity decision, not regulatory mandate).

### Decision inputs — R-prefixed findings (2026-09-23, second research pass)

**R1 — Duplicate pre-check (the flagged open question).** Both options' failure behavior, verified against source:
- Precedent: `CreatePostingReferenceHandler.cs:17-19` — `GetBySourceAsync(request.SourceType, request.SourceId, request.CompanyId)`; non-null → `throw new InvalidOperationException($"Posting reference for source '{request.SourceType}' with ID {request.SourceId} already exists.")`. Pre-check runs BEFORE build/Add/save (:21-28). That handler has NO domain guard — caller supplies arbitrary CompanyId/JournalEntryId/SourceType/SourceId, so the pre-check is its only duplicate defense.
- OpeningBalance flow already has the domain guard: `OpeningBalancePeriod.cs:61-62` — `PostOpeningBalances` throws `DomainException("Opening balances are already posted.")` if `IsPosted`, BEFORE any JE/PR creation. Handler loads period via GetByIdAsync (:17-18) → a second POST on a posted period dies at :61-62 regardless of any pre-check.
- Sequential duplicate (period already posted): Option B (no pre-check) → DomainException :61-62, pre-persistence, clean. Option A pre-check at handler start would throw InvalidOperationException ONLY if a stale PR row exists (period posted before PR-link existed); otherwise it adds a redundant round-trip and changes the exception type for the same condition.
- Concurrent race (two POSTs, both load IsPosted=false): pre-check is TOCTOU-ineffective — both pass it before either saves. Real backstops, in order: (1) **xmin concurrency token on the period row** — second request's save 1 (UPDATE period + INSERT JE) hits DbUpdateConcurrencyException, so JE_B never persists; (2) **unique index (CompanyId, SourceType, SourceId)** — last-resort DbUpdateException for any path bypassing the period update (e.g. manual CreatePostingReferenceCommand). Verified: xmin on all entities (AGENTS.md), period row modified by PostOpeningBalances (:90-91) so it IS part of save 1.
- Option A placement hazard: if pre-check placed after save 1 (the natural "before PR build" spot), a throw leaves the JE already committed with no PR row — dangling-JE partial state. To avoid that it must go at handler start (:17), where it's redundant with IsPosted.
- **Input for planner:** Option B is the stronger choice — IsPosted guard (sequential) + xmin (race, catches at save 1 before JE persists) + unique index (last resort) already layer the protection; Option A adds a round-trip, is TOCTOU-ineffective, and risks dangling JE if misplaced. Decision rests with planner/auditor; either is defensible per prior research (:73).

**R2 — Two-save shape + return value.** `PostOpeningBalancesCommand.cs:5-8` `IRequest<PostOpeningBalancesResult>`; `:10` `PostOpeningBalancesResult(bool Success)`. Handler returns `new PostOpeningBalancesResult(true)` (:26) — **Success bool only; no JE Id, no period Id**. PR link does NOT change the return value. No controller exists for this command (grep `PostOpeningBalances` in src = validator + handler + command only) → Api needs nothing; a future controller wanting JE Id is a separate out-of-scope change. Two-save shape confirmed: save 1 (:24) assigns JE.Id (EF identity PK, persist-loop-proven); build PR; AddAsync; save 2. Same UoW = same DbContext, but **two SaveChanges = two DB transactions** — design §7 "atomic" means same-DbContext, not single-transaction. Residual risk: save-2 failure leaves save-1 committed (JE without PR); realistic race is caught at save 1 by xmin, so this is theoretical for this flow. Flag for planner.

**R3 — companyId.** `OpeningBalancePeriod.CompanyId` at `OpeningBalancePeriod.cs:9` — `public long CompanyId { get; private set; }`, non-nullable `long`. Ctor guard `companyId <= 0` → DomainException (:22-23), set :27. Handler's `period` comes from GetByIdAsync (:17-18) → real CompanyId in scope, direct use, no chain hops. ✓

**R4 — Test surface + CRITICAL enabler.** New fact shape feasible: set `period.Id = 1` (BaseEntity.Id public setter, `BaseEntity.cs:7`), run handler, assert `postingReferenceRepository.Stored` Single {CompanyId==period.CompanyId, JournalEntryId==stored JE Id, SourceType=="OpeningBalance", SourceId==period.Id}, `unitOfWork.SaveCalledCount == 2`. `period.Id` in handler == test-set period.Id: FakeOpeningBalancePeriodRepository is list-backed (Fakes.cs:88-108) → GetByIdAsync returns the SAME instance → same object, Id=1 set by test. ✓
- **CRITICAL: `FakeJournalEntryRepository.AddAsync` (Fakes.cs:79-83) does NOT assign Ids** — it just adds to the list. In the fake path `journalEntry.Id` stays 0 after AddAsync → PR ctor V2 guard (`PostingReference.cs:19-20`, `journalEntryId <= 0` → DomainException) throws → the new PR-link fact FAILS at runtime. **The fake MUST be modified to assign an Id on AddAsync** (simulate EF identity assignment, e.g. counter-based) — this is a required test-enabler, in scope (Fakes.cs is a test file). Safe for existing facts: the only JE Id==0 assert is fact G2-3 (`JournalEntrySourceTests.cs:166`) on the domain-created JE BEFORE the handler — unaffected. Existing facts (h) :176 and (i) :202 ctor calls → CS1729 compile-error RED when 4th param lands (persist-loop G3 mechanism, global MEMORY:254).

**R5 — Scope boundary.** No changes to: CreatePostingReferenceHandler.cs, CreatePostingReferenceCommand.cs, PostingReferenceController.cs, EF configs, DbContext, DI, migrations. No new command. Touched files only: `PostOpeningBalancesHandler.cs` (4th ctor param + PR build/Add/save-2) + tests (`JournalEntrySourceTests.cs` new facts + ctor-call updates, `Fakes.cs` Id-assignment enabler).

**R6 — Unique-index backstop verified.** `20260922084832_PostingReferenceHarden.cs:24-28` — `IX_posting_references_company_id_source_type_source_id`, unique, columns (company_id, source_type, source_id); mirrored in `PostingReferenceConfiguration.cs:33-34`. Migrations dir = 35 files (17 migrations × 2 + snapshot), latest 20260922084832 predates this loop → no-migration evidence baseline established.

## Suggested Approach

1. TDD RED: add PR-link facts to JournalEntrySourceTests.cs (or new test file) — handler ctor gains 4th param → existing fact (h)/(i) ctor calls CS1729 (compile-error RED, same mechanism as persist loop G3); new facts assert PR row shape + SaveCalledCount==2.
2. GREEN: append `IPostingReferenceRepository` to handler ctor; after :24 build PR, AddAsync, second SaveChangesAsync; update fact (h)/(i) ctor calls.
3. Verify: build 0/0, BankTests green, arch 22/22, no-migration evidence (Migrations count 35 = 17×2 + snapshot, latest 20260922084832 predates loop commits, zero NEW).

## Verification Criteria

Passing looks like:
- Handler ctor `(IOpeningBalancePeriodRepository, IUnitOfWork, IJournalEntryRepository, IPostingReferenceRepository)` — 4 params, new one appended end.
- After first SaveChangesAsync: `new PostingReference(period.CompanyId, journalEntry.Id, "OpeningBalance", period.Id)` → `postingReferenceRepository.AddAsync(reference)` → second `unitOfWork.SaveChangesAsync`.
- New test asserts: `postingReferenceRepository.Stored` Single; CompanyId == period.CompanyId; JournalEntryId == stored JE Id (>0); SourceType == "OpeningBalance"; SourceId == period.Id; `unitOfWork.SaveCalledCount == 2`.
- Build 0 warnings/0 errors; BankTests all green; ArchitectureTests 22/22.
- No migration scaffolded (Migrations dir count unchanged, latest timestamp predates loop commits); no DI/EF/controller/command changes.

Failing looks like:
- PR built BEFORE first SaveChangesAsync (JE Id still 0 → V2 DomainException at runtime, or test asserts Id==0).
- PR AddAsync without a second save (PR row never persisted — Stored has it but DB doesn't).
- `period.CompanyId` not used (e.g. hardcoded 1, or derived via chain hops).
- Handler ctor param inserted NOT at end (breaks backwards-compatible pattern).
- Any migration/DI/EF/controller change; any new command.
- SaveCalledCount asserted == 1 in new PR-link facts (must be 2).

## Quality Standards

- Follow CreatePostingReferenceHandler pattern (:21-28) for build/Add/save ordering — same shape, same UoW.
- Follow fact (i) test shape (JournalEntrySourceTests.cs:191-215): reflection ctor-param assert + behavioral Stored asserts + SaveCalledCount.
- `period.Id = 1` via BaseEntity.Id public setter (setsource-caller-fix lesson, global MEMORY:250) — no reflection/subclass needed.
- Keep SetSource (:81) and PostOpeningBalances untouched — zero domain diff.
- No duplicate pre-check unless planner locks it: CreatePostingReferenceHandler's GetBySourceAsync+InvalidOperationException is the manual-path pattern; OpeningBalance flow already has in-memory IsPosted guard + unique index backstop. State the choice explicitly in the design note.
- Anti-patterns: second DbContext/UoW (dual-write drift); PR built from `request.PeriodId` instead of `period.Id`; hardcoded CompanyId; single-save assumption; touching CreatePostingReferenceCommand/Controller.

## Prior Attempt Analysis

No prior failures in this loop (fresh loop, planning in progress). Relevant prior-loop lessons:
- persist loop G3: compile-error RED via ctor-param append = CS1729 "does not contain a constructor that takes 4 arguments" at fact (h)/(i) ctor call sites (global MEMORY:254) — expect same mechanism when 4th param lands.
- persist loop G3: FakeJournalEntryRepository MUST implement all port members (GetAllAsync) — FakePostingReferenceRepository already matches its port exactly, no new fake needed (global MEMORY:254).
- posting-reference-harden G2: don't add guards to entity setters with live transient-Id callers — NOT applicable here (PR built only post-save with real Ids; guards already in place).
- persist loop G1: no-migration evidence = Migrations count + latest timestamp + zero NEW files, NOT grep (134 pre-existing 'openingbalance' hits in Migrations) (global MEMORY:252).

## External Knowledge & Resources

**Classification: CODEBASE-ONLY.** No external research required. Every claim in the task brief re-verified against repo sources this pass:

| Claim | Verification |
|-------|-------------|
| PostingReference ctor shape | `PostingReference.cs:15-24` — 4-param `(long companyId, long journalEntryId, string sourceType, long sourceId)`, V2 guard `journalEntryId <= 0` → DomainException. Verbatim match. |
| Repo Add + same-UoW save | `IPostingReferenceRepository.cs:9` `AddAsync`; `EfPostingReferenceRepository.cs:26-29` delegates to DbSet, no SaveChanges (UoW owns save); handler's existing `unitOfWork` reused. |
| DI registered | `DependencyInjection.cs:69` `AddScoped<IPostingReferenceRepository, EfPostingReferenceRepository>()` — zero DI churn. |
| No VAS/Circular requirement change | `PostingReference-Design-2026.md` E9 (:30): "No regulatory mandate on shape" — ADR-010 has zero PostingReference/SourceType/SourceId mentions; :128 "No VAS / Circular 99 compliance claim beyond E9". `OpeningBalance-Persist-Design-2026.md:17`: "Zero new regulatory surface. No new VAS / Circular 99/2025 treatment is introduced". Shape is integrity decision, not regulatory mandate. |
| Identity-assignment + two-save timing proven in-repo | Persist loop proved JE Id > 0 after `SaveChangesAsync` in THIS handler (OpeningBalance-Persist-Design-2026.md §1 :10, :15). Canonical AddAsync→Save→use-assigned-Id pattern = ~40 handlers, exemplar `CreatePostingReferenceHandler.cs:27-30` (AddAsync :27 → SaveChangesAsync :28 → return `reference.Id` :30). Two-save shape is a direct consequence of V2 guard + EF identity assignment — pure in-repo reasoning. |

**Correction to task brief (non-blocking):** "Bank handler" precedent does not exist as code — `glob *Bank*` in `Application/Handlers` = 0 files; Bank entities confirmed missing (`Discovery-Bank-PostingReference-Gaps-2026.md:12-33`). The brief's "Bank handler" is a loose reading of `OpeningBalance-Persist-Design-2026.md:15` ("e.g. `CreatePostingReferenceHandler.cs:27-30`, Bank handlers" — design-doc citation of the canonical pattern, not a repo file). The real in-repo precedent is CreatePostingReferenceHandler + the ~40-handler Add→Save→use-Id pattern + the persist loop's proof in this exact handler. Classification unchanged: CODEBASE-ONLY.

**Why no external knowledge is needed:**
- No new regulatory surface: E9 + persist design §4 both explicitly zero VAS/Circular 99 claims; PR shape locked since PostingReferenceHarden migration.
- No new library/API/data source: `FakePostingReferenceRepository` (Fakes.cs:50-67) + `FakeUnitOfWork` (SaveCalledCount, :110-118) already exist; no new NuGet/MCP/skill.
- No new EF/DI/schema behavior: identity PK assignment during SaveChangesAsync is the standard EF Core behavior already exercised by every Create handler in the repo.
- Sole SourceType literal `"OpeningBalance"` already in-repo (`OpeningBalancePeriod.cs:81`); column width varchar(100) locked (PostingReferenceConfiguration.cs:24-27).

**If planner/auditor want a second opinion:** the only open design question is the duplicate pre-check (replicate CreatePostingReferenceHandler's GetBySourceAsync+InvalidOperationException vs. rely on in-memory IsPosted guard + unique index backstop) — an in-repo pattern choice, not external knowledge. Flagged in Context section above.
## Task-Specific Research — [G1] design

**Purpose:** lock the DESIGN decisions for `docs/OpeningBalance-PRLink-Design-2026.md` (decision inputs, not code). All line refs re-verified against source this pass (2026-09-23).

### D1 — Duplicate-pre-check decision: **Option B (no pre-check)** — rationale + exact wording

- **Sequential dupes** (period already posted): `OpeningBalancePeriod.cs:61-62` — `PostOpeningBalances` throws `DomainException("Opening balances are already posted.")` if `IsPosted`, BEFORE any JE/PR creation. Handler loads period via `GetByIdAsync` (:17-18) → second POST dies at :61-62 pre-persistence, clean, regardless of any pre-check. This is the primary guard.
- **Concurrent race** (two POSTs, both load `IsPosted=false`): xmin concurrency token on the period row. `PostOpeningBalances` mutates the period (`IsPosted=true`, `Status=Closed` :90-91) so the period row IS part of save 1. Second request's save 1 (UPDATE period + INSERT JE) hits `DbUpdateConcurrencyException` → **JE never persists**. xmin on all entities (AGENTS.md).
- **Unique index last resort**: `IX_posting_references_company_id_source_type_source_id` unique (company_id, source_type, source_id) — verified `20260922084832_PostingReferenceHarden.cs:24-28` + `PostingReferenceConfiguration.cs:33-34`. Catches any path bypassing the period update (e.g. manual `CreatePostingReferenceCommand`).
- **Why CreatePostingReferenceHandler's pre-check (:17-19) is NOT replicated**: that handler has **no domain guard** — caller supplies arbitrary CompanyId/JournalEntryId/SourceType/SourceId, so `GetBySourceAsync` + `InvalidOperationException` is its only duplicate defense. OpeningBalance flow already has the IsPosted domain guard. Replicating the pre-check would: (a) add a redundant DB round-trip; (b) be TOCTOU-ineffective against the concurrent race (both requests pass it before either saves); (c) if placed post-save-1 (the natural "before PR build" spot), a throw leaves the JE already committed with no PR row — dangling-JE partial state. To avoid (c) it must go at handler start (:17), where it's redundant with IsPosted.
- **Wording for design note**: "No `GetBySourceAsync` pre-check in PostOpeningBalancesHandler. Sequential duplicates are blocked pre-persistence by the domain `IsPosted` guard (OpeningBalancePeriod.cs:61-62); the concurrent race is caught at save 1 by the xmin concurrency token on the period row (DbUpdateConcurrencyException — the losing JE never persists); the unique index (CompanyId, SourceType, SourceId) is the last-resort DB backstop. CreatePostingReferenceHandler's pre-check (CreatePostingReferenceHandler.cs:17-19) exists only because that handler lacks a domain guard; replicating it here adds a round-trip, is TOCTOU-ineffective, and risks a dangling JE if misplaced after save 1."

### D2 — Exact handler change (PostOpeningBalancesHandler.cs)

- **Ctor**: append `IPostingReferenceRepository` as 4th param at END — `(IOpeningBalancePeriodRepository periodRepository, IUnitOfWork unitOfWork, IJournalEntryRepository journalEntryRepository, IPostingReferenceRepository postingReferenceRepository)` (:7-10). Backwards-compatible expansion pattern (global MEMORY:74).
- **Flow** (inserted between :24 and :26):
  1. Save 1: `await unitOfWork.SaveChangesAsync(cancellationToken)` (:24) — EF assigns `journalEntry.Id` (identity PK).
  2. Build PR: `new PostingReference(period.CompanyId, journalEntry.Id, "OpeningBalance", period.Id)` — all 4 ctor guards pass (PostingReference.cs:15-24): CompanyId>0 (period.CompanyId :9, ctor-guarded :22-23), journalEntryId>0 (post-save), SourceType non-empty, sourceId>0 (period.Id real — loaded via GetByIdAsync, domain fail-fast :76-77 guarantees >0).
  3. `await postingReferenceRepository.AddAsync(reference)` — same UoW.
  4. Save 2: `await unitOfWork.SaveChangesAsync(cancellationToken)` — second transaction, same DbContext.
- **Return unchanged**: `return new PostOpeningBalancesResult(true)` (:26) — Success bool only; no JE/period Id exposed (R2).
- **Two-save shape is timing-forced**: JE Id doesn't exist until save 1 completes; PR row cannot ride save 1. Same UoW = same DbContext, but two SaveChanges = two DB transactions. Residual save-2-failure risk (JE without PR) is theoretical — realistic race caught at save 1 by xmin.
- **Follow CreatePostingReferenceHandler.cs:21-28 shape** (build → AddAsync → SaveChangesAsync).

### D3 — Test enabler: FakeJournalEntryRepository.AddAsync assigns Id

- **Current**: `Fakes.cs:79-83` — `AddAsync` just adds to `_items`, no Id assignment → `journalEntry.Id` stays 0 in fake path → PR ctor V2 guard (`journalEntryId <= 0` → DomainException, PostingReference.cs:19-20) throws → new PR-link fact fails at runtime.
- **Change**: `AddAsync` assigns Id (counter-based, simulates EF identity assignment during SaveChangesAsync).
- **Safety**: only JE Id==0 assert in the suite is fact G2-3 (`JournalEntrySourceTests.cs:166`) on the domain-created JE BEFORE the handler runs — unaffected by fake Id assignment (that assert never passes through the fake).
- **Correctness**: FakeJournalEntryRepository is list-backed → the stored instance IS the same object the handler builds the PR from → `Stored[0].Id` (assigned) == PR.JournalEntryId. Assertion `JournalEntryId == stored JE Id (>0)` is exact.

### D4 — Fact updates (JournalEntrySourceTests.cs)

- **fact (i)** :191-215: `SaveCalledCount == 1` (:214) → **== 2**; add PR-row assertion: `postingReferenceRepository.Stored` Single { CompanyId == period.CompanyId, JournalEntryId == stored JE Id (>0), SourceType == "OpeningBalance", SourceId == period.Id }. Ctor call :202 gains 4th arg (new `FakePostingReferenceRepository`).
- **fact (h)** :171-187: ctor call :176 gains 4th arg. SaveCalledCount==1 (:184) stays **== 1**? — NO: handler now saves twice, so fact (h) :184 also becomes **== 2** (both facts run the full handler). Flag: PLAN says "existing facts (h)/(i) SaveCalledCount==1 → ==2" — BOTH facts update, not just (i).
- **RED mechanism**: 4th ctor param → CS1729 "does not contain a constructor that takes 4 arguments" at :176 and :202 (compile-error RED, same mechanism as persist-loop G3 — global MEMORY:254). Record actual error code + lines; don't force predicted.
- **New fact shape** (follow fact (i)): `period.Id = 1` via BaseEntity.Id public setter (global MEMORY:250); FakeOpeningBalancePeriodRepository list-backed → GetByIdAsync returns same instance → handler sees Id=1.

### D5 — No-touch list (zero schema/DI/EF churn)

- **Touched (3 files only)**: `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs` + `tests/SmeAccounting.BankTests/JournalEntrySourceTests.cs` + `tests/SmeAccounting.BankTests/Fakes.cs`.
- **No-touch**: `CreatePostingReferenceHandler.cs`, `CreatePostingReferenceCommand.cs`, `CreatePostingReferenceCommandValidator.cs`, `PostingReferenceController.cs`, all EF configurations, `SmeAccountingDbContext.cs`, `DependencyInjection.cs` (IPostingReferenceRepository already registered :69), migrations, unique index (exists since 20260922084832), domain entities (SetSource :81 and PostOpeningBalances untouched).
- **No new command**: PR creation is handler-internal (design §7 same-UoW atomic write), NOT a new MediatR command.

### D6 — Gates

- **Build**: `dotnet build SmeAccounting.sln` 0 warnings / 0 errors (TreatWarningsAsErrors).
- **Arch**: `dotnet test tests/SmeAccounting.ArchitectureTests/` 22/22 (test-project changes never affect count).
- **BankTests**: ≥ 58 (57 existing + ≥ 1 new PR-link fact).
- **No-migration evidence — corrected pattern** (global MEMORY:252, :256): Migrations dir file count == 35 (17 migrations × 2 + snapshot) — verified this pass; latest `20260922084832_PostingReferenceHarden` predates loop commits (git log: loop commits not yet started — last commit ae62ae4 closes opening-balance-persist); zero NEW migration files (count + `git show --stat` per loop commit). **grep over Migrations INVALID** — 134-style pre-existing 'openingbalance'/'postingreference' hits from prior loops.
- **No-touch audit**: `git show --stat` per commit cross-checked against D5 list (zero code changes ⇒ state-files-only commits).

## Task-Specific Research — [G2] verification criteria

**Purpose:** executor/verifier checklist for G2 TDD handler change. All line refs re-verified against source this pass (2026-09-23, HEAD 3c4f3dd). Binding spec = `docs/OpeningBalance-PRLink-Design-2026.md` §2/§3/§4/§5/§6.

### 1) Exact handler change — PostOpeningBalancesHandler.cs (28 lines, verified this pass)

Current full body (verbatim, line numbers current):
- Ctor :7-10 — `(IOpeningBalancePeriodRepository periodRepository, IUnitOfWork unitOfWork, IJournalEntryRepository journalEntryRepository)` — 3 params, primary ctor.
- :17-18 `GetByIdAsync(request.PeriodId)` → `?? throw new KeyNotFoundException(...)`.
- :20 `var journalEntry = period.PostOpeningBalances(request.PostedBy, request.PostedAt);`
- :22 `await journalEntryRepository.AddAsync(journalEntry);`
- :24 `await unitOfWork.SaveChangesAsync(cancellationToken);` — **save 1**.
- :26 `return new PostOpeningBalancesResult(true);` — **return**.

**PR build + AddAsync + save 2 land BETWEEN :24 and :26** (after save 1, before return):
1. `var reference = new PostingReference(period.CompanyId, journalEntry.Id, "OpeningBalance", period.Id);` — `period.CompanyId` direct (OpeningBalancePeriod.cs:9, ctor-guarded >0 :22-23); `journalEntry.Id` post-save; `period.Id` real (loaded via GetByIdAsync, domain fail-fast :76-77 guarantees >0).
2. `await postingReferenceRepository.AddAsync(reference);`
3. `await unitOfWork.SaveChangesAsync(cancellationToken);` — **save 2**, same UoW/DbContext, second transaction.
4. Return :26 unchanged.

**`journalEntry.Id` post-save non-zero in real EF — CONFIRMED**: `JournalEntryConfiguration.cs:14-16` — `builder.Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd();` — identity PK, EF assigns during `SaveChangesAsync`. Persist-loop-proven in this exact handler (OpeningBalance-Persist-Design-2026.md §1). Shape precedent: `CreatePostingReferenceHandler.cs:21-28` (build :21-25 → AddAsync :27 → SaveChangesAsync :28).

### 2) Test RED surface — ALL handler ctor call sites enumerated (grep `PostOpeningBalancesHandler` across repo)

**Only 2 existing ctor call sites in the entire repo** (src has zero — production wiring is MediatR DI):
- `JournalEntrySourceTests.cs:176` — fact (h) `PostOpeningBalancesHandler_PersistsPeriodFlags_SaveCalledOnce` (:171-187). Ctor :176 3-arg; `SaveCalledCount == 1` :184 → **== 2**.
- `JournalEntrySourceTests.cs:202` — fact (i) `PostOpeningBalancesHandler_PersistsJournalEntry_AddsToRepository` (:191-215). Ctor :202 3-arg; `SaveCalledCount == 1` :214 → **== 2**; :211-212 already asserts JE cache columns (`stored.SourceType == "OpeningBalance"`, `stored.SourceId == period.Id`).
- **No other test file references the handler** (grep across tests = JournalEntrySourceTests.cs only). No other fact calls the handler ctor or handler flow.
- **Fact (i) reflection assert :193-197 survives 4th param**: `GetConstructors().Single().GetParameters()` + `Assert.Contains(parameters, p => p.ParameterType == typeof(IJournalEntryRepository))` — `Contains`, NOT exact-count → adding a 4th param does NOT break it. Zero change needed to the reflection assert.
- **New PR-link fact adds a THIRD ctor call site** (4-arg, with `new FakePostingReferenceRepository()`).

**Compile-error RED = CS1729 at THREE sites** (2 existing :176/:202 + new fact's ctor call): 4-arg call vs stale 3-param ctor → `CS1729: 'PostOpeningBalancesHandler' does not contain a constructor that takes 4 arguments`. Same mechanism as persist-loop G3 (global MEMORY:254 — actual was CS1729 for 3-arg vs 2-param; record actual code + lines, don't force predicted).

### 3) FakeJournalEntryRepository AddAsync Id-assignment change

- **Port signature**: `IJournalEntryRepository.cs:9` — `Task AddAsync(JournalEntry entry)` — returns **Task** (NOT `Task<JournalEntry>`). Fake must keep the signature, assign Id to the instance, return `Task.CompletedTask`.
- **Current** `Fakes.cs:79-83`: `_items.Add(entry); return Task.CompletedTask;` — no Id assignment → `journalEntry.Id` stays 0 in fake path.
- **Target** (counter-based, simulates EF identity): `entry.Id = _nextId++;` (or `++_nextId` starting 1) then `_items.Add(entry); return Task.CompletedTask;`. `BaseEntity.Id` has PUBLIC setter (BaseEntity.cs:7) — direct assignment, no reflection.
- **Correctness**: fake is list-backed → stored instance IS the same object the handler builds the PR from → `Stored[0].Id` (assigned) == `PR.JournalEntryId`. Assertion `JournalEntryId == stored JE Id (>0)` is exact.
- **Safety**: only JE `Id == 0` assert in suite is fact G2-3 (`JournalEntrySourceTests.cs:166`) on the domain-created JE BEFORE the handler — never passes through the fake, unaffected (design §3).
- **Side effect (benign)**: fake `GetByIdAsync` (`x.Id == id`) starts matching stored entries — no existing fact asserts it, no breakage.

### 4) New PR-row fact — exact assert shape + interaction with fact (i)

- **Fact (i) already asserts JE SourceType/SourceId** (:211-212) — those are the JE **cache columns** (read-model). The new PR-row assert targets the **canonical** `posting_references` row — same values, different object/layer. **Complementary, NOT duplication** (design §1 Option A: JE SourceType/SourceId = origin-trace cache; PR = canonical audit/idempotency row).
- **Design doc §4 is binding**: fact (i) :202 gains 4th arg, :214 SaveCalledCount → 2, AND gains PR-row assertion `postingReferenceRepository.Stored` Single {`CompanyId == period.CompanyId`, `JournalEntryId == stored JE Id (>0)`, `SourceType == "OpeningBalance"`, `SourceId == period.Id`}. PLUS a **new dedicated PR-link fact** (follows fact (i) shape): `period.Id = 1` (BaseEntity.Id public setter), run handler, assert PR row + `SaveCalledCount == 2`. The new fact is what satisfies the **≥58 gate** (57 + 1 new).
- **New fact shape** (from PLAN + design §4): `var postingReferenceRepository = new FakePostingReferenceRepository();` → 4-arg handler ctor → `period.Id = 1` after `periodRepository.AddAsync(period)` (FakeOpeningBalancePeriodRepository list-backed :88-108 → GetByIdAsync returns SAME instance → handler sees Id=1) → `handler.Handle(new PostOpeningBalancesCommand(1, "tester", TestDate), ...)` → `var pr = Assert.Single(postingReferenceRepository.Stored);` → assert `pr.CompanyId == period.CompanyId`, `pr.JournalEntryId == stored.Id` (stored = `Assert.Single(journalEntryRepository.Stored)`), `pr.SourceType == "OpeningBalance"`, `pr.SourceId == period.Id`, `unitOfWork.SaveCalledCount == 2`.
- **No new fakes**: `FakePostingReferenceRepository` (Fakes.cs:50-67) + `FakeUnitOfWork` (:110-118) already exist. `using SmeAccounting.Domain.Ports;` already at JournalEntrySourceTests.cs:6; FakePostingReferenceRepository is same namespace `SmeAccounting.BankTests` → zero using changes.

### 5) RED strategy — two-stage RED, both captured

1. **Compile-error RED** (tests first): write new fact + update facts (h)/(i) ctor calls to 4-arg against stale 3-param ctor → build fails **CS1729** at :176, :202, + new fact's ctor call (3 sites). Record actual error code + lines (MEMORY:254 — don't force predicted).
2. **Runtime RED** (handler changed, fake NOT yet): build passes, but EVERY fact running the handler — (h), (i), AND the new fact — fails with `DomainException("JournalEntryId must be greater than zero.")` (PR ctor V2 guard, PostingReference.cs:19-20) because fake JE Id stays 0. **Capture this runtime RED too** (brief item 5) — run BankTests after handler change, record the 3 failing facts + exception, then apply the enabler.
3. **Enabler → GREEN**: FakeJournalEntryRepository.AddAsync assigns counter-based Id → all 58 facts green.

### 6) Gates (G3 verify core→edge)

- `dotnet build SmeAccounting.sln` — 0 warnings / 0 errors (TreatWarningsAsErrors).
- `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 (test-project changes never affect count).
- `dotnet test tests/SmeAccounting.BankTests/` — **58 green** (57 baseline verified this pass: BankAggregateTests 13 + JournalEntrySourceTests 12 + PaymentMethodAggregateTests 14 + PostingReferenceAggregateTests 6 + PostingReferenceCqrsTests 10 + PostingReferenceRepositoryTests 2 = 57; + 1 new PR-link fact).
- **No-migration unchanged**: Migrations dir = 35 files (17×2 + snapshot, verified this pass), latest `20260922084832_PostingReferenceHarden` predates loop commits (42ec4e5/3c4f3dd = G1, 2026-09-23), zero NEW. grep over Migrations INVALID (G1 trap, global MEMORY:252).
- **No-touch audit**: `git show --stat` per commit vs design §5 list (touched = handler + JournalEntrySourceTests + Fakes only). Working tree note: `.opencode/agents/verifier.md` has pre-existing unstaged modification (loop MEMORY:7) — not from this loop, do not stage.
- **RED-reconstruction canon** (G3, global MEMORY:255): `git checkout <GREEN commit>~1 -- <changed files>`, rebuild → CS1729 reproduces deterministically, restore after.

## Environment & Integration

- E1: Gates baseline — build 0/0, arch 22/22, BankTests 57/57 (cite opening-balance-persist_DONE/REPORT.md)
- E2: Test layout — BankTests refs Domain+Application; InternalsVisibleTo Application→BankTests (Application.csproj:14); handler facts in JournalEntrySourceTests.cs (fact h ~176-197 ctor 3-param; fact i ~199-215 reflection + Stored JE + SaveCalledCount==1; G2-3 ~155-169 transient Id==0). 4th ctor param → CS1729 RED at h/i call sites.
- E3: Dev DB — posting_references 0 rows, journal_entries 0 rows (no backfill concern)
- E4: Migration posture — zero NEW (posting_references table + unique index (CompanyId,SourceType,SourceId) exist since PostingReferenceHarden 20260922084832; Migrations 35 files, latest predates loop)
- E5: DI — IPostingReferenceRepository → EfPostingReferenceRepository registered DependencyInjection.cs:69
- E6: Integration surface — PostOpeningBalancesCommand/Result consumers = validator + handler only (no Api controller; grep Controllers empty). Second SaveChangesAsync in handler → existing SaveCalledCount==1 assertions in facts h/i must become ==2. FakeJournalEntryRepository.AddAsync must assign Id (R4) to satisfy PR V2 guard journalEntryId>0.
