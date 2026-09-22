# Loop Report — setsource-caller-fix

## Goal
Fix JournalEntry.SetSource guards and OpeningBalance transient-Id caller core to edge following discovery-first TDD rules.

## Mode
patch | Git auto-commit: yes

## Result
ALL DONE — 3/3 tasks verified.

## Tasks
- [x] [G1] Decide fix option + design → docs/SetSource-CallerFix-Design-2026.md (Option 2 domain-only)
- [x] [G2] Implement core TDD (SetSource guards + caller fail-fast, 9 Facts)
- [x] [G3] Verify core→edge (gates + no-migration rationale)

## Evidence
- Build → 0 warnings, 0 errors
- Arch tests → 22/22
- BankTests → 54/54 (45 + 9 new)
- No migration — runtime guards only, zero schema surface (17 migrations, none this loop)

## Deliverables
- `JournalEntry.SetSource`: 3 guards (IsPosted → "Cannot modify a posted journal entry.", SourceType is required., SourceId must be greater than zero.)
- `OpeningBalancePeriod.PostOpeningBalances`: Id<=0 fail-fast before JE build
- `tests/SmeAccounting.BankTests/JournalEntrySourceTests.cs` (9 Facts) + FakeOpeningBalancePeriodRepository
- Design: `docs/SetSource-CallerFix-Design-2026.md`

## Design locks
- Option 2 domain-only: full guard set + caller fail-fast; live persisted-Id flow unchanged
- Setter stays setter (no FK); dead null/null path out of scope (covered by new guards)

## Known limitations
- Discarded-JE persist bug remains (OpeningBalance handler never persists JE) — fact (i) test will fail intentionally when that fix lands; must update in same change.
- PostingReferenceHarden migration backfill risk for production DBs with existing rows (from prior loop, unchanged).

## Failure log
- First auditor returned empty → re-spawned, CLEAN.
- Auditor WARN path minors (PLAN → docs/) fixed pre-verify.
- No build/test failures; no regressions.
