# Loop Report — opening-balance-persist

## Goal
Fix OpeningBalance handler: persist JournalEntry (Add to repo, Save via UoW, use assigned Id) before linking to PostingReference; update fact (i) test in same change; core to edge following discovery-first TDD rules.

## Mode
patch | Git auto-commit: yes

## Result
ALL DONE — 4/4 tasks verified.

## Tasks
- [x] [G1] Design note → docs/OpeningBalance-Persist-Design-2026.md (JE persist-first, Add-before-Save)
- [x] [G2] Domain TDD — OpeningBalancePeriod.PostOpeningBalances void→JournalEntry (return at :95, CS0162 trap avoided)
- [x] [G3] Handler TDD — 3rd ctor param IJournalEntryRepository, AddAsync before SaveChangesAsync, fact (i) flip + FakeJournalEntryRepository
- [x] [G4] Verify core→edge — gates + no-touch audit + no-migration statement

## Evidence
- Build → 0 warnings, 0 errors
- Arch tests → 22/22
- BankTests → 57/57 (54 + 3 new domain Facts; fact (i) flipped)
- No migration — journal_entries table exists since InitialCreate; zero NEW migration scaffolded (35 files = 17×2 + snapshot)

## Deliverables
- `OpeningBalancePeriod.cs`: `return journalEntry;` at end-of-method (after IsPosted/Status/event) — design-doc literal ":88 after Post()" made flags unreachable (CS0162); corrected, documented
- `PostOpeningBalancesHandler.cs`: 3rd ctor param, capture JE, `AddAsync(journalEntry)` BEFORE `SaveChangesAsync`, return unchanged
- `tests/SmeAccounting.BankTests/`: fact (i) flipped to assert persistence + 3 new domain Facts + FakeJournalEntryRepository (GetAllAsync — CS0535 trap)
- Design: `docs/OpeningBalance-Persist-Design-2026.md`

## Design locks
- JE persist-first: EF assigns Id during Save; JE Id > 0 before any PostingReference link (V2 guard)
- No event change (OpeningBalancesPosted keeps PeriodId+CompanyId)
- PR creation stays separate (CreatePostingReferenceHandler — same-UoW atomic write per PostingReference-Design §7, future task)

## Known limitations
- Handler still not exposed via controller/command dispatch (grep Api = 0 hits) — persistence now correct when dispatched
- PR-link from OpeningBalance to JournalEntry remains a future task (PostingReference-Design §7)
- No-migration grep-evidence trap: `grep -i openingbalance` over Migrations = 134 pre-existing property-name hits, NOT valid zero-evidence — use count + timestamps instead

## Failure log
- G1: PLAN gate text had invalid grep-evidence literal → corrected before auditor (134 pre-existing hits)
- G2: research predicted no placement issue; design-doc literal ":88" returned-after-Post would CS0162 → end-of-method :95 (documented, auditor CLEAN)
- G3: RED error was CS1729 (stale 2-param ctor + 3 args) not predicted CS7036 — same deterministic compile-error class, documented
- Verifier hit max steps before committing state updates → orchestrator committed G4 state (PLAN/STATUS/MEMORY)
- No build/test failures in GREEN; no regressions