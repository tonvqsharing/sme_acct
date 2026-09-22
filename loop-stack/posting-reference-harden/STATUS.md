# Loop Status
## State
VERIFIED_PASS
## Current Task
[G4] Verify core-to-edge
## Task Progress
4 / 5 complete
## Attempts On Current Task
0
## Completed Tasks
- [x] [G1] Decide FK vs polymorphic + finalize design (VERIFIED_PASS 2026-09-22)
- [x] [G2] Harden Domain core via discovery-first TDD (VERIFIED_PASS 2026-09-22)
## Skipped Tasks
(none)
## Last Researcher Result
G3 CQRS spec: flat layout locked (PaymentMethod 10-file precedent over BankAccounts feature folder), validator NotEmpty+Max100 no-IsInEnum, duplicate→InvalidOperationException per Design §7 (return-existing rejected), PaymentTermController copy minus Enum.Parse, ValidationBehavior auto-run zero-diff — RESEARCH.md appended, no code written
## Active Heartbeats
researcher: mapping PostingReference/JournalEntry current state + writing RESEARCH.md
researcher: done — RESEARCH.md Context & Prior Work written, STATUS updated
researcher: External Knowledge & Resources written — RESEARCH.md §External confirmed no regulatory mandate, STATUS updated
researcher: G1 FK-vs-polymorphic decision research in progress (weighing A/B/C)
researcher: done — G1 decision (Option A) appended to RESEARCH.md, STATUS updated
## Last Executor Result
executor [G3-CQRS]: TDD CQRS+Api — RED 10-Fact PostingReferenceCqrsTests (compile-fail vs missing types), GREEN flat-layout command+result/validator/handler(duplicate-throw)/2 queries+handlers/DTO + PaymentTerm-shape controller minus Enum.Parse/Deactivate + ViewModel — build 0/0, BankTests 45/45, arch 22/22; fake reused verbatim, no infra/domain changes.
## Last Audit Result
WARN — [G3-CQRS] matches RESEARCH [G3] CQRS spec §1–§7: 8 flat-layout files (command+result, validator, create-handler triple pre-check → InvalidOperationException, 2 queries + 2 handlers, DTO), validator GreaterThan ×3 + NotEmpty/Max100 + no IsInEnum, duplicate path throws (not return-existing), zero Domain.* usings in controller/DTO, no Enum.Parse/Deactivate, Fakes.cs untouched, no infra/domain/DI/migration diff, no TODOs. One non-blocking note: controller Create POST discards Send result and redirects Details with model.JournalEntryId instead of created reference Id (precedent PaymentTermController redirects Index with companyId) — cosmetic routing slip, compiles + routes, fix in follow-up.
## Active Heartbeats
researcher: mapping PostingReference/JournalEntry current state + writing RESEARCH.md
researcher: done — RESEARCH.md Context & Prior Work written, STATUS updated
## Last Verifier Result
VERIFIED_PASS — [G3-CQRS] Application + Api edge: 8 flat-layout files, validator GreaterThan×3 + NotEmpty/Max100 (no IsInEnum), duplicate triple → InvalidOperationException, DTO all-scalar, controller zero Domain.* usings; auditor WARN redirect slip FIXED (Send result Id used); build 0/0, BankTests 45/45, arch 22/22. Prior [G3-EF] also VERIFIED_PASS.
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
auditor: starting audit of [G2] harden Domain core via discovery-first TDD
auditor: done — CLEAN (all spec items pass, commit scoped, no leaks), no code written
memory-keeper: G2 learnings consolidated to loop + global MEMORY, status advanced to [G3] edge (EF wiring + CQRS in parallel) heartbeat
researcher: done — [G3] EF wiring spec appended to RESEARCH.md, STATUS updated
researcher: writing [G3] CQRS spec (flat layout, validator, idempotency decision) to RESEARCH.md
researcher: done — [G3] CQRS spec appended to RESEARCH.md, STATUS updated
executor: [G3-EF] starting RED — FakePostingReferenceRepository + contract facts
executor: [G3-EF] GREEN done — build 0/0, BankTests 35/35, arch 22/22, updating MEMORY+STATUS
auditor: starting audit of [G3] Harden EF persistence + repository wiring via TDD
auditor: done — CLEAN (config triple-unique + dual Restrict + xmin-last, repo tracked, Ignore+DI 1-line each, fake triple-match, no leaks), no code written
executor: [G3-CQRS] starting RED — PostingReferenceCqrsTests (validator/handler/query Facts)
executor: [G3-CQRS] GREEN done — build 0/0, BankTests 45/45, arch 22/22, committing
auditor: starting audit of [G3] Harden Application CQRS + Api edge via TDD
auditor: done — WARN (spec §1–§7 pass, one non-blocking redirect-target note), no code written
memory-keeper: G3 learnings consolidated to loop + global MEMORY (redirect-slip Send-result-Id rule), status [G4] Verify core-to-edge heartbeat
