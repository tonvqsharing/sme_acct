# Opening Balance JE Persist — Locked Design (Handler Persists the Domain-Created JournalEntry)

**Date:** 2026-09-23
**Status:** LOCKED — G2/G3 implement exactly this, no deviation
**Scope:** Design only. No code changed by this document.
**Loop:** `loop-stack/opening-balance-persist/` task [G1]

## 1. Decision

**Persist the JournalEntry the domain already creates: `journalEntryRepository.AddAsync(journalEntry)` then the existing `unitOfWork.SaveChangesAsync` in `PostOpeningBalancesHandler`. EF assigns the JE Id during Save, so the JE Id is > 0 before any PostingReference link (satisfies the `PostingReference` ctor V2 guard `journalEntryId > 0`).**

Rationale:

1. **The JE is currently discarded.** `PostOpeningBalancesHandler.cs:16-21` loads the period, calls `period.PostOpeningBalances(...)`, then `SaveChangesAsync` — but never calls `IJournalEntryRepository.AddAsync`. The JE built inside `OpeningBalancePeriod.PostOpeningBalances` (`OpeningBalancePeriod.cs:80-88`) is a method-local that dies with the call; only the period flags persist. This is the discarded-JE bug explicitly deferred by `docs/PostingReference-Design-2026.md` §9 item 3 ("`PostOpeningBalancesHandler.cs:16-21` discarded-JE bug fix — excluded: separate task; blocks end-to-end value of any option") and anticipated by `docs/SetSource-CallerFix-Design-2026.md` §2 Rejected Option 1 ("Requires `PostOpeningBalances` to expose the JE (currently `void`, JE is a method-local at `OpeningBalancePeriod.cs:77-85`) plus handler injection of `IJournalEntryRepository.AddAsync`... Revisit only in the discard-bug loop"). This loop is that task.
2. **JE-persist-first is the canonical ~40-handler pattern.** `AddAsync(entity)` → `SaveChangesAsync` → use assigned `entity.Id` (e.g. `CreatePostingReferenceHandler.cs:27-30`, Bank handlers). EF Core assigns the identity PK during `SaveChangesAsync`; the JE is new-untracked until `AddAsync`, so Add MUST precede Save — Add-after-Save is the current bug.
3. **The V2 guard is the forcing function.** `PostingReference` ctor (`PostingReference.cs:19-20`) throws on `journalEntryId <= 0`. A reference row cannot exist until the JE Id is assigned post-Save — design §7 timing: "reference row created post-JE-persist when the JE id is assigned". Persisting the JE first makes that handoff possible for any future PR-link call.
4. **Zero new regulatory surface.** The fix persists a JE the domain ALREADY creates with balanced, posted, source-traced lines (`OpeningBalancePeriod.cs:80-88`). No new VAS / Circular 99/2025 treatment is introduced (verified: ADR-010 has zero OpeningBalance/JournalEntry/PostingReference mentions; design §2 E9 — reference shape is an integrity decision, not a regulatory mandate).
5. **Same-UoW atomicity preserved.** The JE and the period flags are written by the one existing `unitOfWork.SaveChangesAsync` — no second save, no dual-write drift. The canonical `posting_references` row (design §7: "Both written atomically in the same UoW/handler that persists the JE") is a SEPARATE future task (§5 no-touch list).

## 2. Domain Surface — `OpeningBalancePeriod.PostOpeningBalances` `void` → `JournalEntry`

**File:** `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs`
**Method:** `PostOpeningBalances(string postedBy, DateTimeOffset postedAt)` (line 59, `void`)

- Change signature `void` → `JournalEntry`.
- Add `return journalEntry;` immediately after `journalEntry.Post(postedBy, postedAt)` (line 88). The JE is fully formed at that point — `IsPosted=true` set inside `Post()` (`JournalEntry.cs:70`), lines balanced (Post validates). Period mutations at lines 90-91 (`IsPosted=true`, `Status=Closed`) and the event at line 93 (`OpeningBalancesPosted`) mutate the PERIOD, not the JE — return placement before/after them is behaviorally identical; lock "after Post()" for minimal diff adjacency to JE construction.
- **JE construction stays in domain.** The handler only persists; it does not build or mutate the JE. `SetSource("OpeningBalance", Id)` stays inside the domain method (line 81) using `period.Id` — the returned JE already carries `SourceType == "OpeningBalance"` and `SourceId == period.Id`.
- **NO event change.** `OpeningBalancesPosted` keeps `(PeriodId, CompanyId)` — do NOT add `JournalEntryId` (event minimalism, global standard).
- **NO guard change.** Ordering is already correct: fail-fast `Id <= 0` (lines 76-77) runs BEFORE JE construction (79-80) and `SetSource` (81); the persisted path passes the hardened SetSource guards naturally (setsource-caller-fix loop). Return-type change is purely additive at method end.
- **Callers (exhaustive, 3 sites):** handler `PostOpeningBalancesHandler.cs:19` + test sites `JournalEntrySourceTests.cs:105` (fact f) and `:119` (fact g). Both test sites discard the return value today → non-breaking signature change.

## 3. Handler Surface — `PostOpeningBalancesHandler`

**File:** `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs` (25 lines, `internal sealed`, primary ctor)

- **3rd ctor param APPENDED at end** (backwards-compatible expansion pattern, new params at end):
  `(IOpeningBalancePeriodRepository periodRepository, IUnitOfWork unitOfWork, IJournalEntryRepository journalEntryRepository)`
- **Body:**
  - Line 19 becomes `var journalEntry = period.PostOpeningBalances(request.PostedBy, request.PostedAt);` (capture from return value).
  - `await journalEntryRepository.AddAsync(journalEntry);` — BEFORE the existing `await unitOfWork.SaveChangesAsync(cancellationToken)` (line 21). Same UoW; EF assigns the JE Id during SaveChanges.
  - Return `new PostOpeningBalancesResult(true)` (line 23) unchanged.
- **`period.Id` for the SetSource link is NOT needed in the handler.** `SetSource` stays inside the domain method; the handler never calls it. The handler needs only the JE reference for `AddAsync`.
- **DI: zero change.** `EfJournalEntryRepository` is already registered (`DependencyInjection.cs:29`: `services.AddScoped<IJournalEntryRepository, EfJournalEntryRepository>();`) — the new ctor param resolves via the existing registration.
- **No controller dispatches this command** (Api grep = 0 hits) — handler is MediatR-wired only; no controller/ViewModel churn.

## 4. Test Surface — `tests/SmeAccounting.BankTests/`

### Fact (i) flip — `JournalEntrySourceTests.cs:146-156`

- Rename `PostOpeningBalancesHandler_DiscardsJournalEntry_NoJournalEntryRepository` → `PostOpeningBalancesHandler_PersistsJournalEntry_AddsToRepository`.
- Shape change: `public void` → `public async Task` (Handle is async, like fact (h)).
- Assert persistence behaviorally:
  - Ctor HAS `IJournalEntryRepository` param (reflection `Contains` — or drop reflection for behavioral asserts).
  - `fakeJournalEntryRepository.Stored` has exactly 1 JE with `SourceType == "OpeningBalance"`, `SourceId == period.Id`, `IsPosted == true`.
  - `unitOfWork.SaveCalledCount == 1`.
- Optional: set `journalEntry.Id = 5` post-Add (`BaseEntity.Id` public setter, `BaseEntity.cs:7`) to simulate the EF handoff — simulates, doesn't test, EF. `FakeUnitOfWork` does NOT assign Ids (matches all existing fakes; EF identity assignment is never faked).

### Fact (h) collateral — `JournalEntrySourceTests.cs:128-144`

- Line 133 `new PostOpeningBalancesHandler(periodRepository, unitOfWork)` → add the fake JE repo arg: `new PostOpeningBalancesHandler(periodRepository, unitOfWork, journalEntryRepository)`.
- Fact (h) is the ONLY handler-ctor call site in tests (line 133); fact (i) uses reflection (`GetConstructors`, lines 150-153) — param-type assert only, no ctor call.

### `FakeJournalEntryRepository` — `Fakes.cs`

- Copy `FakePostingReferenceRepository` shape (lines 50-67) MINUS `GetBySourceAsync` — the `IJournalEntryRepository` port exposes only `GetByIdAsync` / `GetAllAsync` / `AddAsync` (verified `IJournalEntryRepository.cs:5-9`).
- Exact shape: `List<JournalEntry> _items`; `GetByIdAsync` = FirstOrDefault by Id; `GetAllAsync` = `Task.FromResult<IReadOnlyList<JournalEntry>>(_items.ToList())`; `AddAsync` = add + `Task.CompletedTask`; `Stored => _items`.
- **NO `SaveCalledCount` on the fake repo** — save tracking lives on `FakeUnitOfWork` (Fakes.cs:91-99: `SaveCalledCount` + `SaveChangesAsync` → `Task.FromResult(1)`).

### New domain Facts (G2)

- Facts asserting `PostOpeningBalances` returns the created JE: non-null, `SourceType == "OpeningBalance"`, `SourceId == period.Id`, `IsPosted == true`, balanced lines — split into ≥2 Facts (PLAN "add Facts" plural). Existing facts (f)/(g) discard the return — no edit needed for the signature change.

## 5. No-Touch List

| Area | Why untouched |
|------|---------------|
| **PostingReference creation in this handler** | PR creation lives in `CreatePostingReferenceHandler`/`CreatePostingReferenceCommand` (separate command). The design §7 same-UoW atomic write (JE + canonical `posting_references` row) is a SEPARATE future task — `docs/PostingReference-Design-2026.md` §9 item 3 + §7 timing. This loop persists the JE only. |
| **New command / handler / controller** | `PostOpeningBalancesCommand` / `PostOpeningBalancesCommandValidator` / `PostOpeningBalancesResult` untouched; Api grep = 0 hits (no controller dispatches this command). |
| **EF config / DbContext** | `JournalEntryConfiguration` untouched; no DbSet/Ignore change. |
| **DI** | `EfJournalEntryRepository` already registered (`DependencyInjection.cs:29`) — zero DI churn. |
| **Migration** | `journal_entries` table + all mapped columns exist since `InitialCreate` (20260916051341, line 73): id, entry_number, period_id, description, source_type varchar(100) nullable, source_id, posted_by, posted_at, is_posted, xmin. Persisting a domain-created JE touches zero schema. |
| **Domain event / SetSource guards** | `OpeningBalancesPosted` stays minimal; SetSource guards hardened in the setsource-caller-fix loop — read, do not edit. |

## 6. Gates (G4 verify core→edge)

1. `dotnet build SmeAccounting.sln` — 0 warnings, 0 errors (`TreatWarningsAsErrors=true`).
2. `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 (NetArchTest scans src assemblies only; test-project changes never affect the count).
3. `dotnet test tests/SmeAccounting.BankTests/` — **≥ 56 green** (54 pre-existing = 45 + 9 SetSource guard Facts, + ≥ 2 new domain Facts; fact (i) renamed in place, fact (h) extended in place — net 0 count change).
4. **No-migration evidence — CORRECTED pattern** (the literal PLAN phrasing "grep -i openingbalance over Migrations = 0 hits" is factually wrong — do NOT use verbatim):
   - `grep -ri openingbalance src/SmeAccounting.Infrastructure/Migrations/` returns **134 hits — ALL pre-existing** `OpeningBalancePeriod` / `OpeningBalanceEntry` / `OpeningBalanceMapping` C# property names in Designer files + model snapshot (tables created by prior loop `20260921052333_CompanyOpeningUserMgmt`). These are expected entity-model names, NOT this loop's schema surface.
   - Correct evidence: (a) Migrations dir count = **17** (35 files = 17×2 + snapshot); (b) latest = `20260922084832_PostingReferenceHarden` (2026-09-22) predates this loop's commits; (c) **zero NEW migration file** scaffolded this loop, zero new table/column for this fix. State this explicitly — the auditor WARNs on the literal PLAN phrasing.

FAIL looks like: any gate red; a migration added for this loop; an arch rule broken; fact (i) left asserting discard; handler still dropping the JE; JE persisted with Id=0; PostingReference created before JE save; any new VAS/Circular 99 compliance claim added to docs.

## Sources

- `docs/PostingReference-Design-2026.md` §7 (idempotency/timing: reference row post-JE-persist, same-UoW atomic write) and §9 item 3 (discarded-JE bug fix excluded → this loop).
- `docs/SetSource-CallerFix-Design-2026.md` §2 Rejected Option 1 (this exact fix deferred to the discard-bug loop) and §5 fact (i) spec (current test asserts discard; goal mandates flipping it in the same change).
- `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs` (lines 59-94), `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs` (lines 7-24), `tests/SmeAccounting.BankTests/JournalEntrySourceTests.cs` (lines 128-156), `tests/SmeAccounting.BankTests/Fakes.cs` (lines 50-67, 91-99), `src/SmeAccounting.Infrastructure/DependencyInjection.cs:29`, `src/SmeAccounting.Domain/Ports/IJournalEntryRepository.cs`.