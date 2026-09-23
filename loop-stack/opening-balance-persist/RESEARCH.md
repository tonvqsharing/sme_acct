# Research Log
## Context & Prior Work
- **Bug (verified in source):** `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs:16-21` loads period via `GetByIdAsync`, calls `period.PostOpeningBalances(...)`, then `SaveChangesAsync` — but NEVER calls `IJournalEntryRepository.AddAsync`. The JE created inside `OpeningBalancePeriod.PostOpeningBalances` (`src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:80-88`: `new JournalEntry(...)` → `SetSource("OpeningBalance", Id)` → AddLine loop → `Post(...)`) is discarded; only period flags persist.
- **Port ready:** `IJournalEntryRepository` (`src/SmeAccounting.Domain/Ports/IJournalEntryRepository.cs`) already exposes `AddAsync(JournalEntry entry)` — no port change needed. No handler currently injects it (grep over Handlers = 0 hits).
- **Domain method is `void`:** `OpeningBalancePeriod.PostOpeningBalances` (line 59) returns void; JE is a method-local (line 80). Fix requires exposing the JE (return type change or out-param) so the handler can Add it — anticipated by SetSource design §2 Rejected Option 1 ("Requires `PostOpeningBalances` to expose the JE (currently `void`, JE is a method-local at `OpeningBalancePeriod.cs:77-85`)").
- **Test to update (fact i):** `tests/SmeAccounting.BankTests/JournalEntrySourceTests.cs:146-156` — `PostOpeningBalancesHandler_DiscardsJournalEntry_NoJournalEntryRepository` asserts handler ctor has NO `IJournalEntryRepository` param. Must flip to assert JE persisted when handler injects the repo. Fakes.cs has `FakeUnitOfWork` + `FakeOpeningBalancePeriodRepository`; needs a List-backed `FakeJournalEntryRepository` added (copy `FakePostingReferenceRepository` shape).
- **UoW identity-assignment proven in-repo:** ~40 Create*Handlers follow `AddAsync(entity)` → `SaveChangesAsync` → `return new CreateXResult(entity.Id)` — EF assigns identity PK during SaveChanges. Bank handlers (`CreateBankAccountCommandHandler.cs:16-29`) and `CreatePostingReferenceHandler.cs:27-30` are the pattern. No external source needed.
- **PostingReference ctor guard V2** (`journalEntryId > 0`, `PostingReference.cs`) — reference row creation is impossible until JE id assigned post-Save. This is WHY the JE must persist first.

## External Knowledge & Resources
**Classification: CODEBASE-ONLY** (default — no external research required)

### Regulatory check: no new VAS / Circular 99/2025 requirement introduced
- The fix persists a JE the domain ALREADY creates (`OpeningBalancePeriod.cs:80-88`). The accounting treatment — balanced opening-balance JE with lines, posted, source-traced — is fully designed and implemented in domain. The handler merely fails to persist it. Completing persistence introduces NO new treatment and NO new regulatory surface.
- `docs/architecture/ADR-010-tax-foundation-regulatory-traceability.md` — zero mentions of OpeningBalance / JournalEntry / PostingReference (grep = 0 hits).
- `docs/PostingReference-Design-2026.md` §2 E9 (locked): "No VAS / Circular 99 article prescribes reference shape" — structure is an integrity decision, not a regulatory mandate.
- `docs/` grep for OpeningBalance: only Discovery inventories + the two design docs below. No regulatory doc prescribes opening-balance JE persistence.

### Design docs already agree on persistence approach (LOCKED — in-repo guidance, no external source)
- **`docs/PostingReference-Design-2026.md`** (LOCKED 2026-09-22):
  - §2 E7: discarded-JE handler bug documented; §9 item 3: "**`PostOpeningBalancesHandler.cs:16-21` discarded-JE bug fix** — excluded: separate task; blocks end-to-end value of any option." → THIS loop is that separate task.
  - §7 timing (normative): "reference row created post-JE-persist when the JE id is assigned" + "Both written atomically in the same UoW/handler that persists the JE (closes dual-write drift)". → JE must be Add'ed + SaveChanges'd FIRST (Id assigned), THEN SetSource with real Id, THEN PostingReference row in same UoW.
- **`docs/SetSource-CallerFix-Design-2026.md`** (LOCKED 2026-09-22):
  - §2 Rejected Option 1 describes exactly this fix ("handler injection of `IJournalEntryRepository.AddAsync`, then SaveChanges-then-SetSource, plus a canonical `posting_references` row per design §7 timing") and defers it: "Revisit only in the discard-bug loop, where §7 timing (reference row post-JE-persist) has something to hook onto." → THIS loop.
  - §5 fact (i) test spec: current test asserts discard; loop goal mandates updating it in the same change.

### UoW identity-assignment — proven in-repo, no external source
- EF Core `SaveChangesAsync` assigns identity PK to tracked entities; universal handler pattern (`AddAsync` → `SaveChanges` → return `entity.Id`) across ~40 handlers incl. Bank handlers and `CreatePostingReferenceHandler`. Contradictory external source not needed.

## Requirements & Constraints
- Handler must Add the JE to the repo and Save via UoW so the JE Id is assigned before any PostingReference link (V2 guard `journalEntryId > 0`).
- Same-UoW atomic write per design §7 (JE + PostingReference row, if in scope) — closes dual-write drift.
- Fact (i) test in `JournalEntrySourceTests.cs` updated in the SAME change (goal mandate; SetSource design §5).
- Build 0 warnings / 0 errors (`TreatWarningsAsErrors=true`); 22/22 NetArchTest; BankTests green.
- Domain stays zero-NuGet, `DomainException`-only; `"OpeningBalance"` literal verbatim; no migration expected (no schema change — JE table already exists).
- Scope question for planner: whether this loop also creates the `PostingReference` row (design §7 says both atomic in same UoW) or only persists the JE. Goal phrasing centers on JE persistence + assigned Id "before linking to PostingReference".

### Bounded fix spec — decision inputs (verified in source, 2026-09-23)

**R1. Handler change surface — `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs` (25 lines, `internal sealed`, primary ctor)**
- Ctor today: `(IOpeningBalancePeriodRepository periodRepository, IUnitOfWork unitOfWork)` — NO `IJournalEntryRepository` (grep over Handlers = 0 hits; fact (i) asserts absence). Change: add 3rd ctor param `IJournalEntryRepository journalEntryRepository`.
- Body change: line 19 `period.PostOpeningBalances(...)` must now capture the returned JE; then `await journalEntryRepository.AddAsync(journalEntry)`; existing `await unitOfWork.SaveChangesAsync(cancellationToken)` (line 21) stays — same UoW, Id assigned by EF during SaveChanges. Return `PostOpeningBalancesResult(true)` unchanged.
- UoW already injected — no UoW change. No separate query needed — JE escapes via domain return (R2). `EfJournalEntryRepository` exists + DI-registered (`DependencyInjection.cs:29`) — zero DI churn.
- No controller dispatches this command yet (grep Api = 0 hits) — handler is MediatR-wired only; no controller/ViewModel churn.

**R2. Domain change surface — `OpeningBalancePeriod.PostOpeningBalances` (`OpeningBalancePeriod.cs:59`, `void`)**
- Change `void` → `JournalEntry`; add `return journalEntry;` after `journalEntry.Post(...)` (line 88), before/after `IsPosted=true`/`Status=Closed` (lines 90-91). JE is method-local (line 80) — return is the minimal escape hatch.
- Return vs out-param: return `JournalEntry` preferred (C# idiom, cleaner); `out JournalEntry` also violates nothing architecturally. Both keep JE construction in domain. Design §2 Rejected Option 1 explicitly anticipated "expose the JE (currently `void`, JE is a method-local at `OpeningBalancePeriod.cs:77-85`)".
- Callers: handler (1 site) + 2 test sites (`JournalEntrySourceTests.cs:105,119`) — both test sites discard the return value today, so return-type change is non-breaking for them.
- NO event-payload change: `OpeningBalancesPosted` stays minimal (PeriodId, CompanyId) — do NOT add JournalEntryId to the event (event minimalism enforced cross-loop, MEMORY.md).

**R3. Fact (i) test flip — `tests/SmeAccounting.BankTests/JournalEntrySourceTests.cs:146-156`**
- Today: `PostOpeningBalancesHandler_DiscardsJournalEntry_NoJournalEntryRepository` — reflection assert ctor has NO `IJournalEntryRepository` param (assert-and-record per SetSource design §5 fact (i)).
- Must become: assert ctor HAS `IJournalEntryRepository` AND handler persists JE — e.g. rename `PostOpeningBalancesHandler_PersistsJournalEntry_AddsToRepository`: construct handler with `FakeJournalEntryRepository` + `FakeUnitOfWork`, run `Handle`, assert `fakeJournalEntryRepository.Stored` has exactly 1 JE with `SourceType == "OpeningBalance"`, `SourceId == period.Id`, `IsPosted == true`, and `unitOfWork.SaveCalledCount == 1`.
- "JE Id > 0 passed to PostingReference": real Id assignment is EF's job during SaveChanges (proven by ~40 handlers); `FakeUnitOfWork` does NOT assign Ids, so in the fake test JE Id stays 0 unless explicitly set. Test asserts Add+Save+linkage, not fake-assigned Id. Optional: set `journalEntry.Id = 5` post-Add (BaseEntity.Id has public setter — setsource-caller-fix lesson) to simulate the EF handoff; that simulates, doesn't test, EF.
- Collateral: fact (h) (`PostOpeningBalancesHandler_PersistsPeriodFlags_SaveCalledOnce`, lines 128-144) constructs `new PostOpeningBalancesHandler(periodRepository, unitOfWork)` — MUST add the fake JE repo arg. Facts (h) + (i) are the only handler-ctor call sites in tests.

**R4. FakeJournalEntryRepository + FakeUoW shape (`tests/SmeAccounting.BankTests/Fakes.cs`)**
- Add `internal sealed class FakeJournalEntryRepository : IJournalEntryRepository` — copy `FakePostingReferenceRepository` shape (lines 50-67): `List<JournalEntry> _items`, `GetByIdAsync` (FirstOrDefault by Id), `GetAllAsync` (ToList), `AddAsync` (add + `Task.CompletedTask`), `Stored => _items`. NO `GetBySourceAsync` — `IJournalEntryRepository` doesn't expose it (port = GetByIdAsync/GetAllAsync/AddAsync only).
- `FakeUnitOfWork` (lines 91-99) unchanged: `SaveCalledCount` + `SaveChangesAsync` → `Task.FromResult(1)`. No Id assignment — matches all existing fakes; EF identity assignment is never faked.

**R5. Scope boundary**
- NO PostingReference creation change: PR creation lives in `CreatePostingReferenceHandler` (separate `CreatePostingReferenceCommand`), NOT in `PostOpeningBalancesHandler` (handler body verified lines 12-24: GetByIdAsync → PostOpeningBalances → SaveChanges → return). This loop persists the JE only; the PR-link task (design §7 same-UoW atomic write) is a separate future change.
- NO new command, NO new handler, NO controller, NO EF config change, NO DbContext/DI change (EfJournalEntryRepository already registered).
- NO migration: `journal_entries` table exists since InitialCreate (migration line 73) with all mapped columns (entry_number, date, period_id, description, source_type varchar100 nullable, source_id, posted_by, posted_at, is_posted, xmin — `JournalEntryConfiguration.cs`). Persisting a domain-created JE touches zero schema. No-migration evidence pattern: Migrations-dir count + latest migration (20260922084832_PostingReferenceHarden) predates loop commits + grep -i openingbalance over Migrations = 0 hits.

**R6. Ordering — PR creation is NOT in this handler; V2 guard satisfied by JE-persist-first**
- `PostingReference` ctor V2 guard (`PostingReference.cs:19-20`): `journalEntryId <= 0` throws. PR row creation is impossible until JE Id assigned post-Save — this is WHY the JE must persist first (design §7 timing: "reference row created post-JE-persist when the JE id is assigned").
- In this loop the ordering constraint is: `AddAsync(journalEntry)` BEFORE `SaveChangesAsync` in the same handler/UoW — EF assigns Id during Save. The "JE Id > 0 passed to PostingReference" handoff is satisfied for any FUTURE PR-link call (separate command) because the JE now exists with a real Id.
- `JournalEntry` has NO CompanyId property (only PeriodId) — if a future PR-link task needs `PostingReference(companyId, ...)`, companyId comes from `period.CompanyId` (handler has the period in scope). Not needed this loop.

## Suggested Approach
1. Change `OpeningBalancePeriod.PostOpeningBalances` to expose the created JE (return `JournalEntry` — design §2 Option 1 anticipated this; keeps JE construction in domain).
2. Inject `IJournalEntryRepository` into `PostOpeningBalancesHandler`; after `period.PostOpeningBalances(...)`, `await journalEntryRepository.AddAsync(journalEntry)` then existing `SaveChangesAsync` (Id assigned by EF).
3. Update fact (i) test to assert JE persisted (flip the reflection assert); add `FakeJournalEntryRepository` to Fakes.cs; extend fact (h) handler test to pass the new repo and assert JE stored.
4. If PostingReference row in scope: create it post-Save with assigned JE id + `period.CompanyId`, same UoW (design §7).

## Verification Criteria
- PASS: `PostOpeningBalancesHandler` ctor includes `IJournalEntryRepository`; handler Add's the JE before/within the same SaveChanges; JE Id > 0 after save; fact (i) test now asserts persistence (no longer asserts absence of the repo); build 0/0; arch 22/22; BankTests green (updated facts + new fake).
- PASS: no migration scaffolded (schema unchanged — `journal_entries` table exists).
- FAIL: fact (i) left asserting discard; handler still drops JE; JE persisted with Id=0; any new VAS/Circular 99 compliance claim added to docs; migration added; arch rule broken.

## Quality Standards
- Follow the ~40-handler canonical pattern: `AddAsync` → `SaveChangesAsync` → use assigned Id. Copy `CreatePostingReferenceHandler` shape.
- JE construction stays in domain (`PostOpeningBalances`) — handler only persists; do not duplicate JE-building logic in the handler.
- Test enablers already present: `BaseEntity.Id` public setter, `InternalsVisibleTo("SmeAccounting.BankTests")` in Application.csproj, List-backed fakes (no EF InMemory).
- Anti-patterns: asserting discard post-fix; relaxing V2/V4 guards; creating PostingReference before JE save; touching `SetSource` guards (already hardened, SetSource-CallerFix loop).

## Prior Attempt Analysis
- No prior attempts in this loop (STATUS.md: 0 attempts, planning in progress). Prior-loop context: posting-reference-harden G2 deferred the JE-persist fix here; setsource-caller-fix G2 explicitly recorded fact (i) as "never asserting JE persisted (that contradicts discard-bug scope)" — that test now flips by design.

## Task-Specific Research — [G1] design
*(decision inputs verified against source 2026-09-23 — line numbers current)*

**D1. Domain change — `OpeningBalancePeriod.PostOpeningBalances` `void`→`JournalEntry` (OpeningBalancePeriod.cs:59)**
- Return placement: `return journalEntry;` immediately after `journalEntry.Post(postedBy, postedAt)` (line 88). JE fully formed at that point — `IsPosted=true` set inside `Post()` (JournalEntry.cs:70), lines balanced (Post validates). Period flag lines 90-91 (`IsPosted=true`, `Status=Closed`) and event line 93 (`OpeningBalancesPosted`) mutate the PERIOD, not the JE — return placement before/after them is behaviorally identical; lock "after Post()" for minimal diff adjacency to JE construction.
- Guard interactions — ordering already correct, ZERO guard change:
  - Fail-fast `Id <= 0` (lines 76-77) runs BEFORE JE construction (79-80) and `SetSource` (81). Transient period (Id=0) throws caller message before any JE exists — SetSource never reached.
  - Persisted path (Id>0): `SetSource("OpeningBalance", Id)` (line 81) passes its 3 guards naturally — `IsPosted` false (JE just constructed), `SourceType` non-empty literal, `SourceId = period.Id > 0` (V4 guard, JournalEntry.cs:38-39). No guard trips accidentally; setsource-caller-fix hardening intact.
  - Return-type change is purely additive at method end — zero interaction with any guard.
- NO event change: `OpeningBalancesPosted` keeps (PeriodId, CompanyId) — event minimalism (MEMORY.md global standard; do NOT add JournalEntryId).
- Callers (exhaustive, verified): handler :19 + tests :105 (fact f) + :119 (fact g) — both test sites discard return today → non-breaking signature change.

**D2. Handler change — `PostOpeningBalancesHandler` (25 lines, internal sealed, primary ctor)**
- 3rd ctor param APPENDED at end: `(IOpeningBalancePeriodRepository periodRepository, IUnitOfWork unitOfWork, IJournalEntryRepository journalEntryRepository)` — matches backwards-compatible expansion pattern (new params at end, MEMORY.md G2).
- Body: line 19 becomes `var journalEntry = period.PostOpeningBalances(request.PostedBy, request.PostedAt);` (capture from return value); then `await journalEntryRepository.AddAsync(journalEntry);` BEFORE existing `await unitOfWork.SaveChangesAsync(cancellationToken)` (line 21). Same UoW — EF assigns JE Id during SaveChanges (proven ~40-handler pattern). Return `PostOpeningBalancesResult(true)` (line 23) unchanged.
- **period.Id for SetSource link: NOT needed in handler.** `SetSource("OpeningBalance", Id)` stays inside the domain method (line 81) using period.Id — handler never calls SetSource. Returned JE already carries `SourceType="OpeningBalance"`, `SourceId=period.Id`. Handler needs only the JE reference for AddAsync.
- AddAsync MUST precede SaveChangesAsync: JE is new-untracked until AddAsync; EF assigns Id only during Save. Add-after-Save = JE never persisted (the current bug).

**D3. Test surface — fact (i) flip + fact (h) collateral + FakeJournalEntryRepository**
- Fact (i) (JournalEntrySourceTests.cs:146-156): rename `PostOpeningBalancesHandler_DiscardsJournalEntry_NoJournalEntryRepository` → `PostOpeningBalancesHandler_PersistsJournalEntry_AddsToRepository`. Shape change: `public void` → `public async Task` (Handle is async, like fact (h)). Assert: ctor HAS `IJournalEntryRepository` param (reflection `Contains` — or drop reflection for behavioral asserts) AND handler persists JE: `fakeJournalEntryRepository.Stored` exactly 1 JE with `SourceType == "OpeningBalance"`, `SourceId == period.Id`, `IsPosted == true`, `unitOfWork.SaveCalledCount == 1`.
- Fact (h) collateral (lines 128-144): line 133 `new PostOpeningBalancesHandler(periodRepository, unitOfWork)` → add fake JE repo arg. Fact (h) is the ONLY handler-ctor call site in tests (line 133); fact (i) uses reflection (`GetConstructors`, lines 150-153) — param-type assert only, no ctor call.
- FakeJournalEntryRepository (Fakes.cs): copy `FakePostingReferenceRepository` shape (lines 50-67) MINUS `GetBySourceAsync` — `IJournalEntryRepository` port exposes only `GetByIdAsync`/`GetAllAsync`/`AddAsync` (verified IJournalEntryRepository.cs:5-9). Exact shape: `List<JournalEntry> _items`; `GetByIdAsync` = FirstOrDefault by Id; `GetAllAsync` = `Task.FromResult<IReadOnlyList<JournalEntry>>(_items.ToList())`; `AddAsync` = add + `Task.CompletedTask`; `Stored => _items`. **NO `SaveCalledCount` on the fake repo** — save tracking lives on `FakeUnitOfWork` (Fakes.cs:91-99: `SaveCalledCount` + `SaveChangesAsync` → `Task.FromResult(1)`, no Id assignment — matches all existing fakes; EF identity assignment never faked).
- Optional: `journalEntry.Id = 5` post-Add (BaseEntity.Id public setter, BaseEntity.cs:7) to simulate EF handoff — simulates, doesn't test, EF.

**D4. No-touch list (audit targets for G4)**
- NO PostingReference creation in `PostOpeningBalancesHandler` — PR creation lives in `CreatePostingReferenceHandler`/`CreatePostingReferenceCommand` (separate); design §7 same-UoW atomic write is the FUTURE PR-link task (PostingReference-Design-2026.md §9 item 3, line 116).
- NO new command/handler/controller — `PostOpeningBalancesCommand`/`PostOpeningBalancesCommandValidator`/`PostOpeningBalancesResult` untouched; Api grep = 0 hits (no controller dispatches this command).
- NO EF config change — `JournalEntryConfiguration` untouched; NO DbContext change.
- NO DI change — `EfJournalEntryRepository` already registered (`DependencyInjection.cs:29`, verified E5); handler ctor param resolves via existing registration.
- NO migration — `journal_entries` table + all columns exist since InitialCreate (E4); opening_balance tables from prior loop `20260921052333_CompanyOpeningUserMgmt`.
- NO event change; NO SetSource guard change (hardened in setsource-caller-fix loop).

**D5. Gates**
- Build: 0 warnings / 0 errors (`TreatWarningsAsErrors=true`).
- Architecture: 22/22 (NetArchTest scans src assemblies only — test-project changes never affect count).
- BankTests: 54 pre-existing (45 + 9 SetSource guard Facts, E1) + new Facts all green. G2 adds Facts asserting return value (non-null, SourceType, SourceId, IsPosted, balanced lines — 5 assertions, executor splits into ≥2 Facts per PLAN "add Facts" plural). Fact (i) renamed in place, fact (h) extended in place — net 0 count change. **Gate: ≥56 green** (54 + ≥2 new).
- No-migration evidence — **CORRECTED pattern (PLAN's "grep -i openingbalance = 0 hits" is factually wrong, do NOT use verbatim)**: `grep -ri openingbalance src/SmeAccounting.Infrastructure/Migrations/` returns **134 hits — ALL pre-existing** `OpeningBalancePeriod`/`OpeningBalanceEntry`/`OpeningBalanceMapping` C# property names in Designer files + model snapshot (tables created by prior loop `20260921052333_CompanyOpeningUserMgmt`). Correct evidence: (a) Migrations dir count = 17 (35 files = 17×2 + snapshot); (b) latest = `20260922084832_PostingReferenceHarden` (2026-09-22) predates loop commits; (c) zero NEW migration file, zero new table/column for this fix — the 134 hits are expected pre-existing entity model names, not this loop's schema surface. State this explicitly in the design note or auditor WARNs on the literal PLAN phrasing.

**D6. Test discovery gotchas (all verified)**
- `BaseEntity.Id` public setter (BaseEntity.cs:7) — tests set `period.Id = 5` directly (fact g, line 117); no reflection/subclass needed for Id assignment.
- `InternalsVisibleTo("SmeAccounting.BankTests")` present (Application.csproj:14) — internal handler Facts testable, zero csproj edits.
- Ctor call sites: production = handler :19 (only PostOpeningBalances caller); tests = :105 (fact f) + :119 (fact g), both discard return → non-breaking. Handler ctor call sites: test :133 (fact h — MUST gain fake JE repo arg) + reflection :150-153 (fact i — param assert only). Api = 0 hits.
- Explicit `using SmeAccounting.Application.Handlers;` already present (JournalEntrySourceTests.cs:2) — avoids CS0246 (setsource-caller-fix lesson).
- Fact (i) shape change `void`→`async Task` required for behavioral asserts (Handle is async).
- Design doc path: `docs/OpeningBalance-Persist-Design-2026.md` does NOT exist yet (verified) — G1 creates it; exact path mandatory (auditor WARNs on mismatch).

## Environment & Integration
*(verified live 2026-09-23 — all items below confirmed against source/DB, not assumed)*

**E1. Gates baseline — cited from `loop-stack/setsource-caller-fix_DONE/REPORT.md` (just-verified prior loop, commit tail re-confirm NOT needed):**
- Build: 0 warnings, 0 errors (`TreatWarningsAsErrors=true`)
- Architecture tests: 22/22
- BankTests: 54/54 (45 pre-existing + 9 new SetSource guard Facts)
- REPORT.md is the authoritative citation; no need to re-run gates or inspect commit tail for this loop's baseline.

**E2. Test projects layout:**
- `tests/SmeAccounting.BankTests/` — refs Domain + Application only; xunit 2.9.3, xunit.runner.visualstudio 3.1.4, TestSdk 17.14.1, coverlet 6.0.4; `IsPackable=false`; `<Using Include="Xunit"/>`. This loop extends it (JournalEntrySourceTests.cs + Fakes.cs).
- `tests/SmeAccounting.ArchitectureTests/` — NetArchTest.Rules 1.3.2; scans src assemblies only, so test-project changes never affect the 22/22 count.
- **InternalsVisibleTo confirmed:** `SmeAccounting.Application.csproj:14` → `<InternalsVisibleTo Include="SmeAccounting.BankTests" />` — internal `PostOpeningBalancesHandler` Facts testable with zero csproj edits (setsource-caller-fix lesson).

**E3. Dev DB state (live psql, `sme_acct_dev` @ 172.21.208.1, 2026-09-23):**
- `journal_entries` = 0 rows; `posting_references` = 0 rows; `opening_balance_periods` = 0 rows; `opening_balance_entries` = 0 rows.
- **No backfill concern** — dev DB is empty for all four tables; the JE-persist fix writes new rows only, nothing to migrate/backfill.

**E4. Migration posture — NO migration for this fix:**
- `journal_entries` table exists since `InitialCreate` (20260916051341, line 73) with ALL mapped columns already present: id, entry_number varchar(50), date timestamptz, period_id bigint, description varchar(500), source_type varchar(100) nullable, source_id bigint nullable, posted_by varchar(100), posted_at timestamptz, is_posted bool, xmin.
- 17 migrations total; latest = `20260922084832_PostingReferenceHarden` (2026-09-22) — predates this loop's commits.
- `opening_balance_periods`/`opening_balance_entries` tables created in `20260921052333_CompanyOpeningUserMgmt`.
- Fix = handler Add + domain return type only → zero EF config/DbContext change → zero schema surface. No-migration evidence pattern (setsource-caller-fix task 3): Migrations-dir count + latest-migration timestamp + grep over Migrations.

**E5. DI — confirmed `DependencyInjection.cs:29`:**
- `services.AddScoped<IJournalEntryRepository, EfJournalEntryRepository>();` — `EfJournalEntryRepository` already registered. Handler ctor gains `IJournalEntryRepository` param → zero DI churn, zero DbContext change.

**E6. Integration surface — `PostOpeningBalances` void signature consumers (exhaustive):**
- Domain: `OpeningBalancePeriod.PostOpeningBalances` (`OpeningBalancePeriod.cs:59`, `void`) — the method itself.
- Application: `PostOpeningBalancesHandler.cs:19` — the ONLY production caller.
- Tests: `JournalEntrySourceTests.cs:105` (Throws fact) + `:119` (Posts fact) — both discard the return value today, so `void`→`JournalEntry` return-type change is non-breaking for them.
- Api: grep over `src/SmeAccounting.Api` for `PostOpeningBalances|OpeningBalance` = 0 hits — no controller dispatches this command; handler is MediatR-wired only.
- Conclusion: exactly 3 call sites total (1 handler + 2 test sites), matching R2. Return-type change touches all 3; test sites need no edit for the signature change itself (fact (h) needs the new fake repo ctor arg per R3).

## Task-Specific Research — [G2] verification criteria
*(all line numbers re-verified against source 2026-09-23 — binding spec = `docs/OpeningBalance-Persist-Design-2026.md` §2/§4/§6)*

**1. Exact signature change + return placement**
- `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:59` — `public void PostOpeningBalances(string postedBy, DateTimeOffset postedAt)` → `public JournalEntry PostOpeningBalances(string postedBy, DateTimeOffset postedAt)`.
- `return journalEntry;` lands IMMEDIATELY AFTER `journalEntry.Post(postedBy, postedAt)` (line 88), BEFORE period flags `IsPosted = true;` / `Status = PeriodStatus.Closed;` (lines 90-91) and event `AddDomainEvent(new OpeningBalancesPosted(...))` (line 93). Design §2: JE fully formed at :88 (`IsPosted=true` set inside `Post()`, JournalEntry.cs:70; lines balanced — Post validates); period mutations :90-93 touch the PERIOD, not the JE — placement before/after them behaviorally identical; lock "after Post()" for minimal diff adjacency.
- Diff = exactly 2 lines in the domain file: line 59 signature + line 89 `return journalEntry;`. NO event change, NO guard change (fail-fast `Id <= 0` :76-77 already precedes JE construction :80 + SetSource :81; hardened SetSource guards pass naturally on persisted path).

**2. Every site touching the changed signature TODAY (exhaustive — grep over src/ + tests/ + Api, verified)**
- **No `OpeningBalance*Tests.cs` file exists** — glob `tests/**/*OpeningBalance*` = 0 files. BankTests files: Fakes.cs, PostingReferenceAggregateTests.cs, BankAggregateTests.cs, PostingReferenceRepositoryTests.cs, JournalEntrySourceTests.cs, PaymentMethodAggregateTests.cs, PostingReferenceCqrsTests.cs. The ONLY test file touching `PostOpeningBalances` is `JournalEntrySourceTests.cs`.
- Method call sites (3 total, all verified):
  1. `PostOpeningBalancesHandler.cs:19` (Application — only production caller)
  2. `JournalEntrySourceTests.cs:105` (fact f, `PostOpeningBalances_TransientPeriod_IdZero_ThrowsDomainException`) — discards return → non-breaking
  3. `JournalEntrySourceTests.cs:119` (fact g, `PostOpeningBalances_PersistedPeriod_RealId_PostsUnchanged`) — discards return → non-breaking
- Api = 0 hits; Infrastructure = 0 hits; Domain = the method definition itself only. No other caller anywhere.
- Handler-ctor call sites (G3 context, NOT touched in G2): test `:133` (fact h — only ctor call site) + reflection `:150-153` (fact i — param-type assert only, no ctor call). Fakes.cs NOT touched in G2 (`FakeJournalEntryRepository` is G3).
- C# legality check: discarding a return value is legal — facts f/g compile unchanged against the new signature. Zero test edits needed for the signature change itself.

**3. NEW Facts to add (≥2 per gates — design §4 "split into ≥2 Facts"; recommend 3)**
All in `JournalEntrySourceTests.cs`, all using the persisted-period pattern from fact g (`period.Id = 5;` — BaseEntity.Id public setter, BaseEntity.cs:7). `using SmeAccounting.Domain.Entities;` (:3) + `using SmeAccounting.Domain.ValueObjects;` (:7) already present — zero new usings.
- **Fact 1 — return-value correctness** (name suggestion `PostOpeningBalances_ReturnsJournalEntry_SourceAndPosted`): `var journalEntry = period.PostOpeningBalances("tester", TestDate);` then assert `Assert.NotNull(journalEntry)`, `Assert.Equal("OpeningBalance", journalEntry.SourceType)`, `Assert.Equal(period.Id, journalEntry.SourceId)` (== 5), `Assert.True(journalEntry.IsPosted)`. This is the "returned JE == constructed JE" contract: SourceType literal "OpeningBalance" (SetSource :81), SourceId == period.Id, IsPosted after Post (:88).
- **Fact 2 — balanced lines** (name suggestion `PostOpeningBalances_ReturnsJournalEntry_BalancedLines`): same setup, assert `Assert.Equal(2, journalEntry.Lines.Count)` (one per AddEntry) and `Assert.Equal(journalEntry.Lines.Sum(l => l.Debit.Amount), journalEntry.Lines.Sum(l => l.Credit.Amount))` (== 10m each for NewBalancedPeriod). `Lines` is public (`JournalEntry.cs:20`), `Debit/Credit.Amount` public (used in ValidateBalance :77-78).
- **Fact 3 — transient JE Id** (name suggestion `PostOpeningBalances_ReturnsJournalEntry_TransientIdZero`): assert `Assert.Equal(0, journalEntry.Id)` — the returned JE is NOT persisted by the domain (zero-NuGet, no repo); Id 0 = transient, EF assigns real Id during G3 handler SaveChanges. Documents the G3 contract (handler must Add+Save). Stable assertion — domain can never persist.
- **TRAP — do NOT write a "transient PERIOD returns JE" fact**: `Id <= 0` fail-fast (:76-77) throws before JE construction — a period with Id=0 can never reach the return (fact f already covers the throw). "Transient" in the criteria means the returned JE's own Id (0, not persisted), not the period.
- Fact count math: 54 pre-existing (verified: BankAggregateTests 13 + JournalEntrySourceTests 9 + PaymentMethodAggregateTests 14 + PostingReferenceAggregateTests 6 + PostingReferenceCqrsTests 10 + PostingReferenceRepositoryTests 2 = 54) + 3 new = 57 green. Gate is ≥56 (54 + ≥2) — 3 Facts clears it.

**4. RED verification method for a void→return change — compiler error IS the RED (justified)**
- Mechanism: each new Fact captures the return (`var journalEntry = period.PostOpeningBalances(...)`). Against the stale `void` signature this is **CS0815 "Cannot assign void to an implicitly-typed variable"** — the test project fails to COMPILE, so the Facts cannot run, let alone pass. `dotnet build SmeAccounting.sln` (or `dotnet test tests/SmeAccounting.BankTests/`) fails at the new Fact lines → RED.
- Why the alternative ("behavior-first tests failing on stale signature") is impossible/meaningless here: return-value assertions cannot be written against a void method (CS0815 is the only possible failure); side-effect assertions (IsPosted/Status) already PASS on the stale signature (fact g covers them) — they'd be false-green, not RED. The compiler IS the test runner for a signature contract change.
- RED evidence to record: the CS0815 build-failure output (file + line of each new Fact) captured BEFORE the GREEN edit. Verifier re-checks by confirming the RED commit (tests only) fails to build and the GREEN commit (signature + return) builds 0/0 with all Facts green. Precedent: setsource-caller-fix G2 recorded which Facts failed RED (4/9) — here the failure is compile-level, so the recorded artifact is the build error, not a failed-assertion list.
- GREEN: change `void` → `JournalEntry` (:59) + `return journalEntry;` after :88. Facts compile and pass (traced: Id=5 path passes all guards, Post validates 10==10, all 3 Fact assertions hold).

**5. No-migration + no-touch + gates**
- **G2 touches exactly 2 files**: `OpeningBalancePeriod.cs` (2 lines: signature :59 + return :89) + `JournalEntrySourceTests.cs` (3 new Facts). NO handler change (G3), NO Fakes.cs change (G3), NO event change, NO guard change, NO EF/DbContext/DI change, NO command/controller change.
- **No migration**: domain-only in-memory change — zero schema surface. Evidence pattern (corrected — do NOT use literal PLAN "grep = 0 hits"): Migrations dir count = 17 (35 files = 17×2 + snapshot), latest = `20260922084832_PostingReferenceHarden` (2026-09-22) predates loop commits, zero NEW migration scaffolded; `grep -ri openingbalance` over Migrations = 134 pre-existing property-name hits (OpeningBalancePeriod/Entry/Mapping in Designer/snapshot from prior loop `20260921052333_CompanyOpeningUserMgmt`) — expected, NOT this loop's surface.
- **Gates**: (a) `dotnet build SmeAccounting.sln` 0 warnings/0 errors (TreatWarningsAsErrors) — RED build failure expected pre-GREEN, 0/0 post-GREEN; (b) `dotnet test tests/SmeAccounting.ArchitectureTests/` 22/22 (NetArchTest scans src assemblies only — test-project changes never affect count); (c) `dotnet test tests/SmeAccounting.BankTests/` 54 pre-existing + 3 new = 57 green (gate ≥56); (d) no-migration evidence per above.
- FAIL looks like: return placed before Post() or after event; any caller edited for the signature change (none needed); a transient-period return Fact (throws — fact f territory); Fakes.cs or handler touched in G2; migration scaffolded; arch rule broken; new Facts not capturing the return (a discard-style Fact would false-green on stale signature — not a valid RED).

## Task-Specific Research — [G3] verification criteria
*(all line numbers re-verified against source 2026-09-23 — binding spec = `docs/OpeningBalance-Persist-Design-2026.md` §3/§4; NOTE: G2's 3 new Facts shifted JournalEntrySourceTests.cs line numbers — RESEARCH [G2]/[G1] refs to :128-156 are STALE, current numbers below)*

**1. Exact handler change — `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs` (25 lines, internal sealed, primary ctor)**
- Ctor today (:7-9): `(IOpeningBalancePeriodRepository periodRepository, IUnitOfWork unitOfWork)` — 2 params, NO `IJournalEntryRepository` (grep `new PostOpeningBalancesHandler` = 1 test site only, :175; production wiring is MediatR DI). Target: 3rd param APPENDED at end → `(IOpeningBalancePeriodRepository periodRepository, IUnitOfWork unitOfWork, IJournalEntryRepository journalEntryRepository)` (backwards-compatible expansion pattern).
- Body flow (verified): :16-17 `var period = await periodRepository.GetByIdAsync(request.PeriodId) ?? throw new KeyNotFoundException(...)`; :19 `period.PostOpeningBalances(request.PostedBy, request.PostedAt);` (currently DISCARDS return — G2 made it return JournalEntry); :21 `await unitOfWork.SaveChangesAsync(cancellationToken);` (already awaited ✓); :23 `return new PostOpeningBalancesResult(true);`.
- Target body: :19 → `var journalEntry = period.PostOpeningBalances(request.PostedBy, request.PostedAt);` then NEW line `await journalEntryRepository.AddAsync(journalEntry);` BETWEEN :19 and :21 (BEFORE SaveChangesAsync — JE new-untracked until AddAsync; Add-after-Save = the current bug). :21 SaveChangesAsync unchanged (same UoW, EF assigns JE Id during Save). :23 return unchanged.
- Handler does NOT call SetSource — returned JE already carries `SourceType=="OpeningBalance"`, `SourceId==period.Id` (SetSource inside domain :81). Handler needs only the JE reference for AddAsync.
- Command shape verified: `PostOpeningBalancesCommand(long PeriodId, string PostedBy, DateTimeOffset PostedAt) : IRequest<PostOpeningBalancesResult>`; `PostOpeningBalancesResult(bool Success)` — matches test usage `new PostOpeningBalancesCommand(1, "tester", TestDate)`.

**2. Fact (i) flip — CURRENT location `JournalEntrySourceTests.cs:188-198` (NOT :146-156 — G2 shifted; RESEARCH [G1] D3 refs stale)**
- Today: `PostOpeningBalancesHandler_DiscardsJournalEntry_NoJournalEntryRepository` (:189-198), `public void`, reflection `GetConstructors().Single().GetParameters()` (:192-195), `Assert.DoesNotContain(parameters, p => p.ParameterType == typeof(IJournalEntryRepository))` (:197).
- Target: rename → `PostOpeningBalancesHandler_PersistsJournalEntry_AddsToRepository`; `public void` → `public async Task` (Handle is async, like fact (h)); construct handler with fake JE repo; assert:
  - Ctor HAS `IJournalEntryRepository` param — reflection `Assert.Contains(parameters, p => p.ParameterType == typeof(IJournalEntryRepository))` (keep — cheap, explicit) OR drop for behavioral asserts (design §4 allows either).
  - `fakeJournalEntryRepository.Stored` has exactly 1 JE: `Assert.Single(...)` then `SourceType == "OpeningBalance"`, `SourceId == period.Id`, `IsPosted == true`.
  - `unitOfWork.SaveCalledCount == 1`.
- Optional: `journalEntry.Id = 5` post-Add (BaseEntity.Id public setter, BaseEntity.cs:7) to simulate EF handoff — simulates, doesn't test, EF. FakeUnitOfWork assigns NO Ids (matches all fakes).
- Fact count: renamed in place → net 0 count change. BankTests stays 57/57 (54 + 3 G2 Facts).

**3. Fact (h) collateral — CURRENT location `JournalEntrySourceTests.cs:169-186` (NOT :128-144 — stale)**
- Ctor call at **:175** `new PostOpeningBalancesHandler(periodRepository, unitOfWork)` → `new PostOpeningBalancesHandler(periodRepository, unitOfWork, journalEntryRepository)` (add fake JE repo arg). Grep confirms :175 is the ONLY handler-ctor call site in tests (fact (i) uses reflection, no ctor call).
- Fact (h) pattern to copy: `var periodRepository = new FakeOpeningBalancePeriodRepository(); var unitOfWork = new FakeUnitOfWork();` + NEW `var journalEntryRepository = new FakeJournalEntryRepository();`; `await periodRepository.AddAsync(period); period.Id = 1;` (fact (h) uses Id=1, NOT 5 — JE SourceId will be 1; fact (i) flip can use same Id=1 pattern or 5 like G2 facts — assert `SourceId == period.Id` whatever it is).
- Fact (h) asserts unchanged: `result.Success`, `SaveCalledCount == 1`, `period.IsPosted`, `Status == Closed`. Optional extra: JE stored (Stored count 1) — but that's fact (i)'s job; keep fact (h) minimal.

**4. FakeJournalEntryRepository exact shape — `tests/SmeAccounting.BankTests/Fakes.cs`**
- Port verified `IJournalEntryRepository.cs:5-9`: `GetByIdAsync(long id)`, `GetAllAsync()`, `AddAsync(JournalEntry entry)` — NO `GetBySourceAsync` (that's IPostingReferenceRepository-only). Fake must implement ALL 3 port members.
- Copy `FakePostingReferenceRepository` shape (Fakes.cs:50-67: `List<T> _items`, FirstOrDefault GetById, AddAsync add + `Task.CompletedTask`, `Stored => _items`) — but FakePostingReferenceRepository has NO GetAllAsync, so ADD it: `public Task<IReadOnlyList<JournalEntry>> GetAllAsync() => Task.FromResult<IReadOnlyList<JournalEntry>>(_items.ToList());` (design §4 exact shape lists it explicitly).
- Exact target: `internal sealed class FakeJournalEntryRepository : IJournalEntryRepository` with `List<JournalEntry> _items`; `GetByIdAsync` = FirstOrDefault by Id; `GetAllAsync` = ToList; `AddAsync` = add + `Task.CompletedTask`; `Stored => _items`. NO SaveCalledCount on the fake repo — save tracking lives on `FakeUnitOfWork` (Fakes.cs:91-99: `SaveCalledCount` + `SaveChangesAsync` → `Task.FromResult(1)`, verified exists ✓).
- Usings: Fakes.cs already has `using SmeAccounting.Domain.Entities;` (:1) + `using SmeAccounting.Domain.Ports;` (:2) — JournalEntry + IJournalEntryRepository resolve, zero new usings.

**5. Handler test file — no new file needed**
- Handler Facts (h) + (i) already live in `JournalEntrySourceTests.cs` — flip/extend in place. No separate HandlerTests file exists; `PostingReferenceCqrsTests.cs` is the CQRS-pattern precedent but NOT needed (facts h/i are already here). G3 touches exactly 3 files: `PostOpeningBalancesHandler.cs` + `JournalEntrySourceTests.cs` + `Fakes.cs`.

**6. RED strategy — compile-error RED (CS7036), compiler IS the test runner (G2 CS0815 precedent)**
- Mechanism: flipped fact (i) + extended fact (h) both call `new PostOpeningBalancesHandler(periodRepository, unitOfWork, journalEntryRepository)` against the stale 2-param ctor → **CS7036 "There is no argument given that corresponds to the required parameter 'journalEntryRepository'"** at :175 + fact (i) ctor call. Test project fails to COMPILE → RED. Record the CS7036 build output (file + lines) BEFORE the GREEN edit.
- Why not runtime-RED: keeping only the reflection `Assert.Contains` would compile against stale ctor and fail at runtime — valid but weaker; behavioral asserts (Stored/SaveCalledCount) require constructing the handler, which forces the compile error anyway. Compile-error RED is deterministic + matches G2 precedent (CS0815).
- GREEN: add 3rd ctor param + capture `var journalEntry` + `await journalEntryRepository.AddAsync(journalEntry)` before :21. Facts compile and pass (traced: period.Id=1/5 path passes all guards, JE returned with SourceType/SourceId/IsPosted, AddAsync stores 1, SaveCalledCount 1).

**7. No-touch + gates**
- **G3 touches exactly 3 files**: `PostOpeningBalancesHandler.cs` (Application — ctor + 2 body lines) + `JournalEntrySourceTests.cs` (fact (i) flip :188-198, fact (h) :175 arg) + `Fakes.cs` (FakeJournalEntryRepository). NO EF/DbContext/DI change (`EfJournalEntryRepository` registered `DependencyInjection.cs:29` — ctor param resolves via existing registration), NO command/validator/result change, NO controller (Api grep = 0 hits), NO event/guard change, NO migration.
- **No-migration evidence** (verified live): Migrations dir = 35 files = 17×2 + snapshot; latest = `20260922084832_PostingReferenceHarden` (2026-09-22) predates loop commits (git log: G1 `410aa35`/`8008a09`, G2 `eaaf099`/`3b12e34` — all 2026-09-23); zero NEW migration scaffolded. `grep -ri openingbalance` over Migrations = 134 pre-existing property-name hits — NOT valid zero-evidence (G1 lesson).
- **Gates**: (a) `dotnet build SmeAccounting.sln` 0 warnings/0 errors (TreatWarningsAsErrors) — RED build failure expected pre-GREEN (CS7036), 0/0 post-GREEN; (b) `dotnet test tests/SmeAccounting.ArchitectureTests/` 22/22 (NetArchTest scans src assemblies only — test-project changes never affect count); (c) `dotnet test tests/SmeAccounting.BankTests/` 57/57 (54 pre-existing + 3 G2 Facts; fact (i) renamed + fact (h) extended in place + FakeJournalEntryRepository added = net 0 count change; gate ≥56).
- FAIL looks like: ctor param NOT appended at end (order change breaks DI resolution pattern); AddAsync after SaveChangesAsync (JE never persisted — the bug); fact (i) left asserting discard; fact (h) ctor call not updated (CS7036 persists); FakeJournalEntryRepository missing GetAllAsync (port member — CS0535 compile error); SaveCalledCount on the fake repo instead of FakeUnitOfWork; handler building/mutating JE (construction stays in domain); migration scaffolded; arch rule broken; any file beyond the 3 touched.
