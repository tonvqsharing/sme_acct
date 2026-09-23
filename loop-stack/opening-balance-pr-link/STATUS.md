# Loop Status
## State
IN_PROGRESS
## Current Task
G1 — Write design note docs/OpeningBalance-PRLink-Design-2026.md (lock R1 Option B decision + two-save + fake-Id enabler + SaveCalledCount==2 + no-touch + gates)
## Task Progress
0 / 3 complete
## Attempts On Current Task
0
## Completed Tasks
(none)
## Skipped Tasks
(none)
## Last Researcher Result
G1 design decisions D1-D6 locked + appended to RESEARCH.md "## Task-Specific Research — [G1] design", all line refs re-verified against source. D1: Option B (no pre-check) — IsPosted guard :61-62 blocks sequential dupes pre-persistence; xmin on period row catches concurrent race at save 1 (DbUpdateConcurrencyException, JE never persists); unique index (CompanyId,SourceType,SourceId) last resort (migration :24-28); CreatePostingReferenceHandler pre-check :17-19 exists only because that handler lacks domain guard — replicating adds round-trip, is TOCTOU-ineffective, risks dangling JE post-save-1. D2: 4th ctor param IPostingReferenceRepository appended end; save 1 (:24) → build PR (period.CompanyId :9, journalEntry.Id post-save, "OpeningBalance", period.Id) → AddAsync → second SaveChangesAsync; return unchanged. D3: FakeJournalEntryRepository.AddAsync (Fakes.cs:79-83) MUST assign Id (counter-based) or PR V2 guard throws; safe — only JE Id==0 assert is G2-3 :166 pre-handler. D4: fact (i) :214 SaveCalledCount 1→2 + PR-row Single assert; fact (h) :184 ALSO 1→2 (both facts run full handler); ctor calls :176/:202 → CS1729 RED. D5: touched = handler + JournalEntrySourceTests + Fakes only; no-touch = CreatePostingReferenceHandler/Command/Controller/EF/DbContext/DI(:69 already)/migrations. D6: build 0/0, arch 22/22, BankTests ≥58; no-migration evidence = count 35 + latest 20260922084832 predates loop + zero NEW (grep INVALID — 134-style pre-existing hits).
## Last Executor Result
G1 design note written: docs/OpeningBalance-PRLink-Design-2026.md (89 lines, no placeholders). All 6 locked items: (1) Option B no GetBySourceAsync pre-check with exact rationale (IsPosted :61-62 sequential pre-persistence; xmin on period row catches race at save 1 → DbUpdateConcurrencyException → JE never persists; unique index (CompanyId,SourceType,SourceId) last resort; CreatePostingReferenceHandler pre-check :17-19 exists only because that handler lacks domain guard — TOCTOU-ineffective, adds round-trip, dangling-JE risk post-save-1); (2) handler surface — 4th ctor param IPostingReferenceRepository appended end, save 1 (:24) → new PostingReference(period.CompanyId :9, journalEntry.Id post-save, "OpeningBalance", period.Id) → AddAsync → second SaveChangesAsync, return PostOpeningBalancesResult(bool) unchanged; (3) enabler — FakeJournalEntryRepository.AddAsync counter-based Id (safe: only JE Id==0 assert is G2-3 :166 pre-handler); (4) test surface — BOTH facts (h) :184 and (i) :214 SaveCalledCount 1→2, fact (i) adds PR-row Single assert, fact (h) ctor gains 4th arg, CS1729 RED at :176/:202; (5) no-touch list — CreatePostingReferenceHandler/command/validator/controller/EF/DbContext/DI(:69 already)/migration/unique index; (6) gates — build 0/0, arch 22/22, BankTests ≥58, corrected no-migration evidence (Migrations count 35 + latest 20260922084832 predates loop commits + zero NEW; grep INVALID). Cites PostingReference-Design-2026.md §7 + OpeningBalance-Persist-Design-2026.md §1/§5. All line refs re-verified against source. Zero code changes (design-only).
## Last Audit Result
(none)
## Active Heartbeats
resource-scout: TOOLS.md reused from global cache (2026-09-21, verified 2026-09-23) — dotnet 10.0.401, git 2.51.0, no .codegraph, skills present — done
researcher: D1-D6 design decisions locked + appended to RESEARCH.md, all line refs re-verified — done
executor: G1 writing design note docs/OpeningBalance-PRLink-Design-2026.md — all source line refs re-verified (handler :7-26, IsPosted :61-62, PR ctor :15-24, pre-check :17-19, Fakes :50-118, tests :171-215, DI :69, migration :24-28, Migrations 35, HEAD ae62ae4)
executor: G1 design note written + MEMORY/STATUS updated — done
## Blocked Reason
(none)
