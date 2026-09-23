# Opening Balance → PostingReference Link — Locked Design (Canonical PR Row in PostOpeningBalancesHandler)

**Date:** 2026-09-23
**Status:** LOCKED — G2/G3 implement exactly this, no deviation
**Scope:** Design only. No code changed by this document.
**Loop:** `loop-stack/opening-balance-pr-link/` task [G1]
**Sources:** `loop-stack/opening-balance-pr-link/RESEARCH.md` (Context §§1–6, Task-Specific §[G1] D1–D6); all file:line refs absolute under `/home/projects/sme_acct/` and re-verified against source this pass.

## 1. Decision — Option B: no `GetBySourceAsync` pre-check in PostOpeningBalancesHandler

**LOCKED: the handler does NOT replicate `CreatePostingReferenceHandler`'s duplicate pre-check.** Duplicate protection for the OpeningBalance flow is already layered, in order:

1. **Sequential duplicates — domain `IsPosted` guard, pre-persistence.** `OpeningBalancePeriod.PostOpeningBalances` throws `DomainException("Opening balances are already posted.")` when `IsPosted` (`src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:61-62`), BEFORE any JE/PR creation. The handler loads the period via `GetByIdAsync` (`PostOpeningBalancesHandler.cs:17-18`), so a second POST on a posted period dies at :61-62 regardless of any pre-check. This is the primary guard.
2. **Concurrent race — xmin concurrency token on the period row, caught at save 1.** Two POSTs both load `IsPosted=false`; `PostOpeningBalances` mutates the period (`IsPosted=true`, `Status=Closed`, `OpeningBalancePeriod.cs:90-91`), so the period row IS part of save 1. The losing request's save 1 (UPDATE period + INSERT JE) hits `DbUpdateConcurrencyException` → **the losing JE never persists**. xmin rowversion is on all entities (AGENTS.md; `PostingReferenceConfiguration.cs:46-48` pattern).
3. **Unique index — last-resort DB backstop.** `IX_posting_references_company_id_source_type_source_id` unique on `(company_id, source_type, source_id)` (`20260922084832_PostingReferenceHarden.cs:24-28`; `PostingReferenceConfiguration.cs:33-34`) catches any path that bypasses the period update (e.g. manual `CreatePostingReferenceCommand`).

**Why `CreatePostingReferenceHandler`'s pre-check is NOT replicated:** that handler (`src/SmeAccounting.Application/Handlers/CreatePostingReferenceHandler.cs:17-19`) has **no domain guard** — the caller supplies arbitrary CompanyId/JournalEntryId/SourceType/SourceId, so `GetBySourceAsync` + `InvalidOperationException` is its only duplicate defense. The OpeningBalance flow already has the `IsPosted` domain guard. Replicating the pre-check here would:
- (a) add a redundant DB round-trip on every post;
- (b) be **TOCTOU-ineffective** against the concurrent race — both requests pass the pre-check before either saves, so it changes nothing the xmin token doesn't already catch;
- (c) if placed after save 1 (the natural "before PR build" spot), a throw leaves the JE already committed with no PR row — **dangling-JE partial state**. Avoiding (c) forces it to handler start (:17), where it is redundant with `IsPosted`.

**Wording for the note:** "No `GetBySourceAsync` pre-check in PostOpeningBalancesHandler. Sequential duplicates are blocked pre-persistence by the domain `IsPosted` guard (OpeningBalancePeriod.cs:61-62); the concurrent race is caught at save 1 by the xmin concurrency token on the period row (DbUpdateConcurrencyException — the losing JE never persists); the unique index (CompanyId, SourceType, SourceId) is the last-resort DB backstop. CreatePostingReferenceHandler's pre-check (CreatePostingReferenceHandler.cs:17-19) exists only because that handler lacks a domain guard; replicating it here adds a round-trip, is TOCTOU-ineffective, and risks a dangling JE if misplaced after save 1."

## 2. Handler surface — `PostOpeningBalancesHandler`

**File:** `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs` (28 lines, `internal sealed`, primary ctor)

- **4th ctor param APPENDED at end** (backwards-compatible expansion pattern, new params at end — global MEMORY:74):
  `(IOpeningBalancePeriodRepository periodRepository, IUnitOfWork unitOfWork, IJournalEntryRepository journalEntryRepository, IPostingReferenceRepository postingReferenceRepository)` (:7-10).
- **Flow** (inserted between :24 and :26):
  1. Save 1: existing `await unitOfWork.SaveChangesAsync(cancellationToken)` (:24) — EF assigns `journalEntry.Id` (identity PK).
  2. Build PR: `new PostingReference(period.CompanyId, journalEntry.Id, "OpeningBalance", period.Id)` — all 4 ctor guards pass (`PostingReference.cs:15-24`):
     - `companyId` = `period.CompanyId` (`OpeningBalancePeriod.cs:9`, ctor-guarded `> 0` at :22-23) — direct, in scope, no chain hops;
     - `journalEntryId` = `journalEntry.Id` — **> 0 only after save 1** (V2 guard `journalEntryId <= 0` → DomainException, `PostingReference.cs:19-20`, is the forcing function for the two-save shape);
     - `sourceType` = `"OpeningBalance"` — sole live SourceType literal in src (`OpeningBalancePeriod.cs:81`), free string max100 (`PostingReferenceConfiguration.cs:24-27`);
     - `sourceId` = `period.Id` — real (> 0 guaranteed by the domain fail-fast `if (Id <= 0) throw` at `OpeningBalancePeriod.cs:76-77`, which runs before JE construction).
  3. `await postingReferenceRepository.AddAsync(reference)` — same UoW.
  4. Save 2: `await unitOfWork.SaveChangesAsync(cancellationToken)` — second transaction, same DbContext.
- **Return unchanged**: `return new PostOpeningBalancesResult(true)` (:26) — `PostOpeningBalancesResult(bool Success)` only; no JE Id, no period Id exposed (RESEARCH R2).
- **Two-save shape is timing-forced**: the JE Id does not exist until save 1 completes, so the PR row cannot ride save 1. Same UoW = same DbContext, but two `SaveChangesAsync` = two DB transactions. Residual save-2-failure risk (JE committed without PR row) is theoretical for this flow — the realistic race is caught at save 1 by xmin (RESEARCH R2).
- **Shape precedent**: build → AddAsync → SaveChangesAsync, exactly `CreatePostingReferenceHandler.cs:21-28`.

## 3. Test enabler — `FakeJournalEntryRepository.AddAsync` assigns Id

**File:** `tests/SmeAccounting.BankTests/Fakes.cs`

- **Current**: `FakeJournalEntryRepository.AddAsync` (:79-83) just adds to `_items` — no Id assignment → `journalEntry.Id` stays 0 in the fake path → PR ctor V2 guard (`journalEntryId <= 0` → DomainException, `PostingReference.cs:19-20`) throws → the new PR-link fact fails at runtime.
- **Change**: `AddAsync` assigns an Id (counter-based, simulating EF identity assignment during `SaveChangesAsync`).
- **Safety**: the only JE `Id == 0` assert in the suite is fact G2-3 (`JournalEntrySourceTests.cs:166`) on the domain-created JE BEFORE the handler runs — that assert never passes through the fake, so it is unaffected.
- **Correctness**: `FakeJournalEntryRepository` is list-backed → the stored instance IS the same object the handler builds the PR from → `Stored[0].Id` (assigned) == `PR.JournalEntryId`; the assertion `JournalEntryId == stored JE Id (>0)` is exact.

## 4. Test surface — `tests/SmeAccounting.BankTests/JournalEntrySourceTests.cs`

- **fact (h)** `PostOpeningBalancesHandler_PersistsPeriodFlags_SaveCalledOnce` (:171-187): ctor call :176 gains the 4th arg (`new FakePostingReferenceRepository()`); `SaveCalledCount == 1` (:184) → **== 2** (the handler now saves twice; both facts run the full handler).
- **fact (i)** `PostOpeningBalancesHandler_PersistsJournalEntry_AddsToRepository` (:191-215): ctor call :202 gains the 4th arg; `SaveCalledCount == 1` (:214) → **== 2**; add PR-row assertion: `postingReferenceRepository.Stored` Single { `CompanyId == period.CompanyId`, `JournalEntryId == stored JE Id (>0)`, `SourceType == "OpeningBalance"`, `SourceId == period.Id` }.
- **D4 correction (locked)**: PLAN wording "existing facts (h)/(i) SaveCalledCount==1 → ==2" means **BOTH** facts update — fact (h) :184 AND fact (i) :214. Not just (i).
- **RED mechanism**: the 4th ctor param → CS1729 "does not contain a constructor that takes 4 arguments" at :176 and :202 (compile-error RED, same mechanism as opening-balance-persist G3 — global MEMORY:254). Record the actual error code + lines during G2; do not force a predicted code.
- **New PR-link fact shape** (follows fact (i)): set `period.Id = 1` via the `BaseEntity.Id` public setter (global MEMORY:250); `FakeOpeningBalancePeriodRepository` is list-backed (:88-108) → `GetByIdAsync` returns the SAME instance → the handler sees `Id=1`; run handler; assert PR row + `SaveCalledCount == 2`.
- `FakePostingReferenceRepository` (:50-67) and `FakeUnitOfWork` (:110-118) already exist — no new fakes.

## 5. No-touch list

| Area | Why untouched |
|------|---------------|
| `CreatePostingReferenceHandler.cs` / `CreatePostingReferenceCommand.cs` / `CreatePostingReferenceCommandValidator.cs` / `PostingReferenceController.cs` | Manual-path CQRS stays as-is; PR creation in the OpeningBalance flow is handler-internal (design §7 same-UoW atomic write), NOT a new MediatR command. |
| EF configurations / `SmeAccountingDbContext.cs` | `PostingReferenceConfiguration.cs` untouched — table, columns, FKs, unique index all exist. |
| `DependencyInjection.cs` | `IPostingReferenceRepository` already registered (`DependencyInjection.cs:69` `AddScoped<IPostingReferenceRepository, EfPostingReferenceRepository>()`) — zero DI churn. |
| Migrations / unique index | `posting_references` table + `company_id` + unique `(CompanyId, SourceType, SourceId)` + dual Restrict FKs exist since `20260922084832_PostingReferenceHarden` — zero schema surface. |
| Domain entities | `SetSource` (`OpeningBalancePeriod.cs:81`) and `PostOpeningBalances` untouched — zero domain diff. |

**Touched (3 files only)**: `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs` + `tests/SmeAccounting.BankTests/JournalEntrySourceTests.cs` + `tests/SmeAccounting.BankTests/Fakes.cs`.

## 6. Gates (G3 verify core→edge)

1. `dotnet build SmeAccounting.sln` — 0 warnings, 0 errors (`TreatWarningsAsErrors=true`).
2. `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 (NetArchTest scans src assemblies only; test-project changes never affect the count).
3. `dotnet test tests/SmeAccounting.BankTests/` — **≥ 58 green** (57 existing + ≥ 1 new PR-link fact).
4. **No-migration evidence — CORRECTED pattern** (grep over Migrations is INVALID — 134-style pre-existing `openingbalance`/`postingreference` hits from prior loops, global MEMORY:252):
   - (a) Migrations dir file count == **35** (17 migrations × 2 + snapshot) — verified this pass;
   - (b) latest = `20260922084832_PostingReferenceHarden` (2026-09-22) predates this loop's commits (HEAD `ae62ae4` closes opening-balance-persist);
   - (c) **zero NEW migration file** scaffolded this loop (count + `git show --stat` per loop commit — global MEMORY:256).
5. **No-touch audit**: `git show --stat` per loop commit cross-checked against §5 (zero code changes ⇒ state-files-only commits).

FAIL looks like: any gate red; a migration added for this loop; an arch rule broken; PR built BEFORE save 1 (JE Id 0 → V2 DomainException at runtime); PR AddAsync without a second save; `period.CompanyId` not used (hardcoded or chain-derived); ctor param inserted NOT at end; `SaveCalledCount` asserted == 1 in the new PR-link facts; any change to CreatePostingReferenceHandler/Command/Controller, EF configs, DbContext, DI, migrations; any new VAS / Circular 99 compliance claim.

## Sources

- `docs/PostingReference-Design-2026.md` §7 (:93-99) — `posting_references` is canonical (idempotency + audit); JE SourceType/SourceId are read-model cache only; both written atomically in the same UoW/handler that persists the JE; creation timing post-JE-persist when the JE id is assigned (reconciles `journalEntryId > 0` / `sourceId > 0` guards with the transient-Id=0 pattern); unique index is the backstop.
- `docs/OpeningBalance-Persist-Design-2026.md` §1 (:10-18) — JE-persist-first: EF assigns the JE Id during Save, so JE Id > 0 before any PR link (satisfies the V2 guard); §5 (:77) — "PR creation lives in CreatePostingReferenceHandler/CreatePostingReferenceCommand (separate command). The design §7 same-UoW atomic write (JE + canonical posting_references row) is a SEPARATE future task" — **this loop is that task**.
- `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs` (:7-26), `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs` (:9, :61-62, :76-77, :81, :90-91), `src/SmeAccounting.Domain/Entities/PostingReference.cs` (:15-24), `src/SmeAccounting.Application/Handlers/CreatePostingReferenceHandler.cs` (:17-28), `tests/SmeAccounting.BankTests/JournalEntrySourceTests.cs` (:159-215), `tests/SmeAccounting.BankTests/Fakes.cs` (:50-118), `src/SmeAccounting.Infrastructure/DependencyInjection.cs:69`, `src/SmeAccounting.Infrastructure/Migrations/20260922084832_PostingReferenceHarden.cs:24-28`, `src/SmeAccounting.Infrastructure/Persistence/Configurations/PostingReferenceConfiguration.cs:33-34`.