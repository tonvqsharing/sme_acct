# SetSource + Caller Fix — Locked Design (Option 2, Domain-Only)

**Date:** 2026-09-22
**Status:** LOCKED — G2 implements exactly this, no deviation
**Scope:** Design only. No code changed by this document.
**Loop:** `loop-stack/setsource-caller-fix/` task [G1]

## 1. Decision

**Option 2, domain-only variant: harden `JournalEntry.SetSource` fully AND fail-fast the caller in `OpeningBalancePeriod.PostOpeningBalances` before any `JournalEntry` is built. The JE stays discarded (transient/dry-run); live persisted-Id flow is unchanged; transient (Id=0) post fails fast — intentional.**

Rationale:

1. The production handler path already carries a real Id. `PostOpeningBalancesHandler` loads the period via `GetByIdAsync(request.PeriodId)`, so `SetSource("OpeningBalance", Id)` at `OpeningBalancePeriod.cs:78` already passes a persisted Id in live flow. The `Id=0` hazard fires only for transient (never-saved) periods posting in-memory (domain unit-test / pre-save path).
2. Guard + caller land atomically. The new `sourceId > 0` guard would otherwise break the OpeningBalance flow on every transient-period post (prior G2 lesson). A fail-fast `Id <= 0` pre-condition makes transient post throw the caller message deliberately instead of tripping the V4 guard accidentally.
3. Posted-guard ordering is safe. `SetSource (:78)` runs before `journalEntry.Post (:85)`, so the new reject-once-posted guard never fires on the OpeningBalance path — it hardens only external post-post mutation, mirroring `AddLine`.
4. Setter stays setter (no FK semantics), Domain stays zero-NuGet / `DomainException`-only, magic string `"OpeningBalance"` kept verbatim (sole live SourceType literal).

## 2. Rejected Options (with reasons)

### Rejected: Option 1 — persist JE then SetSource with real Ids (handler owns persist)

Requires `PostOpeningBalances` to expose the JE (currently `void`, JE is a method-local at `OpeningBalancePeriod.cs:77-85`) plus handler injection of `IJournalEntryRepository.AddAsync`, then SaveChanges-then-SetSource, plus a canonical `posting_references` row per design §7 timing. That IS the discarded-JE bug fix, explicitly a separate task (design §9 item 3, `docs/PostingReference-Design-2026.md`). It forces handler/DI changes this loop's G2 scope forbids ("domain + caller only, no handler/handler-DI/EF-config changes"). Revisit only in the discard-bug loop, where §7 timing (reference row post-JE-persist) has something to hook onto.

### Rejected: Option 3 — keep cache-only SetSource with relaxed guard (allow `sourceId == 0`)

Directly contradicts design §5 normative `sourceId > 0` and V4 parity (`PostingReference.cs:23-24` `"SourceId must be greater than zero."`). Codifies a cache `SourceId=0` that can never join to a real row and would need backfill later. Diverges from the `> 0` guards already shipped on the `PostingReference` constructor. Zero caller churn is not worth a knowingly wrong invariant.

## 3. Exact Guard Set — `JournalEntry.SetSource`

**File:** `src/SmeAccounting.Domain/Entities/JournalEntry.cs`
**Method:** `SetSource(string sourceType, long sourceId)` (lines 32-36, replaced in full)
**Order normative. All `DomainException`. No signature change. No FK semantics. `using SmeAccounting.Domain.Exceptions;` already present (line 2).**

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

Message provenance (verbatim copies):

| # | Guard | Message | Source |
|---|-------|---------|--------|
| G1 | `if (IsPosted)`, ordered first (state before payload, same as `AddLine`) | `Cannot modify a posted journal entry.` | `JournalEntry.cs:47-48` |
| G2 | `if (string.IsNullOrWhiteSpace(sourceType))` | `SourceType is required.` | `PostingReference.cs:21-22` (V3) |
| G3 | `if (sourceId <= 0)` | `SourceId must be greater than zero.` | `PostingReference.cs:23-24` (V4) |

Forbidden: any `ArgumentNullException`, any relaxed `sourceId == 0` allowance, any message text differing by even punctuation, any guard-only landing without the caller pre-condition (§4).

## 4. Caller Change Spec — `OpeningBalancePeriod.PostOpeningBalances`

**File:** `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs`
**Method:** `PostOpeningBalances(string postedBy, DateTimeOffset postedAt)` (lines 59-91)
**Change:** insert exactly one pre-condition after the balance check (lines 73-74) and before `entryNumber` (line 76) — i.e. new line 75:

```csharp
        if (Id <= 0)
            throw new DomainException("Cannot post opening balances before the period is persisted.");
```

**Line 78 stays verbatim — no reorder, no literal change, no signature change:**

```csharp
        journalEntry.SetSource("OpeningBalance", Id);
```

Net effect:

- Persisted periods (handler path, `Id > 0`): flow unchanged — SetSource → AddLine loop → `journalEntry.Post` → `IsPosted=true`, `Status=Closed`, `OpeningBalancesPosted(Id, CompanyId, ...)` event.
- Transient periods (`Id == 0`): fail fast with the actionable caller message before any JE is built, instead of writing a `SourceId=0` cache or tripping the V4 guard accidentally.
- `void` signature unchanged: no JE return / out-param / event-payload change.

## 5. Test List (discovery-first TDD for G2)

**Template to copy:** `tests/SmeAccounting.BankTests/PostingReferenceAggregateTests.cs` (6 Facts: valid ctor + 4 guard messages + event-minimalism payload check) and `tests/SmeAccounting.BankTests/Fakes.cs` (`FakeUnitOfWork` with `SaveCalledCount`, List-backed repos, no EF InMemory).

**SetSource facts (new `JournalEntry` aggregate tests):**

- (a) happy — valid `SetSource("OpeningBalance", 9)` sets `SourceType` and `SourceId`.
- (b) empty type — `null` / `""` / `"  "` each throw `DomainException` with `SourceType is required.`
- (c) zero + negative sourceId — `0` and `-1` each throw `DomainException` with `SourceId must be greater than zero.`
- (d) SetSource after `Post` throws `DomainException` with `Cannot modify a posted journal entry.`
- (e) SetSource before Post on an unposted JE does not throw.

**Caller facts (new `OpeningBalancePeriod` tests):**

- (f) transient period (`Id == 0`, never-saved) post throws `DomainException` with `Cannot post opening balances before the period is persisted.`
- (g) persisted-Id path unchanged — period loaded by Id (handler `GetByIdAsync` flow) passes the real Id through line 78 with no behavior change.

**Handler/discard facts:**

- (h) handler persists period flags — `FakeUnitOfWork.SaveCalledCount == 1`.
- (i) JE discard recorded as `Skip` / assert-and-record — handler has zero `IJournalEntryRepository.AddAsync` (`PostOpeningBalancesHandler.cs:12-24`); never silently passing, never asserting JE persisted (that contradicts discard-bug scope).

**Test FAIL conditions:** new Facts absent (implementation without failing-first tests); fact (i) asserting JE persisted; `Assert.Throws<ArgumentNullException>` anywhere.

## 6. No-Touch List

- **Discard bug itself:** `PostOpeningBalancesHandler.cs` — no `IJournalEntryRepository` injection, no `AddAsync`, no JE return/out-param/event change. Separate task per design §9 item 3.
- **Dead null/null path:** `CreateJournalEntryCommand.cs` optional source, `CreateJournalEntryCommandValidator.cs` (zero source rules), `JournalEntryController.cs:39-41` hardcoded nulls, no `CreateJournalEntry*Handler`. Design §9 item 4 excludes resurrecting it.
- **`PostingReference.*` files:** parity reference only, already hardened — read, do not edit.
- **EF / migrations / DI:** no EF config change, no migration scaffold, no new DbSet/Ignore/DI line, no `CompanyId`-on-JE, no enum-izing SourceType, no backfill.
- **Touch boundary (G2):** exactly 2 files, 2 methods — `JournalEntry.cs::SetSource` (+3 guards) and `OpeningBalancePeriod.cs::PostOpeningBalances` (+1 pre-condition). Any diff outside these 2 methods fails review.

## 7. Gates (G3 verify core→edge)

1. `dotnet build SmeAccounting.sln` — 0 warnings, 0 errors (`TreatWarningsAsErrors=true`).
2. `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 (controllers never reference `Domain.Entities`; Domain zero NuGet refs).
3. `dotnet test tests/SmeAccounting.BankTests/` — baseline green plus new SetSource/caller Facts green.
4. **No migration:** state why — domain in-memory guards plus caller fail-fast reorder only; no new table/column/index/FK.

FAIL looks like: any gate red; a migration added for this loop; an arch rule broken by a new `using` (e.g. controller → `Domain.Entities`).
