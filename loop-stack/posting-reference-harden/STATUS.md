# Loop Status
## State
VERIFIED_PASS
## Current Task
[G2] Harden Domain core via discovery-first TDD
## Task Progress
1 / 5 complete
## Attempts On Current Task
0
## Completed Tasks
- [x] [G1] Decide FK vs polymorphic + finalize design (VERIFIED_PASS 2026-09-22)
## Skipped Tasks
(none)
## Last Researcher Result
G1 verification criteria: SourceType stays max100 (NOT Code-20) per InitialCreate varchar(100); unique(CompanyId,SourceType,SourceId) + dual Restrict FKs + xmin-last; 4 DomainExceptions; minimal event; 8-item out-of-scope list — RESEARCH.md appended, no code written
## Active Heartbeats
researcher: mapping PostingReference/JournalEntry current state + writing RESEARCH.md
researcher: done — RESEARCH.md Context & Prior Work written, STATUS updated
researcher: External Knowledge & Resources written — RESEARCH.md §External confirmed no regulatory mandate, STATUS updated
researcher: G1 FK-vs-polymorphic decision research in progress (weighing A/B/C)
researcher: done — G1 decision (Option A) appended to RESEARCH.md, STATUS updated
## Last Executor Result
executor [G1]: created docs/PostingReference-Design-2026.md locking Option A (dual Restrict FKs + direct CompanyId + unique(CompanyId,SourceType,SourceId), canonical table, cache JE columns, 4 DomainExceptions, minimal event, 8 out-of-scope + non-goals, widths from InitialCreate source_type 100) — design only, no code changes; MEMORY.md appended.
## Last Audit Result
WARN — [G1] docs/PostingReference-Design-2026.md passes RESEARCH.md §0–§9 all items (Option A locked with reasons, source_type max100, unique(CompanyId,SourceType,SourceId), Restrict ×2, xmin last, 4 DomainExceptions no ArgumentNullException, minimal event, idempotency semantics, 8 out-of-scope with reasons, no placeholders, no invented VAS). One non-blocking note: file lives at docs/PostingReference-Design-2026.md, not PLAN-specified loop-stack/posting-reference-harden/DESIGN.md — content complete so downstream G2–G4 can consume as-is; suggest copy/symlink to DESIGN.md path or accept docs/ as canonical.
## Active Heartbeats
researcher: mapping PostingReference/JournalEntry current state + writing RESEARCH.md
researcher: done — RESEARCH.md Context & Prior Work written, STATUS updated
## Last Verifier Result
VERIFIED_PASS — [G1] docs/PostingReference-Design-2026.md satisfies RESEARCH.md §0–§9: Option A locked, source_type max100 (not 20), unique(CompanyId,SourceType,SourceId) + Restrict ×2 + xmin-last, 4 DomainExceptions (no ArgumentNullException), minimal event (Id+CompanyId+occurredOn), 8-item out-of-scope with reasons, no placeholders; stop-condition ref loop-stack/01-system-security_DONE/PLAN.md all 7 tasks [x] checked.
## Blocked Reason
(none)
researcher: writing [G1] verification criteria appendix to RESEARCH.md

researcher: done — [G1] verification criteria appended to RESEARCH.md, STATUS updated
executor: [G1] writing docs/PostingReference-Design-2026.md (Option A locked)
executor: [G1] done — design doc + MEMORY + STATUS updated, committing
auditor: starting audit of [G1] decide FK vs polymorphic + finalize design
auditor: done — WARN (all §0–§9 pass, one non-blocking path note), no code written
memory-keeper: G1 learnings consolidated to loop + global MEMORY, status advanced to [G2] Domain core heartbeat
