# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
### G4 Integration gates + no-touch evidence (2026-09-23)
- Final gate numbers: build 0/0, arch 22/22, bank 72/72, Migrations dir 35 files (17 migrations + 17 Designers + snapshot). Latest migration 20260922084832_PostingReferenceHarden (09-22) predates loop commits (09-23).
- No-touch audit canon (MEMORY:256 extended): `git diff-tree --no-commit-id --name-only -r <commit>` per commit + grep for Migrations/Domain/Infrastructure — cleaner than `git show --stat` for machine-checking; `git log -- <file>` proves entity/port untouched (JournalEntry last touched 5b3db2c, IPostingService only 9f491fc — both pre-loop).
- Verifier state commits (43ed37d/03c0a4e/3682b42) are loop commits too — include them in the Migrations-touch sweep (they're state-files-only, but prove it, don't assume).
- End-to-end code-level trace: controller → MediatR.Send → internal handler (assembly-scanned) → port → single SaveChangesAsync → result record. All signatures verified by reading the 8 wiring files; build 0/0 is the compiler's confirmation.
- G4 = evidence-only task: no commit (evidence lives in STATUS.md, committed by next step).
### G3 PostJournalEntryHandler (2026-09-23)
- CS8629 trap on nullable `.Value`: `entry.PostedAt.Value` (DateTimeOffset?) fails under TreatWarningsAsErrors — compiler can't prove non-null after `entry.Post(...)` (void method, no [MemberNotNull]). Fixes: handler `entry.PostedAt!.Value` (null-forgiving); test `Assert.Equal(clock.Now, entry.PostedAt)` (implicit DateTimeOffset→DateTimeOffset? conversion, no warning). RESEARCH G3-3 claim "compiler allows .Value" was WRONG — compiler is arbiter.
- RED was CS0246 at :39/:59/:74 — 3 ctor call sites (RESEARCH predicted 4; validator fact constructs no handler). Same deterministic compile-error RED mechanism.
- First handler to inject IClock (grep Application for IClock = 0 hits before G3). FakeClock = settable Now property, 5 lines.
- Handler: GetByIdAsync null-guard (InvalidOperationException, ResetNumberingSeriesHandler style) → entry.Post("system", clock.Now) → single SaveChangesAsync → PostJournalEntryResult(entry.Id, entry.PostedAt!.Value). No IPostingService (dead port).
- G3 gates: build 0/0, arch 22/22, bank 72/72 (68 + 4 new facts: 1 validator + 1 happy path + 1 already-posted + 1 not-found). Commit e9ec524 (3 files: Fakes.cs +5, PostJournalEntryHandlerTests.cs 79, PostJournalEntryHandler.cs 26).
- Already-posted fact asserts exact message "Journal entry is already posted." via Assert.ThrowsAsync<DomainException> — DomainException base also catches InvalidPostingRuleException subclass, but happy path is balanced so only already-posted throws.
- Null-forgiving `!.Value` justification (auditor-accepted, STATUS audit check 4b): JournalEntry.Post() throws (already-posted, unbalanced ValidateBalance) BEFORE assigning PostedAt; on normal return PostedAt unconditionally set — throw precedes return, so `.Value` post-normal-return is safe. Same reasoning pattern reusable for any nullable property set inside a throwing domain method.
### G2 CreateJournalEntryHandler (2026-09-23)
- `$"{x:D{width}}"` nested interpolation in format specifier is INVALID C# (CS1056 "Unexpected character '{'") — format string cannot contain `{`. Fix: `x.ToString($"D{width}")` — identical output ("JNRL000001"). Design-doc literal deviation; compiler is arbiter (MEMORY:253 precedent).
- MEMORY:258 lesson reproduced: FakeVoucherTypeRepository without counter-based Id in AddAsync → `Stored[0].Id` = 0 → `new DocumentNumberingSeries(1, vtRepo.Stored[0].Id, ...)` throws DomainException "VoucherTypeId must be greater than zero" at runtime (test line 59). Runtime RED proven first, then counter enabler → green. Any fake feeding a domain ctor that guards Id>0 needs identity simulation.
- G2 gates: build 0/0, arch 22/22, bank 68/68 (61 + 7 new facts: 4 validator + 1 happy path + 2 null-guards). Commit ff88722 (3 files: Fakes.cs, CreateJournalEntryHandlerTests.cs, CreateJournalEntryHandler.cs).
- RED was CS0246 at :62/:80/:94 exactly as predicted (handler missing) — 3 constructor call sites in tests.
- Handler: GetByCodeAsync("JNRL", companyId) → null-guard; GetDefaultAsync(voucherType.Id, companyId) → null-guard; format → Increment() → new JournalEntry → AddLine per input (Money VND) → AddAsync → SINGLE SaveChangesAsync → CreateJournalEntryResult(entry.Id, entry.EntryNumber).
- VoucherType code is company-scoped: composite unique index (CompanyId, Code) — same code valid across different companies; `GetByCodeAsync(code, companyId)` is the correct lookup, never code-only. Handler resolves voucher type by code "JNRL" + request.CompanyId.
- Numbering single-save atomicity: series.Increment() mutates the tracked series (port has NO UpdateAsync — change tracking persists); single SaveChangesAsync persists entry + series increment atomically. entry_number has NO unique index — series-row xmin is the only concurrency serialization point (concurrent creates → DbUpdateConcurrencyException on series row).
- CS0535 trap: fakes must implement ALL port members — FakeVoucherTypeRepository needs GetAllAsync, FakeDocumentNumberingSeriesRepository needs GetAllByCompanyAsync (FakeBankRepository shape lacks both); check the port interface, not just the copy source (MEMORY:254 precedent).
### G1 CompanyId plumbing (2026-09-23)
- CreateJournalEntryCommand now `(long CompanyId, DateTimeOffset Date, long PeriodId, string? Description, string? SourceType, long? SourceId, IReadOnlyList<JournalEntryLineInput> Lines)` — CompanyId FIRST matches 30/32 Create commands.
- Validator rule verbatim from CreatePaymentMethodCommandValidator: `RuleFor(x => x.CompanyId).GreaterThan(0).WithMessage("Company ID is required.")` — English messages in validators, Vietnamese Display in ViewModels.
- `[Required]` on non-nullable `long` is a no-op — real guard is validator GreaterThan(0) (matches PeriodId pattern).
- JournalEntry/Create.cshtml is the FIRST view in the Api project rendering a CompanyId input (ChartOfAccounts omits it — broken pattern, don't copy).
- Call sites were exactly 2 (validator + controller) — no tests/handler touched; G2 handler will be 3rd call site.
- Gates after G1: build 0/0, arch 22/22, bank exactly 61 (no behavior change).
- verifier.md stop-condition path change is committed separately as chore (precedent 6b5c3df) — never fold into task commit.
- Change surface for command-shape change = 5 files: command record, validator, ViewModel, view, controller — no Domain/Infrastructure/migration touched; JournalEntry entity has NO CompanyId column (command-level only, per RESEARCH §5/R9.2).
### Loop complete — daily screen end-to-end (2026-09-23)
- ALL_DONE 4/4. Phiếu kế toán daily screen fully wired: Index read side (af94908, pre-loop) + Create POST → CreateJournalEntryHandler (G2) + Post → PostJournalEntryHandler (G3). Write side is Application/Api-only — JournalEntry entity has NO CompanyId column, so future company-scoped JE features stay command-level (no migration).
- Final gates: build 0/0, arch 22/22, bank 72/72, Migrations 35 files (17+17+snapshot), latest 20260922084832_PostingReferenceHarden (09-22) predates all 6 loop commits (09-23).
- G4 = evidence-only task, no commit: evidence lives in STATUS.md, committed by next step. Verifier re-ran every gate independently — STATUS.md numbers are hypotheses, not facts.
