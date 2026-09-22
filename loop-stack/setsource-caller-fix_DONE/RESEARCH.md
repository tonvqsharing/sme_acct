# Research Log
## Context & Prior Work
Mapped from source 2026-09-22. All paths absolute under `/home/projects/sme_acct/`.

### 1. JournalEntry.SetSource — unguarded setter (the fix target)
- `src/SmeAccounting.Domain/Entities/JournalEntry.cs:13-14` — nullable `string? SourceType` + `long? SourceId` (origin-trace cache; canonical store is `posting_references` per `docs/PostingReference-Design-2026.md:15`).
- `src/SmeAccounting.Domain/Entities/JournalEntry.cs:24-30` — ctor `(entryNumber, date, periodId, description)` takes no source params; source only via SetSource.
- `src/SmeAccounting.Domain/Entities/JournalEntry.cs:32-36` — `SetSource(string sourceType, long sourceId)` is an unconditional setter: zero guards (no null/empty/whitespace check, no `sourceId > 0`, no posted-state rejection), no `DomainException`, callable even when posted. Design spec (`docs/PostingReference-Design-2026.md:80`) requires: non-empty-type guard + `sourceId > 0` guard + reject-change-once-posted guard, all `DomainException`, stays setter (no FK semantics).
- Guard not yet added deliberately: G2 executor kept `JournalEntry.cs` zero-diff because live caller passes transient Id 0 — adding `> 0`/posted guards first breaks OpeningBalance flow (`loop-stack/.global/MEMORY.md:246`; `loop-stack/posting-reference-harden_DONE/MEMORY.md:8`; `loop-stack/posting-reference-harden_DONE/PLAN.md:14`).

### 2. Sole SetSource caller — OpeningBalancePeriod.PostOpeningBalances (transient-Id core)
- `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:78` — sole `SetSource` caller in codebase (`grep SetSource src` = definition `JournalEntry.cs:32` + this 1 caller; confirmed `docs/PostingReference-Design-2026.md:22` E1).
- Full flow `OpeningBalancePeriod.cs:59-91` `PostOpeningBalances(postedBy, postedAt)`:
  1. Guards: `IsPosted` (`:61-62`), `Status != Open` (`:64-65`), empty entries (`:67-68`), debit != credit (`:73-74`) — all `DomainException`.
  2. `:76-77` — entryNumber `$"OP-{PeriodDate:yyyyMMdd}"` (Id-free after Opening-Balances fix; no `OP-{Id}` formatting — `loop-stack/.global/MEMORY.md:177`), then `new JournalEntry(entryNumber, postedAt, FiscalPeriodId, ...)` — JE is `new`'d in-memory, never attached to a repository here.
  3. `:78` — `journalEntry.SetSource("OpeningBalance", Id)` — `Id` is the period's own PK, which is **0 when the period is transient (pre-save)** per transient-Id=0 pattern (`loop-stack/.global/MEMORY.md:180`; design E6 `docs/PostingReference-Design-2026.md:27`). Persisted periods pass real Id; new/un-saved periods pass 0. Magic string `"OpeningBalance"` is the only live SourceType literal in codebase.
  4. `:80-83` — `AddLine` per entry; `:85` — `journalEntry.Post(postedBy, postedAt)` (balance validate → state → `JournalEntryPosted` event); `:87-90` — period `IsPosted=true`, `Status=Closed`, raises minimal `OpeningBalancesPosted(Id, CompanyId, ...)` (no JournalEntryId — `loop-stack/.global/MEMORY.md:173-175`).
- Post hardened-guard behavior: `SetSource("OpeningBalance", 0)` on a transient period throws under `sourceId > 0` guard — so caller must be fixed (pass persisted Id / reorder) in the same change as the guard, or the OpeningBalance flow breaks. That ordering is this loop's core task.

### 3. JE persistence relative to SetSource — JE is currently DISCARDED (not persisted at all)
- `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs:12-24` — loads period via `periodRepository.GetByIdAsync`, calls `period.PostOpeningBalances(...)` (`:19`), then `unitOfWork.SaveChangesAsync` (`:21`) with **no repository `Add` of the JE** created inside the domain method (`OpeningBalancePeriod.cs:77-85`). Only period flags persist; JE (+ its SourceType/SourceId) is discarded. Documented as out-of-scope handler bug: design E7 (`docs/PostingReference-Design-2026.md:28`) and `loop-stack/posting-reference-harden_DONE/RESEARCH.md:109,215`. Any `> 0`-guard reconciliation that assumes "JE persisted after SetSource" must account for this: today there is no JE persist step at all — reference-row creation timing (§7: post-JE-persist when JE id assigned, `docs/PostingReference-Design-2026.md:97`) has nothing to hook onto until the discard bug is fixed (separate task per design §9 item 3).
- Design §7 rule for this loop: `posting_references` canonical, JE columns read-model cache written atomically in same UoW/handler that persists JE (`docs/PostingReference-Design-2026.md:95-96`).

### 4. Dead null/null command path — CreateJournalEntry + controller
- `src/SmeAccounting.Application/Commands/CreateJournalEntryCommand.cs:6-12` — carries optional `SourceType`/`SourceId` (`string?`, `long?`), but no `SetSource` usage in Application (grep 0 hits) and no `CreateJournalEntry*Handler` exists (design E2 `docs/PostingReference-Design-2026.md:23`).
- `src/SmeAccounting.Application/Validators/CreateJournalEntryCommandValidator.cs:1-22` — validates only PeriodId/Lines; zero source rules.
- `src/SmeAccounting.Api/Controllers/JournalEntryController.cs:39-41` — hardcodes `null, null` for source when constructing the command; source path dead end-to-end. Design §9 item 4 excludes resurrecting it in this loop (`docs/PostingReference-Design-2026.md:117`).

### 5. Guard parity reference — PostingReference hardened ctor (4 DomainExceptions)
- `src/SmeAccounting.Domain/Entities/PostingReference.cs:15-32` (post-G2 hardened) — public ctor `(companyId, journalEntryId, sourceType, sourceId)` with 4 ordered guards, all `DomainException`, zero `ArgumentNullException`:
  1. `companyId <= 0` → `"CompanyId must be greater than zero."` (`:17-18`, copies `VoucherType.cs:20-21`)
  2. `journalEntryId <= 0` → `"JournalEntryId must be greater than zero."` (`:19-20`, copies `TransactionReason.cs:21-22` VoucherTypeId guard)
  3. `string.IsNullOrWhiteSpace(sourceType)` → `"SourceType is required."` (`:21-22`)
  4. `sourceId <= 0` → `"SourceId must be greater than zero."` (`:23-24`)
- `SetSource` hardening should mirror V3+V4 messages plus a posted-state guard copying `AddLine`'s `"Cannot modify a posted journal entry."` (`JournalEntry.cs:47-48`); normative spec `docs/PostingReference-Design-2026.md:69-80` §5. Note ordering hazard: `PostOpeningBalances` calls `SetSource` (`:78`) **before** `journalEntry.Post` (`:85`), so a reject-once-posted guard does not fire on this path — but a `sourceId > 0` guard fires on every transient-period post. Caller fix and guard must land together.
- Cross-loop standards that still apply: Domain zero NuGet refs, private parameterless ctor for EF, event minimalism (Id+CompanyId+timestamp), transient Id=0 accepted at construction, identifier formatting in Application not Domain (`loop-stack/.global/MEMORY.md:13-48,169-193`).
## External Knowledge & Resources
(pending)
## Requirements & Constraints
Appended 2026-09-22 — guard/caller fix decision inputs (not the decision). All paths absolute under `/home/projects/sme_acct/`.

### R1. Persistence verdict: OpeningBalance JE is fully transient / dry-run (discarded)
- `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs:12-24`: loads period via `IOpeningBalancePeriodRepository.GetByIdAsync` (`:16`), calls `period.PostOpeningBalances(...)` (`:19`), calls `unitOfWork.SaveChangesAsync` (`:21`), returns `PostOpeningBalancesResult(true)` (`:23`). **Zero `IJournalEntryRepository` injection, zero `AddAsync(JE)` call.**
- `src/SmeAccounting.Domain/Ports/IJournalEntryRepository.cs:9` exposes `AddAsync(JournalEntry)` — exists but unused in this flow (grep `AddAsync` in `PostOpeningBalancesHandler.cs` = 0 hits).
- `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:59-91` `PostOpeningBalances` news up `JournalEntry` (`:77`), `SetSource` (`:78`), `AddLine` loop (`:80-83`), `journalEntry.Post` (`:85`) — all in-memory; method returns `void`, exposes no JE reference; JE never attached to DbContext.
- Net effect: only mutated tracked period (`IsPosted=true`, `Status=Closed`, `:87-88`) persists via UoW; JE + lines + SourceType/SourceId discarded. Matches design E7 (`docs/PostingReference-Design-2026.md:28`, §9 item 3 out-of-scope) and Context §3 of this RESEARCH.md.
- Repository tracking note: `EfOpeningBalancePeriodRepository.GetByIdAsync` (`:14-19`) uses `Include(p => p.Entries).FirstOrDefaultAsync` with **no `AsNoTracking`** → returned period is tracked, so domain mutations persist on `SaveChangesAsync`. Contrast `GetAllByCompanyAsync` (`:28-35`) which is `AsNoTracking` (read-only). `EfJournalEntryRepository.GetByIdAsync` (`:14-19`) same tracked pattern; `AddAsync` (`:29-32`) delegates to `DbSet.AddAsync`.
- UoW note: `SmeAccountingDbContext : DbContext, IUnitOfWork` (`SmeAccountingDbContext.cs:8`); `SaveChangesAsync` override (`:116-131`) calls `base.SaveChangesAsync` (`:123`) — standard EF identity assignment point: real `long` Ids materialize only after this call.

### R2. How Bank handler gets Ids (canonical create-then-return-Id pattern)
- `src/SmeAccounting.Application/Banks/Commands/CreateBankCommandHandler.cs:16-25`: `new Bank(...)` (Id=0 transient) → `await repository.AddAsync(bank)` (`:22`) → `await unitOfWork.SaveChangesAsync` (`:23`) → `return new CreateBankResult(bank.Id)` (`:25`). Real Id read **after** SaveChanges.
- `CreateOpeningBalancePeriodHandler.cs:17-25` identical shape: `new OpeningBalancePeriod(...)` → `AddAsync` → `SaveChangesAsync` → `CreateOpeningBalancePeriodResult(period.Id)`.
- Implication for this loop: any fixed flow needing a real Id (period Id is already real here since period was loaded by Id; JE Id is never real since JE never Added/Saved) must follow the same Add → SaveChanges → read-Id ordering. The period's `Id` passed at `OpeningBalancePeriod.cs:78` **is already persisted** in the handler path (loaded via `GetByIdAsync(request.PeriodId)`), so `SetSource("OpeningBalance", Id)` carries a real Id in production handler flow — the `Id=0` hazard fires only for transient (never-saved) periods posting in-memory (domain unit-test / pre-save path).

### R3. Fixed-flow options (inputs, planner/executor decides)
- **Option 1 — persist JE then SetSource with real Ids (handler owns persist):** handler injects `IJournalEntryRepository`, Adds JE, SaveChanges assigns JE Id, then SetSource/posting_reference written. Requires `PostOpeningBalances` to expose the JE (return value / out param / event payload) — currently `void` with JE as method-local. PRO: aligns with design §7 (reference row post-JE-persist when JE id assigned, `docs/PostingReference-Design-2026.md:97`) and Bank Id pattern. CON: touches design §9 item 3 discarded-JE bug explicitly marked separate-task/out-of-scope — planner must scope or split.
- **Option 2 — defer SetSource until persist (reorder inside domain or split across two UoW steps):** keep JE creation in domain but move `SetSource` call to after Add+SaveChanges (handler calls `je.SetSource("OpeningBalance", period.Id)` once both Ids real). PRO: no relaxed guard needed; hardened `> 0` guard holds unconditionally. CON: splits JE construction across domain+handler; `journalEntry.Post` (`:85`) currently runs before any persist — posted-state guard (`reject-change-once-posted`) would then block a post-persist SetSource unless ordering is Post→persist→SetSource carefully sequenced or guard scoped to pre-post changes only.
- **Option 3 — keep cache-only SetSource with relaxed guard:** leave JE transient/dry-run, soften `SetSource` (e.g. allow `sourceId == 0` transient, reject only negative; or skip guard when JE unpersisted). PRO: zero caller/handler churn, unblocks guard hardening elsewhere. CON: directly conflicts with design §5 normative `sourceId > 0` + §7 post-JE-persist timing; codifies cache holding `0` that can never join to a real row; diverges from `PostingReference` V4 parity (`SourceId must be greater than zero.`).
- Non-negotiable regardless of option: `SetSource` stays a setter (no FK semantics) per design §5 (`docs/PostingReference-Design-2026.md:80`).

### R4. Hard constraints on the fix
- Domain: zero NuGet refs; `DomainException` only (never `ArgumentNullException`) — T1 invariant pattern (`loop-stack/.global/MEMORY.md:113`).
- Guard messages (parity): `SourceType is required.` (V3) + `SourceId must be greater than zero.` (V4) from `PostingReference.cs:21-24`; posted-state guard copies `JournalEntry.AddLine` message `"Cannot modify a posted journal entry."` (`JournalEntry.cs:47-48`).
- Ordering hazard: `SetSource` (`:78`) runs **before** `journalEntry.Post` (`:85`) — posted-guard never fires on this path, but `sourceId > 0` guard fires on every transient-period post. Guard + caller fix must land atomically (same change), per G2 lesson (`loop-stack/.global/MEMORY.md:246`).
- Same-UoW atomicity (§7: `docs/PostingReference-Design-2026.md:96`): JE cache columns + canonical `posting_references` row written in the same UoW/handler that persists JE — no split-UoW drift.
- Out of scope (do not resurrect): dead null/null command path (`CreateJournalEntryCommand` optional source + `JournalEntryController.cs:39-41` hardcoded nulls, no handler — design §9 item 4).
- Magic string `"OpeningBalance"` is the sole live SourceType literal — keep verbatim if caller retained.
- Arch: 22 NetArchTest rules must stay green; controllers never reference `Domain.Entities`.

### R5. Test surface (discovery-first TDD — facts to add, existing style to copy)
- Existing template: `tests/SmeAccounting.BankTests/PostingReferenceAggregateTests.cs` (6 Facts: valid ctor + 4 guard messages + event-minimalism payload check); fakes: `tests/SmeAccounting.BankTests/Fakes.cs` (`FakeUnitOfWork` counts `SaveCalledCount`, List-backed repos, no EF InMemory per global MEMORY BankTests pattern).
- SetSource guard facts (new, `JournalEntry` aggregate): (a) valid SetSource sets SourceType/SourceId; (b) null/empty/whitespace type → `DomainException "SourceType is required."`; (c) `sourceId 0` and negative → `DomainException "SourceId must be greater than zero."`; (d) SetSource after `Post` → `DomainException "Cannot modify a posted journal entry."`; (e) SetSource before Post on unposted JE does not throw.
- Caller flow facts (new, `OpeningBalancePeriod` + handler): (f) posting a **persisted** period (Id>0) sets JE SourceId to real period Id (needs JE exposure — currently unobservable since JE discarded; test forces the exposure design decision); (g) posting a **transient** period (Id=0) under hardened guard throws `DomainException` (documents why guard+caller land together); (h) handler persists period flags via `SaveChangesAsync` (FakeUoW `SaveCalledCount==1`); (i) JE discard documented: handler stores no JE (fails until discard-bug task lands — mark `Skip` or assert-and-record rather than silently passing).
- No `SetSource` usage in Application today (grep 0 hits) — handler facts require new `IJournalEntryRepository` injection only under Option 1/2; Option 3 needs domain-only facts.
## Task-Specific Research — [G1] verification criteria
Appended 2026-09-22 — verifier/auditor checklist for G1 DESIGN.md + G2/G3 gates. All paths absolute under `/home/projects/sme_acct/`. Source-verified this pass: `JournalEntry.cs:32-36` (unguarded setter), `OpeningBalancePeriod.cs:59-91` (`:78` sole caller), `PostingReference.cs:15-32` (4-guard parity ref), `PostOpeningBalancesHandler.cs:12-24` (no JE Add), `CreateJournalEntryCommand.cs:6-12` + `JournalEntryController.cs:39-41` (dead null/null path), `tests/SmeAccounting.BankTests/PostingReferenceAggregateTests.cs` (6-Fact template) + `Fakes.cs` (`FakeUnitOfWork` pattern). Confirms [G1] option decision (Option 2 domain-only) above — no new evidence contradicts it.

### V1. Exact guard set (what PASS looks like)
- `JournalEntry.SetSource` (`src/SmeAccounting.Domain/Entities/JournalEntry.cs:32-36`), 3 guards in order, all `DomainException`, setter stays setter (no FK):
  1. `if (IsPosted)` → `"Cannot modify a posted journal entry."` (verbatim copy of `AddLine` `JournalEntry.cs:47-48`; ordered first: state before payload).
  2. `if (string.IsNullOrWhiteSpace(sourceType))` → `"SourceType is required."` (verbatim copy of `PostingReference.cs:21-22` V3).
  3. `if (sourceId <= 0)` → `"SourceId must be greater than zero."` (verbatim copy of `PostingReference.cs:23-24` V4).
- Caller fail-fast in `OpeningBalancePeriod.PostOpeningBalances` (`src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:59-91`): single pre-condition inserted after balance check (`:73-74`) and before `entryNumber` (`:76`):
  `if (Id <= 0) throw new DomainException("Cannot post opening balances before the period is persisted.");`
- `OpeningBalancePeriod.cs:78` stays verbatim: `journalEntry.SetSource("OpeningBalance", Id);` — literal kept, no reorder, `void` signature unchanged.
- FAIL looks like: any `ArgumentNullException`/relaxed `sourceId == 0` allowance (Option 3); guard-only landing without caller pre-condition (breaks transient OB flow per G2 lesson); message text differing by even punctuation.

### V2. Test list (discovery-first TDD, copy `PostingReferenceAggregateTests.cs` + `Fakes.cs` List-backed `FakeUnitOfWork`)
- SetSource facts (new `JournalEntry` aggregate tests): (a) happy — valid `SetSource("OpeningBalance", 9)` sets `SourceType`/`SourceId`; (b) empty type — null/`""`/`"  "` → `DomainException "SourceType is required."`; (c) zero + negative sourceId → `DomainException "SourceId must be greater than zero."`; (d) SetSource after `Post` → `DomainException "Cannot modify a posted journal entry."`; (e) SetSource before Post on unposted JE no-throw.
- Caller facts (new `OpeningBalancePeriod` tests): (f) transient period (`Id == 0`, never-saved) post throws `DomainException "Cannot post opening balances before the period is persisted."`; (g) persisted-Id path unchanged — period loaded by Id (handler `GetByIdAsync` flow) passes real Id through `:78` with no behavior change.
- Handler/discard facts: (h) handler persists period flags (`FakeUnitOfWork.SaveCalledCount == 1`); (i) JE discard recorded as `Skip`/assert-and-record (handler has zero `IJournalEntryRepository.AddAsync` — `PostOpeningBalancesHandler.cs:12-24`), never silently passing.
- FAIL looks like: new Facts absent (implementation without failing-first tests); fact (i) asserting JE persisted (contradicts discard-bug scope); `Assert.Throws<ArgumentNullException>` anywhere.

### V3. Files touched vs no-touch
- TOUCHED (2 files, 2 methods only): `src/SmeAccounting.Domain/Entities/JournalEntry.cs` :: `SetSource` (+3 guards); `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs` :: `PostOpeningBalances` (+1 pre-condition line). No handler change — this option explicitly requires none.
- NO-TOUCH: discard-bug fix (`PostOpeningBalancesHandler.cs` — no `IJournalEntryRepository` injection/`AddAsync`, no JE return/out-param/event change; separate task per design §9 item 3); dead null/null path (`CreateJournalEntryCommand.cs` optional source, validator, `JournalEntryController.cs:39-41` hardcoded nulls; §9 item 4); `PostingReference.*` files (parity reference only, already hardened); any EF config / migration / DI / `CompanyId`-on-JE / enum-izing SourceType / backfill.
- FAIL looks like: diff outside the 2 methods above; new DbSet/Ignore/DI line; migration scaffolded for this loop.

### V4. Regression gates (G3 verify core→edge)
- `dotnet build SmeAccounting.sln` — 0 warnings 0 errors (`TreatWarningsAsErrors=true`).
- `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 (controllers never reference `Domain.Entities`; Domain zero NuGet refs).
- `dotnet test tests/SmeAccounting.BankTests/` — 45/45 baseline green + new SetSource/caller Facts green.
- No migration: state why — domain in-memory guards + caller fail-fast reorder only, no new table/column/index/FK.
- FAIL looks like: any gate red; migration added; arch rule broken by new `using` (e.g. controller → `Domain.Entities`).
## Task-Specific Research — [G1] option decision
Decided 2026-09-22 from source (no code written). All paths absolute under `/home/projects/sme_acct/`.

### Recommendation: Option 2 scoped to domain-only (harden SetSource fully + fail-fast caller pre-condition; JE stays discarded)
- **Chosen:** hardened `SetSource` per design §5 (guards G1–G3 below) **plus** a transient-period pre-condition guard inside `OpeningBalancePeriod.PostOpeningBalances` that throws before any JE is built when `Id <= 0`. This is the domain-only half of R3 Option 2 ("defer post until persisted"): the caller never passes a transient 0 as `SourceId`, so the hardened `sourceId > 0` guard holds unconditionally with zero handler/DI/EF changes — exactly the G2 constraint ("domain + caller only, no handler/handler-DI/EF-config changes unless G1 option explicitly requires" — this option explicitly requires none).
- **Why not Option 1 (persist-then-SetSource, handler owns persist):** requires `PostOpeningBalances` to expose the JE (currently `void`, JE method-local `OpeningBalancePeriod.cs:77-85`) + handler to inject `IJournalEntryRepository.AddAsync` + SaveChanges-then-SetSource + `posting_references` row per §7. That IS the discarded-JE bug fix, explicitly a separate task (design §9 item 3, `docs/PostingReference-Design-2026.md:116`; RESEARCH.md R1/Context §3). G2 forbids handler changes unless required — Option 1 requires them, so it breaks the loop's scope/budget boundary. Revisit only in the discard-bug loop, where §7 timing (reference row post-JE-persist) finally has something to hook onto.
- **Why not Option 3 (relaxed guard, allow sourceId == 0):** directly contradicts design §5 normative `sourceId > 0` (`docs/PostingReference-Design-2026.md:80`) and V4 parity (`PostingReference.cs:23-24` `"SourceId must be greater than zero."`); codifies a cache `SourceId=0` that can never join to a real row and would need backfill later (design §9 item 7 exclusion); diverges from the `> 0` guards already shipped on `PostingReference` ctor. Zero caller churn is not worth a knowingly wrong invariant.
- **Why the domain-only Option 2 variant wins on evidence:**
  1. Handler-path Id is already real: `PostOpeningBalancesHandler.cs:16` loads the period via `GetByIdAsync(request.PeriodId)`, so `OpeningBalancePeriod.cs:78` `SetSource("OpeningBalance", Id)` already carries a persisted Id in production — the `Id=0` hazard fires only for transient (never-saved) periods posting in-memory (RESEARCH.md R2). A fail-fast `Id <= 0` guard therefore changes nothing in the live handler flow and fixes only the broken pre-save path.
  2. Atomic landing satisfies the G2 lesson: guard + caller fix land together so the new `sourceId > 0` guard never breaks the OB flow (`loop-stack/.global/MEMORY.md:246`). Transient post now throws the caller message (intentional, tested as fact (g)), not an accidental `SourceId` violation.
  3. Posted-guard ordering is safe: `SetSource (:78)` runs before `journalEntry.Post (:85)`, so the new reject-once-posted guard never fires on the OB path — it hardens only external post-post mutation, mirroring `AddLine` (`JournalEntry.cs:47-48`).
  4. Setter stays setter (no FK), Domain stays zero-NuGet/`DomainException`-only, magic string `"OpeningBalance"` kept verbatim (sole live literal, design E1).

### Exact SetSource guard set (in `src/SmeAccounting.Domain/Entities/JournalEntry.cs:32-36`, order normative)
```csharp
public void SetSource(string sourceType, long sourceId)
{
    if (IsPosted)
        throw new DomainException("Cannot modify a posted journal entry.");
    if (string.IsNullOrWhiteSpace(sourceType))
        throw new DomainException("SourceType is required.");
    if (sourceId <= 0)
        throw new DomainException("SourceId must be greater than zero.");
    SourceType = sourceType;
    SourceId = sourceId;
}
```
- G1 posted-state guard copies `AddLine` message verbatim (`JournalEntry.cs:47-48`); ordered first (state before payload, same as `AddLine`). Requires `using SmeAccounting.Domain.Exceptions;` (already present `JournalEntry.cs:2`).
- G2 type guard mirrors `PostingReference` V3 (`PostingReference.cs:21-22`); G3 id guard mirrors V4 (`:23-24`). Both messages verbatim per PLAN.md R4.
- No nullability-signature change (`string sourceType, long sourceId` stays); no FK semantics; no `ArgumentNullException`.

### Exact caller change (in `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs`, method `PostOpeningBalances`, lines 59-91)
- Insert one pre-condition after the balance check (`:73-74`) and before `entryNumber` (`:76`) — i.e. new `:75`:
```csharp
        if (Id <= 0)
            throw new DomainException("Cannot post opening balances before the period is persisted.");
```
- `OpeningBalancePeriod.cs:78` stays verbatim: `journalEntry.SetSource("OpeningBalance", Id);` — literal kept, no reorder, no signature change (`void` stays, no JE return/out-param/event change).
- Net effect: persisted periods (handler path, Id > 0) flow unchanged through SetSource→AddLine→Post; transient periods (Id == 0) fail fast with an actionable message instead of writing `SourceId=0` cache or tripping the V4 guard accidentally.
- No other file touched by this option: NOT `PostOpeningBalancesHandler.cs`, NOT `IJournalEntryRepository.cs`, NOT any EF config/migration/DI.

### What stays out (discard bug itself untouched unless chosen option requires — it does not)
- Discarded-JE fix (handler `IJournalEntryRepository.AddAsync` + SaveChanges + return/expose JE + canonical `posting_references` row per §7 timing) — separate task per design §9 item 3. Fact (i) records it as `Skip`/assert-and-record, never silently passing.
- Dead null/null command path (`CreateJournalEntryCommand` optional source + `JournalEntryController.cs:39-41` hardcoded nulls, no handler) — design §9 item 4.
- EF/migration/DI/CompanyId-on-JE/enum-izing SourceType/backfill — all per design §§6/9 exclusions.
- Test list for G1 DESIGN.md / G2 TDD (per R5, unchanged): (a) valid SetSource sets both; (b) null/empty/whitespace type → `"SourceType is required."`; (c) sourceId 0 + negative → `"SourceId must be greater than zero."`; (d) SetSource after Post → `"Cannot modify a posted journal entry."`; (e) SetSource before Post on unposted JE no-throw; (f) persisted period (Id>0) JE SourceId == real period Id (needs JE observability note — domain fact asserts via exposed JE or owned-test subclass; handler-level observability waits for discard-bug loop); (g) transient period (Id=0) post throws `DomainException` (the new caller message); (h) handler persists period flags (`FakeUnitOfWork.SaveCalledCount==1`); (i) JE discard documented (`Skip` or assert-and-record). Template: `tests/SmeAccounting.BankTests/PostingReferenceAggregateTests.cs` + `Fakes.cs` List-backed `FakeUnitOfWork` pattern.
