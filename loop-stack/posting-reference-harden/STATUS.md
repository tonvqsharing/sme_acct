# Loop Status
## State
IN_PROGRESS
## Current Task
[G1] Decide FK vs polymorphic + finalize design
## Task Progress
0 / 5 complete
## Attempts On Current Task
0
## Completed Tasks
(none)
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
(none)
## Active Heartbeats
researcher: mapping PostingReference/JournalEntry current state + writing RESEARCH.md
researcher: done — RESEARCH.md Context & Prior Work written, STATUS updated
## Blocked Reason
(none)
researcher: writing [G1] verification criteria appendix to RESEARCH.md

researcher: done — [G1] verification criteria appended to RESEARCH.md, STATUS updated
executor: [G1] writing docs/PostingReference-Design-2026.md (Option A locked)
executor: [G1] done — design doc + MEMORY + STATUS updated, committing
