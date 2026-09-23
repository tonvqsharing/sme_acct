# Loop Status
## State
IN_PROGRESS
## Current Task
G2 — Domain TDD — expose JE from OpeningBalancePeriod.PostOpeningBalances (void→JournalEntry, return after Post() :88)
## Task Progress
1 / 4 complete
## Attempts On Current Task
0
## Completed Tasks
- [x] [G1] Write design note docs/OpeningBalance-Persist-Design-2026.md — VERIFIED_PASS (2026-09-23): deliverable at exact PLAN path docs/OpeningBalance-Persist-Design-2026.md; all 6 content areas present (decision JE persist-first, domain void→JournalEntry, handler 3rd ctor param, test surface fact-i flip + FakeJournalEntryRepository, no-touch list, gates); corrected no-migration evidence stated (134 pre-existing grep hits NOT zero-evidence, Migrations count 17, latest 20260922084832_PostingReferenceHarden predates loop commits); citations verified against source (PostingReference-Design §7/§9, SetSource-CallerFix §2/§5, OpeningBalancePeriod.cs:59/76-94, Handler.cs:7-24, DI:29, IJournalEntryRepository.cs:5-9, Fakes.cs:50-67/91-99); no placeholders; auditor CLEAN.
## Skipped Tasks
(none)
## Last Researcher Result
G1 design decisions D1-D6 locked in RESEARCH.md (all verified against source): D1 return after Post() :88, guards ordering already correct (fail-fast :76-77 precedes SetSource, zero guard change); D2 3rd ctor param appended, AddAsync before SaveChangesAsync, handler does NOT need period.Id (SetSource stays in domain :81); D3 fact (i) flip void→async Task + fact (h) :133 gains fake JE repo arg + FakeJournalEntryRepository = FakePostingReferenceRepository shape minus GetBySourceAsync, NO SaveCalledCount on fake repo; D4 no-touch list confirmed; D5 gates build 0/0 + arch 22/22 + BankTests >=56 — CRITICAL: PLAN's "grep -i openingbalance over Migrations = 0 hits" is WRONG (134 hits, all pre-existing OpeningBalancePeriod/Entry/Mapping property names in Designer/snapshot from prior loop 20260921052333_CompanyOpeningUserMgmt) — design note must state corrected evidence pattern; D6 BaseEntity.Id public setter + InternalsVisibleTo + ctor sites (handler :19, tests :105/:119, handler-ctor :133 + reflection :150-153) all confirmed. Design doc path docs/OpeningBalance-Persist-Design-2026.md does not exist yet — G1 creates it.
## Last Executor Result
G1 complete: wrote docs/OpeningBalance-Persist-Design-2026.md (exact PLAN path). Content locked per D1-D6: (1) decision JE persist-first — AddAsync then existing SaveChangesAsync in PostOpeningBalancesHandler, EF assigns Id during Save, JE Id > 0 before any PR link (V2 guard); (2) domain surface — PostOpeningBalances void→JournalEntry, `return journalEntry;` after Post() :88, JE construction stays in domain, no event change; (3) handler surface — 3rd ctor param IJournalEntryRepository appended end, capture return → AddAsync → existing SaveChangesAsync, return unchanged; (4) test surface — fact (i) flip to assert persistence (Stored 1 JE SourceType=="OpeningBalance" + SourceId==period.Id + IsPosted, SaveCalledCount==1), fact (h) ctor gains fake JE repo arg, FakeJournalEntryRepository in Fakes.cs (FakePostingReferenceRepository shape minus GetBySourceAsync, save-count on FakeUnitOfWork); (5) no-touch list — PR creation separate future task (PostingReference-Design §7 same-UoW atomic), no new command/handler/controller, no EF/DbContext/DI change (DependencyInjection.cs:29), no migration (journal_entries since InitialCreate); (6) gates — build 0/0, arch 22/22, BankTests ≥56, corrected no-migration evidence (Migrations count 17 = 35 files, latest 20260922084832_PostingReferenceHarden predates loop commits, zero NEW migration; grep = 134 pre-existing property-name hits NOT valid zero-evidence). Cites PostingReference-Design-2026.md §7/§9 + SetSource-CallerFix-Design-2026.md §2/§5. No placeholders. Verified against source before writing (OpeningBalancePeriod.cs, PostOpeningBalancesHandler.cs, JournalEntrySourceTests.cs, Fakes.cs, both design docs, Migrations dir).
## Last Audit Result
CLEAN — design note matches PLAN path + all D1-D6 criteria, citations verified against source.
- Path exact: docs/OpeningBalance-Persist-Design-2026.md; decision persist-first Add-before-Save, domain void→JournalEntry (return after Post() :88, no event change), handler 3rd ctor param appended, test surface (fact i flip :146-156, fact h :133 arg, FakeJournalEntryRepository = FakePostingReferenceRepository shape :50-67 minus GetBySourceAsync, save-count on FakeUnitOfWork :91-99) all present.
- No-touch list complete (PR creation separate per PostingReference-Design §7/§9 item 3; no command/EF/DI/controller/migration); gates correct incl. corrected no-migration evidence (134 pre-existing grep hits NOT zero-evidence, Migrations count 17, latest 20260922084832 predates loop commits).
- Citations real: PostingReference-Design §7:96-97 + §9 item 3:116, SetSource-CallerFix §2:21-23 + §5:102, OpeningBalancePeriod.cs:59-94, Handler.cs:7-24, JournalEntry.cs:70, BaseEntity.cs:7, IJournalEntryRepository.cs:5-9, DependencyInjection.cs:29 — all verified. No placeholders.
## Active Heartbeats
memory-keeper: G1 learnings consolidated (loop MEMORY.md +1 line, global MEMORY.md +1 line — grep-evidence trap), STATUS advanced to G2, done
auditor: starting audit of [G1] design note — CLEAN, all D1-D6 verified
executor: G1 design note written to docs/OpeningBalance-Persist-Design-2026.md, MEMORY.md + STATUS.md updated, committing
resource-scout: TOOLS.md reused from global cache (1 day old, verified dotnet 10.0.401, no .codegraph), done
researcher: wrote R1-R6 bounded fix spec to RESEARCH.md, done
researcher: verified Environment & Integration E1-E6 (gates/DB/migrations/DI/callers), appended to RESEARCH.md, done
researcher: locked G1 design decisions D1-D6 (domain/handler/test surface, no-touch list, gates incl. corrected no-migration evidence, test gotchas), appended to RESEARCH.md, done
## Blocked Reason
(none)
