# Completion Report — journal-entry-handlers

## Goal
Make the Phiếu kế toán (Journal Entry) daily screen work end-to-end: implementing the two missing CQRS handlers — CreateJournalEntryCommand and PostJournalEntryCommand.

## Problem
`JournalEntryController` Create POST and Post actions sent commands with **no handlers** → runtime 500 on "Tạo phiếu mới" and "Ghi sổ". The Index screen had already been fixed in the previous slice (GetJournalEntriesQuery, commit af94908).

## What was done

| Task | Commit | Change |
|---|---|---|
| G1 CompanyId plumbing | `57e008d` | `long CompanyId` FIRST param on CreateJournalEntryCommand + validator rule + ViewModel `[Required]` + Create.cshtml input + controller passes it. 5 files, no behavior change. |
| G2 CreateJournalEntryHandler | `ff88722` | Handler: resolve VoucherType by code "JNRL" (company-scoped) → default numbering series → `JNRL000001` format → `Increment()` → `new JournalEntry` → AddLine (`Money(x, "VND")`) → AddAsync → **single** SaveChangesAsync (entry + series atomic) → `(Id, EntryNumber)`. Plus FakeVoucherTypeRepository + FakeDocumentNumberingSeriesRepository + 7 test facts. |
| G3 PostJournalEntryHandler | `e9ec524` | Handler: GetByIdAsync null-guard → `entry.Post("system", clock.Now)` (no IPostingService — dead port) → SaveChangesAsync → `(Id, PostedAt)`. Plus FakeClock + 4 test facts. |
| G4 Gates + evidence | (no commit) | build 0/0, arch 22/22, bank 72/72, zero migrations, zero Domain/Infrastructure touches. |

## Daily screen now fully wired
```
Create POST → CreateJournalEntryCommand(CompanyId, Date, PeriodId, Description, null, null, Lines)
  → GetByCodeAsync("JNRL", companyId) → GetDefaultAsync(vt, companyId)
  → entryNumber = Prefix + NextNumber:D(Padding) → Increment() → JournalEntry → AddLine(VND)
  → AddAsync → SaveChangesAsync (single, atomic) → (Id, EntryNumber)
Post(id) → PostJournalEntryCommand(id)
  → GetByIdAsync → entry.Post("system", clock.Now) → SaveChangesAsync → (Id, PostedAt)
```

## Gates (final)
- `dotnet build SmeAccounting.sln` — **0 warnings / 0 errors**
- Architecture tests — **22/22**
- Bank tests — **72/72** (was 61 at loop start; +11 net: 7 Create + 4 Post)
- Migrations — **35 files unchanged**, latest `20260922084832_PostingReferenceHarden` predates loop
- No-touch — zero Domain/, zero Infrastructure/, zero IPostingService, JournalEntry entity untouched

## Design decisions
- **No IPostingService**: the port has no Infrastructure implementation — handlers call domain `Post()` directly (PostOpeningBalancesHandler precedent).
- **VoucherType code "JNRL"**: `VoucherCategory.Journal`; company-scoped lookup mandatory; null-guard because no seed data exists (screen requires setup first).
- **Numbering series is the serialization point**: entry_number has no unique index; series row xmin concurrency token; single save makes entry+series atomic.
- **PostedBy "system"**: no user context in Api layer (no claims/session); PostJournalEntryCommand carries no user identity.
- **CompanyId is form-driven** (no claims resolution): consistent with all 30 other Create commands; first view in project with a visible CompanyId input.

## Known gaps (out of scope, recorded)
- No period-open check in create/post (no FK on period_id; domain Post() validates balance only).
- Unbalanced entry persists at Create (validator has no amount rules; balance enforced at Post → ValidateBalance).
- VoucherType "JNRL" must exist per company before first entry (no seeder).

## Loop bookkeeping
- 4 tasks, 4 verified (auditor CLEAN + verifier VERIFIED_PASS each; final ALL_DONE).
- State-only commits live in loop dir `journal-entry-handlers_DONE/`.
- Cross-loop lessons appended to `loop-stack/.global/MEMORY.md`.