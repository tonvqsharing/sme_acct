# Loop Status
## State
IN_PROGRESS
## Current Task
G1 — Write design note docs/OpeningBalance-Persist-Design-2026.md
## Task Progress
0 / 4 complete
## Attempts On Current Task
0
## Completed Tasks
(none)
## Skipped Tasks
(none)
## Last Researcher Result
G1 design decisions D1-D6 locked in RESEARCH.md (all verified against source): D1 return after Post() :88, guards ordering already correct (fail-fast :76-77 precedes SetSource, zero guard change); D2 3rd ctor param appended, AddAsync before SaveChangesAsync, handler does NOT need period.Id (SetSource stays in domain :81); D3 fact (i) flip void→async Task + fact (h) :133 gains fake JE repo arg + FakeJournalEntryRepository = FakePostingReferenceRepository shape minus GetBySourceAsync, NO SaveCalledCount on fake repo; D4 no-touch list confirmed; D5 gates build 0/0 + arch 22/22 + BankTests >=56 — CRITICAL: PLAN's "grep -i openingbalance over Migrations = 0 hits" is WRONG (134 hits, all pre-existing OpeningBalancePeriod/Entry/Mapping property names in Designer/snapshot from prior loop 20260921052333_CompanyOpeningUserMgmt) — design note must state corrected evidence pattern; D6 BaseEntity.Id public setter + InternalsVisibleTo + ctor sites (handler :19, tests :105/:119, handler-ctor :133 + reflection :150-153) all confirmed. Design doc path docs/OpeningBalance-Persist-Design-2026.md does not exist yet — G1 creates it.
## Last Executor Result
G1 complete: wrote docs/OpeningBalance-Persist-Design-2026.md (exact PLAN path). Content locked per D1-D6: (1) decision JE persist-first — AddAsync then existing SaveChangesAsync in PostOpeningBalancesHandler, EF assigns Id during Save, JE Id > 0 before any PR link (V2 guard); (2) domain surface — PostOpeningBalances void→JournalEntry, `return journalEntry;` after Post() :88, JE construction stays in domain, no event change; (3) handler surface — 3rd ctor param IJournalEntryRepository appended end, capture return → AddAsync → existing SaveChangesAsync, return unchanged; (4) test surface — fact (i) flip to assert persistence (Stored 1 JE SourceType=="OpeningBalance" + SourceId==period.Id + IsPosted, SaveCalledCount==1), fact (h) ctor gains fake JE repo arg, FakeJournalEntryRepository in Fakes.cs (FakePostingReferenceRepository shape minus GetBySourceAsync, save-count on FakeUnitOfWork); (5) no-touch list — PR creation separate future task (PostingReference-Design §7 same-UoW atomic), no new command/handler/controller, no EF/DbContext/DI change (DependencyInjection.cs:29), no migration (journal_entries since InitialCreate); (6) gates — build 0/0, arch 22/22, BankTests ≥56, corrected no-migration evidence (Migrations count 17 = 35 files, latest 20260922084832_PostingReferenceHarden predates loop commits, zero NEW migration; grep = 134 pre-existing property-name hits NOT valid zero-evidence). Cites PostingReference-Design-2026.md §7/§9 + SetSource-CallerFix-Design-2026.md §2/§5. No placeholders. Verified against source before writing (OpeningBalancePeriod.cs, PostOpeningBalancesHandler.cs, JournalEntrySourceTests.cs, Fakes.cs, both design docs, Migrations dir).
## Last Audit Result
(none)
## Active Heartbeats
executor: G1 design note written to docs/OpeningBalance-Persist-Design-2026.md, MEMORY.md + STATUS.md updated, committing
resource-scout: TOOLS.md reused from global cache (1 day old, verified dotnet 10.0.401, no .codegraph), done
researcher: wrote R1-R6 bounded fix spec to RESEARCH.md, done
researcher: verified Environment & Integration E1-E6 (gates/DB/migrations/DI/callers), appended to RESEARCH.md, done
researcher: locked G1 design decisions D1-D6 (domain/handler/test surface, no-touch list, gates incl. corrected no-migration evidence, test gotchas), appended to RESEARCH.md, done
## Blocked Reason
(none)
