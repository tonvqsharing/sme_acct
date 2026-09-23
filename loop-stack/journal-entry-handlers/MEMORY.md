# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
### G1 CompanyId plumbing (2026-09-23)
- CreateJournalEntryCommand now `(long CompanyId, DateTimeOffset Date, long PeriodId, string? Description, string? SourceType, long? SourceId, IReadOnlyList<JournalEntryLineInput> Lines)` — CompanyId FIRST matches 30/32 Create commands.
- Validator rule verbatim from CreatePaymentMethodCommandValidator: `RuleFor(x => x.CompanyId).GreaterThan(0).WithMessage("Company ID is required.")` — English messages in validators, Vietnamese Display in ViewModels.
- `[Required]` on non-nullable `long` is a no-op — real guard is validator GreaterThan(0) (matches PeriodId pattern).
- JournalEntry/Create.cshtml is the FIRST view in the Api project rendering a CompanyId input (ChartOfAccounts omits it — broken pattern, don't copy).
- Call sites were exactly 2 (validator + controller) — no tests/handler touched; G2 handler will be 3rd call site.
- Gates after G1: build 0/0, arch 22/22, bank exactly 61 (no behavior change).
- verifier.md stop-condition path change is committed separately as chore (precedent 6b5c3df) — never fold into task commit.
- Change surface for command-shape change = 5 files: command record, validator, ViewModel, view, controller — no Domain/Infrastructure/migration touched; JournalEntry entity has NO CompanyId column (command-level only, per RESEARCH §5/R9.2).
