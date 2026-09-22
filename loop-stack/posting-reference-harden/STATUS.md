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
G2 TDD plan: 6 RED-first Facts in PostingReferenceAggregateTests (happy-path + 4 DomainExceptions verbatim + minimal event), no fakes needed, legacy ArgumentNullException dropped — RESEARCH.md appended, no code written
## Active Heartbeats
researcher: mapping PostingReference/JournalEntry current state + writing RESEARCH.md
researcher: done — RESEARCH.md Context & Prior Work written, STATUS updated
researcher: External Knowledge & Resources written — RESEARCH.md §External confirmed no regulatory mandate, STATUS updated
researcher: G1 FK-vs-polymorphic decision research in progress (weighing A/B/C)
researcher: done — G1 decision (Option A) appended to RESEARCH.md, STATUS updated
## Last Executor Result
executor [G2]: RED-first PostingReferenceAggregateTests (6 Facts) failed vs stub then GREEN hardened Domain (PostingReference 4-param ctor + CompanyId + 4 DomainExceptions + event, PostingReferenceCreated minimal, IPostingReferenceRepository 3-method) — build 0/0, BankTests 33/33, arch 22/22; JournalEntry/OpeningBalancePeriod untouched per scope.
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
researcher: writing [G2] domain-spec appendix to RESEARCH.md
researcher: done — [G2] domain spec appended to RESEARCH.md, STATUS updated
researcher: writing [G2] domain TDD plan appendix to RESEARCH.md
researcher: done — [G2] TDD plan (6 RED Facts, no fakes, legacy note) appended, STATUS updated
memory-keeper: G1 learnings consolidated to loop + global MEMORY, status advanced to [G2] Domain core heartbeat
executor: [G2] starting RED — writing PostingReferenceAggregateTests (6 Facts)
executor: [G2] RED confirmed (4-arg ctor missing vs stub) — writing GREEN domain files
executor: [G2] done — build 0/0, BankTests 33/33, arch 22/22, MEMORY+STATUS updated, committing
