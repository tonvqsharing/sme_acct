# Loop Plan
## Mode
patch
## Goal
Fix JournalEntry.SetSource guards and OpeningBalance transient-Id caller core to edge following discovery-first TDD rules
## Stop Condition
all tasks in loop-stack/setsource-caller-fix/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks
- [x] [G1] Decide fix option + design: choose one of RESEARCH.md R3 Options 1/2/3 with tradeoff justification, spec exact SetSource guard set + DomainException messages (SourceType is required. / SourceId must be greater than zero. / Cannot modify a posted journal entry. per R4), caller change spec for OpeningBalancePeriod.cs:78 (keep "OpeningBalance" literal, guard+caller atomic landing), test list per R5 (a–i incl. transient-Id=0 throws + discard Skip/assert-and-record), output design note to docs/SetSource-CallerFix-Design-2026.md; constraints: setter stays setter (no FK), Domain zero NuGet refs, dead null/null path out of scope
- [x] [G2] Implement core via discovery-first TDD (domain + caller only): write failing BankTests Facts first (copy PostingReferenceAggregateTests.cs + Fakes.cs List-backed FakeUnitOfWork pattern), then add SetSource guards in src/SmeAccounting.Domain/Entities/JournalEntry.cs:32-36 + caller fix in src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:59-91 per docs/SetSource-CallerFix-Design-2026.md, keep magic string verbatim, DomainException only, no handler/handler-DI/EF-config changes unless G1 option explicitly requires
- [x] [G3] Verify core→edge: dotnet build SmeAccounting.sln (0 warn, TreatWarningsAsErrors), dotnet test tests/SmeAccounting.ArchitectureTests/ (22/22, controllers never reference Domain.Entities), dotnet test tests/SmeAccounting.BankTests/ (regression + new SetSource/caller Facts green), state why no migration needed (domain in-memory guards + caller reorder only, no new table/column/index/FK)
