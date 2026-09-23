# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
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
