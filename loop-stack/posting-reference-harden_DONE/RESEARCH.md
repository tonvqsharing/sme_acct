# Research Log
## Context & Prior Work
Current PostingReference + JournalEntry implementation mapped from source (2026-09-22). All paths absolute under `/home/projects/sme_acct/`.

### 1. Domain entities
- `src/SmeAccounting.Domain/Entities/PostingReference.cs:1-17` — stub entity, extends `BaseEntity`:
  - `PostingReference.cs:5` `long JournalEntryId` (no navigation prop, no CompanyId)
  - `PostingReference.cs:6` `string SourceType` non-nullable, default `string.Empty`
  - `PostingReference.cs:7` `long SourceId` non-nullable
  - `PostingReference.cs:9` private parameterless ctor (EF materialization, matches global pattern)
  - `PostingReference.cs:11-16` public ctor `(journalEntryId, sourceType, sourceId)` — validates only `sourceType ?? throw ArgumentNullException`; no `DomainException`, no JournalEntryId/SourceId range checks, no empty/whitespace check, raises no domain event
- `src/SmeAccounting.Domain/Entities/JournalEntry.cs:1-78` — aggregate root:
  - `JournalEntry.cs:13-14` nullable `string? SourceType` + `long? SourceId` (source tracking duplicated with PostingReference table, no sync)
  - `JournalEntry.cs:32-36` `SetSource(string sourceType, long sourceId)` — unconditional setter, no validation, no DomainException, callable even when posted
  - `JournalEntry.cs:24-30` ctor `(entryNumber, date, periodId, description)` — no source params; source only via SetSource
  - `JournalEntry.cs:38-53` `AddLine(...)` guards posted state via DomainException; creates `JournalEntryLine(Id, ...)` (transient Id=0 pattern)
  - `JournalEntry.cs:55-67` `Post(...)` validates balance, sets state, raises `JournalEntryPosted` — PostingReference never created here
- `src/SmeAccounting.Domain/Entities/BaseEntity.cs:1-23` — `long Id`, AddDomainEvent plumbing; PostingReference raises zero events
- `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:78` — sole `SetSource` caller in Domain: `journalEntry.SetSource("OpeningBalance", Id)` inside `PostOpeningBalances` (`OpeningBalancePeriod.cs:59-91`). No `PostingReference` row created — source linkage lives only on JournalEntry columns. Magic string "OpeningBalance", transient `Id` (0 pre-save) passed as SourceId.

### 2. EF Core mapping
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/PostingReferenceConfiguration.cs:1-36` — `internal sealed`, `ToTable("posting_references")`, `HasKey(Id)`, `id` ValueGeneratedOnAdd, `journal_entry_id` (no Required/FK), `source_type` Required max100, `source_id`, indexes on `JournalEntryId` (line 29) and `(SourceType, SourceId)` (line 30), `xmin` rowversion. Missing vs. established pattern (Company FK Restrict, composite unique per company, enum conversion, max lengths on all strings): no `HasOne<JournalEntry>()` relationship, no `OnDelete`, no CompanyId column, no unique constraint.
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:16` — `DbSet<PostingReference> PostingReferences => Set<PostingReference>()`; `OnModelCreating` (`:59-112`) applies configs via `ApplyConfigurationsFromAssembly` (line 110); no PostingReference domain event to Ignore (none exists) — consistent.
- Migration `src/SmeAccounting.Infrastructure/Migrations/20260916051341_InitialCreate.cs:94-108` — `CreateTable posting_references (id bigint identity, journal_entry_id bigint NOT NULL, source_type varchar(100) NOT NULL, source_id bigint NOT NULL, xmin xid rowversion)`, PK only, no FK to `journal_entries`; indexes `IX_posting_references_journal_entry_id` (:200-203) and `IX_posting_references_source_type_source_id` (:205-208) non-unique. All later migration Designers + `SmeAccountingDbContextModelSnapshot.cs:1722-1757` repeat identical shape — no hardening migration ever scaffolded.

### 3. Repository / CQRS / API — confirmed absent
- Ports: `src/SmeAccounting.Domain/Ports/` lists 50+ `I*Repository` files (IBank*, ITax*, etc.) — no `IPostingReferenceRepository.cs` (glob + grep confirmed).
- Infrastructure: no `EfPostingReferenceRepository`; `DependencyInjection.cs:28-72` registers ~40 repos (incl. Bank hierarchy, CompanySettings) — zero PostingReference lines (grep confirmed).
- Application: `CreateJournalEntryCommand.cs:6-12` carries optional `SourceType`/`SourceId` but grep finds no `SetSource` usage in Application; `CreateJournalEntryCommandValidator.cs:1-22` validates only PeriodId/Lines — no source rules; no `CreateJournalEntry*Handler` exists (glob `**/*Handler*.cs` + grep `IRequestHandler.*JournalEntry` = 0 hits); `PostJournalEntryCommand` has record + validator but likewise no handler. No PostingReference commands/queries/validators/DTOs anywhere (Application grep = no files found).
- Api: no PostingReference controller (glob: 20 controllers, none matching); `JournalEntryController.cs:39-41` constructs `CreateJournalEntryCommand(..., null, null, model.Lines)` — always passes null source, so even the nullable JournalEntry.SourceType/SourceId path is dead in the UI.
- Tests: `tests/SmeAccounting.ArchitectureTests/` (22 rules) unaffected — stub follows naming/location rules.

### 4. Discovery doc (prior analysis, still accurate)
- `docs/Discovery-Bank-PostingReference-Gaps-2026.md:35-93` — line-by-line verified against current source: entity-incomplete (:37-52), config-no-FK (:53-60), migration-no-FK (:62-63), DbContext (:65-66), no repo/application/events (:68-72), JournalEntry coupling/SetSource duplication (:74-82), missing-patterns list (:84-91: no Company isolation, no IsActive, no effective dating, free-string SourceType, no composite unique, no DomainException, no repo/CQRS). Bank half of that doc is now stale (Bank/Branch/Account entities + repos + CQRS + `AddBankHierarchy` migration exist); PostingReference half is fully current — no file changed since discovery.

### 5. Usages inventory (complete)
- `PostingReference` referenced only in: entity file, EF config, DbContext DbSet, migrations/Designer/snapshot (model-only, ~15 Designer files + snapshot). Zero business-logic references.
- `SetSource` referenced only in: `JournalEntry.cs:32` (definition) + `OpeningBalancePeriod.cs:78` (single caller).
- `SourceType`/`SourceId` (non-migration) referenced only in: `JournalEntry.cs:13-14,32-35`, `CreateJournalEntryCommand.cs:10-11`, `OpeningBalancePeriod.cs:78`.

### 6. Cross-loop patterns available for hardening (from loop-stack/.global/MEMORY.md)
- VoucherType/T3-TransactionReason checklist: entity + event + port + EF config + repo + DbSet/Ignore + DI (T1-VoucherType ref).
- Company-scoped pattern: `CompanyId` + `HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict)` + composite unique `(CompanyId, Code)` + `xmin` (G2-cross-cutting, T5-dimensions).
- `DomainException` hierarchy for all invariants (never ArgumentNullException); private parameterless ctor + public validating ctor; minimal events `(EntityId, CompanyId, occurredOn)`.
- Transient Id=0 accepted at construction; identifier formatting in Application, not Domain (Opening-Balances fix note).
- CQRS: `record` command `IRequest<T>`, handler constructs entity + AddAsync + SaveChanges, FluentValidation via `ValidationBehavior` pipeline, DTO records manual mapping, thin MediatR controller; check-only migration scaffold (PaymentMethod G3).
## External Knowledge & Resources
Evidence-only. All paths absolute under `/home/projects/sme_acct/`. Claims without file:line marked UNKNOWN.

### 1. ADR-010 — no PostingReference dependency (confirmed)
- `docs/architecture/ADR-010-tax-foundation-regulatory-traceability.md:1-148` contains zero mentions of PostingReference / SourceType / SourceId (full-file read confirmed).
- Tax snapshot contract (`ADR-010:102-108`) uses its OWN fields: Tax Type, Code, Treatment, Rate, Rule Version, Effective Date, Legal Reference. It does NOT consume PostingReference — future transaction modules snapshot tax data directly, not via the posting-reference table.
- Consequence: hardening PostingReference cannot break ADR-010 compliance; no traceability-matrix update required for this entity.

### 2. VoucherType / SourceType relationship — none exists (confirmed)
- `docs/document-numbering-voucher-transaction-reason-design-summary.md:1-122` — VoucherType links only to DocumentNumberingSeries (`VoucherTypeId` FK, :21,36-38) and TransactionReason (`VoucherTypeId` FK, :71-75,84-86). No link to PostingReference, JournalEntry, SourceType, or posting flow anywhere in doc.
- Only doc bridging the two concepts is `docs/PaymentMethod-Design-2026.md:79,136,158`: states payment linkage to journals "already exists via free-text `JournalEntry.SourceType/SourceId` + `SetSource`" and explicitly decides "no hard FK needed" / "No `JournalEntry.SourceType` change — free-text `SetSource` linkage suffices" for PaymentMethod scope. That is a PaymentMethod-loop design decision, not a PostingReference hardening constraint — planner must decide whether it still holds.
- No `VoucherCategory` / voucher-type enum constrains SourceType values today.

### 3. VAS / Circular 99 imposes NO PostingReference structure — UNKNOWN unless sourced (confirmed unknown)
- Searched `docs/` for `PostingReference|SourceType|voucher.*post|posting.*voucher`: only hits are `Discovery-Bank-PostingReference-Gaps-2026.md` (gap analysis), `Discovery-GeneralAccounting-Entities-2026.md:20,122,232,262` (inventory: "no FK, no CompanyId, no repository, no application layer"), `PaymentMethod-Design-2026.md` (above). Zero regulatory citations prescribing reference shape, numbering, or mandatory fields.
- Global MEMORY: Circular 99 Art. 28 maps to posting rules / audit / reports / extensible architecture — no PostingReference field mandate. Tax accounts (1331/1332/3331/33311/33312/3334/3335) constrain WHICH accounts postings hit, not HOW the source link is stored.
- Closest regulatory-adjacent statement: `PaymentMethod-Design-2026.md:73` — members "NOT sourced from any VAS/Circular 99 list — no repo doc prescribes payment-method values". Same evidentiary status applies to PostingReference: no repo doc prescribes its structure.
- Verdict: any claim "VAS/Circular 99 requires field X on PostingReference" is UNKNOWN unless executor cites article/clause + effective period per ADR-010 §Critical Regulatory Rule (:22-32).

### 4. Journal/posting docs — no additional constraints
- `docs/discovery-phase0.md:1-55` — classifies JournalEntry EXISTS, OpeningBalanceMapping EXISTS but engine MISSING; no PostingReference mention, no structure prescribed.
- `docs/Patterns-CompanyIsolation-EffectiveDating-2026.md:1-227` — prescribes HOW to harden (CompanyId FK Restrict + composite unique, xmin, snake_case, DomainException, SetNull-for-dimensions-only), not WHAT PostingReference must contain. Directly reusable patterns quoted with file:line in RESEARCH Context §6.
- `docs/Discovery-Bank-PostingReference-Gaps-2026.md:84-93` missing-patterns list (no Company isolation, no IsActive, no effective dating, free-string SourceType, no composite unique, no DomainException, no repo/CQRS) is a pattern-conformance checklist, not a regulatory mandate.

### 5. TOOLS.md current versions (from `loop-stack/.global/TOOLS.md`)
- SDK 10.0.401; runtimes 10.0.12; dotnet-ef 10.0.12; psql 18.4; git 2.51.0; Node 26.5.0.
- NuGet: Domain zero refs (must stay); Application MediatR 14.2.0 + FluentValidation 12.1.0; Infrastructure EF Core 10.0.4 + Npgsql 10.0.3 + NamingConventions; Api EF Design 10.0.12 + Swashbuckle 10.2.3; tests NetArchTest.Rules 1.3.2 + xunit 2.9.3.
- Loop `TOOLS.md` status PENDING — no loop-local discoveries yet; nothing new found online needed: hardening reuses in-repo patterns only (no new package/MCP/skill required). No `knowledge-sources.md` fallback consulted — task fully answerable from repo docs + source.
- Not available: nuget CLI, make, gcc, jq, docker. CodeGraph: no `.codegraph/` index — use grep/glob/read.
## Requirements & Constraints
Decision inputs for FK vs polymorphic reference design. Evidence only — NO recommendation. Planner/G1 decides. All paths absolute under `/home/projects/sme_acct/`. Claims without a file:line ref are marked UNKNOWN.

### 1. Distinct SourceType string values in use: exactly 1
- Only live literal: `"OpeningBalance"` — `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:78` (`journalEntry.SetSource("OpeningBalance", Id)`). Sole `SetSource` caller in codebase (matches Context §5).
- `src/SmeAccounting.Application/Commands/CreateJournalEntryCommand.cs:10-11` carries optional `SourceType`/`SourceId`, but `src/SmeAccounting.Api/Controllers/JournalEntryController.cs:39-41` always passes `null, null` — the command path is dead.
- `src/SmeAccounting.Application/Validators/CreateJournalEntryCommandValidator.cs:1-22` has zero source rules.
- Only seed file is `src/SmeAccounting.Infrastructure/Persistence/Seeds/SystemSecuritySeed.cs` (glob confirmed) — no seed writes any SourceType.
- All other `SourceType`/`SourceId` hits are EF migration Designers/snapshot echoing the same two columns — no new values.

### 2. Distinct source entity types needing FKs under option C: 1 today, rest UNKNOWN
- Today: `OpeningBalancePeriod` only. ~50 entity classes exist in `src/SmeAccounting.Domain/Entities/` (grep `public class`), but none besides OpeningBalancePeriod posts to JournalEntry.
- Future source types (invoices, payments, bank postings — no such posting modules exist today): UNKNOWN. No roadmap doc found stating which modules will post journals.
- Implication: option C costs 1 nullable FK column today; future cost scales with UNKNOWN number of source types.

### 3. Reversal / correction modeling: absent
- Grep `Revers|ReversedBy|Reverses|Correction|Corrects|Void` across `src/` = 0 files.
- `JournalEntry.cs:55-67` has only `Post()` + `IsPosted` bool guard; no reverse/void/correct method, no status enum, no `ReversedById`/`ReversesId` columns; `JournalEntryConfiguration.cs:1-57` confirms no such columns.
- Whether PostingReference must also link reversal chains (vs origin trace only): UNKNOWN — planner must scope this.

### 4. CompanyId derivability: by convention only, not guaranteed
- `JournalEntry` has NO `CompanyId` property (`JournalEntry.cs:7-17`) and `JournalEntryConfiguration.cs` contains zero `HasOne` — `PeriodId` is a bare non-unique index (`:50`), no FK to `fiscal_periods`.
- Intended chain: `JournalEntry.PeriodId` → `FiscalPeriod.YearId` → `FiscalYear.CompanyId` (`FiscalYear.cs:9`, enforced FK `FiscalYearConfiguration.cs:38-41`, Restrict).
- But hop 2 is also unenforced: `FiscalPeriodConfiguration.cs:45` has only `HasIndex(e => e.YearId)` — no `HasOne<FiscalYear>`, no FK.
- Domain gives no backup: `JournalEntry` ctor (`:24-30`) does not validate `periodId > 0`; `FiscalPeriod` ctor (`FiscalPeriod.cs:19-31`) does not validate `yearId > 0`.
- `PostingReference` has no `CompanyId` either (`PostingReference.cs:1-17`; config `:1-36` has zero `HasOne`).
- Extra hazard: `OpeningBalancePeriod.cs:78` passes transient `Id` (0 pre-save, per transient-Id pattern) as `SourceId` — any persisted source id is unreliable until save completes.
- So: CompanyId is derivable ONLY if both unenforced hops happen to be valid. Any option relying on the chain for tenant isolation inherits this fragility unless the hops get real FKs first.

### 5. Idempotency: no DB guard anywhere
- `posting_references` index on `(SourceType, SourceId)` is NON-UNIQUE (`PostingReferenceConfiguration.cs:30`; `Migrations/20260916051341_InitialCreate.cs:205-208`). No unique constraint on the table at all.
- `journal_entries` has NO source index (`JournalEntryConfiguration.cs:50-51` indexes only `PeriodId`, `EntryNumber`, both non-unique).
- Duplicate-post protection is in-memory only: `OpeningBalancePeriod.PostOpeningBalances` `IsPosted`/`Status` guards (`:61-65`). No DB-level backstop against concurrent double-post or re-post after reload.
- Stronger breakage: `PostOpeningBalancesHandler.cs:16-21` calls `period.PostOpeningBalances(...)` then `SaveChangesAsync` — but the `JournalEntry` created inside the domain method (`OpeningBalancePeriod.cs:77-85`) is never added to any repository, so it is DISCARDED; only the period's `IsPosted`/`Status` flags persist. Source→JE linkage is broken end-to-end today, not just unindexed.
- Whether re-posting must be idempotent at DB level (unique `source_type+source_id`): UNKNOWN — planner must state the requirement.

### 6. Options table (evidence, no decision)

| | A: FK to JournalEntry + keep SourceType/SourceId as origin trace | B: fully polymorphic, no FK (status quo shape) | C: typed per-source nullable FKs |
|---|---|---|---|
| What changes | Add `HasOne<JournalEntry>().WithMany().HasForeignKey(JournalEntryId).OnDelete(Restrict)` to PostingReference config + migration; keep free-string SourceType/SourceId columns | Validation/domain hardening only (DomainException, CompanyId?, unique index?) — no relationship mapping | Add 1 nullable FK today (`OpeningBalancePeriodId` → Restrict) + keep or drop string columns; each future source = new nullable FK + migration |
| Pros (evidenced) | JE-side orphan rows become impossible (today NOTHING links `posting_references.journal_entry_id` to `journal_entries` — InitialCreate `:94-108` PK only, no FK); matches universal Restrict-for-financial-data convention (configs grep: Restrict everywhere except dimension SetNull); cheapest integrity win | Zero migration risk; matches current reality that linkage is trace-only and the JE from the only caller is discarded (Handler `:16-21`); no schema churn while source-type count is 1 | Only option with DB-enforced validity on BOTH ends; join from JE to source without string matching; company-scoped checks possible per FK; cost today is exactly 1 column |
| Cons (evidenced) | Source side stays a free string: no DB check that `SourceId` exists, no check it belongs to the same company (neither table has CompanyId — §4); typo'd `"OpeningBalance"` variants undetectable; keeps dual-write drift between `JournalEntry.SourceType/SourceId` columns and `posting_references` rows (Context §1: no sync) | Orphan `posting_references` rows possible (delete JE → dangling `journal_entry_id`); cross-company mismatch (`SourceId` is a global long, no tenant scope) undetectable; every integrity rule must live in app code with no backstop | Future cost UNKNOWN (§2: future source count unknown); nullable-column sprawl if many sources; still needs a discriminator or convention to know WHICH FK is populated per row; does not fix the discarded-JE handler bug by itself |
| Company isolation | Partial: JE existence guaranteed, tenant match NOT (no CompanyId on either table; chain in §4 unenforced) — needs app-level check or added CompanyId column to close | None at DB level; fully app-enforced | Best per-source (FK join can verify same-company), but JE side still CompanyId-less via §4 chain |
| Idempotency fit | FK does not deduplicate; still needs unique `(SourceType, SourceId)` decision (§5, UNKNOWN requirement) | Same — needs explicit unique-index decision | Unique index per FK column possible; same requirement decision needed |

### Unknowns (planner/G1 must resolve)
1. Future source entity types/count beyond OpeningBalancePeriod.
2. Whether reversal/correction linkage is in scope for PostingReference.
3. Whether `unique(source_type, source_id)` idempotency is required.
4. Whether the `PostOpeningBalancesHandler` discarded-JE bug is fixed in this loop or a separate task (blocks any option's end-to-end value).
5. Whether `JournalEntry.PeriodId`→`FiscalPeriod` and `FiscalPeriod.YearId`→`FiscalYear` get real FKs (pre-req for trusting the CompanyId chain) or PostingReference/JournalEntry get a direct CompanyId.
## Verification Criteria
Verifier checks this research (not the design — planner decides that):
- [ ] `grep -rn '"OpeningBalance"' src --include=*.cs` outside Migrations returns exactly OpeningBalancePeriod.cs:78 (plus this RESEARCH.md).
- [ ] `grep -rni 'revers\|correction\|void' src --include=*.cs` returns 0 entity-field hits (proves §3).
- [ ] `JournalEntryConfiguration.cs` contains no `HasOne`; `FiscalPeriodConfiguration.cs` contains no `HasOne` (proves §4 unenforced hops).
- [ ] `InitialCreate.cs` posting_references block has PK + 2 non-unique indexes, no FK (proves §5).
- [ ] `PostOpeningBalancesHandler.cs` has no repository call persisting the created JournalEntry (proves discard claim).
- [ ] Every UNKNOWN above is genuinely unanswerable from repo source (no doc/file states it).
- [ ] No design recommendation sentence exists in Requirements & Constraints (planner owns decision).

## Quality Standards
Good decision inputs: every factual claim carries file:line; options describe trade-offs with evidence pointers, not preferences; unknowns labeled UNKNOWN instead of guessed. Anti-patterns: recommending an option, inventing future source types, citing migration Designer echoes as independent usages.

## Task-Specific Research — [G2] domain spec
Exact spec for hardening `src/SmeAccounting.Domain/Entities/PostingReference.cs` + event + port via discovery-first TDD. All paths absolute under `/home/projects/sme_acct/`. Normative source: `docs/PostingReference-Design-2026.md` (§3–§5, §7–§8); precedents verified from source below.

### 1. New ctor signature (replaces current 3-param ctor)
- Current: `public PostingReference(long journalEntryId, string sourceType, long sourceId)` — `PostingReference.cs:11-16`, validates only `sourceType ?? throw ArgumentNullException` (`:14`), no event, no `CompanyId` prop (entity `:5-7` has `JournalEntryId/SourceType/SourceId` only).
- New (Design §3/§5): `public PostingReference(long companyId, long journalEntryId, string sourceType, long sourceId)` — `companyId` FIRST (copies `VoucherType.cs:18`, `TransactionReason.cs:17`, `Bank.cs:16` param order: companyId first). New `public long CompanyId { get; private set; }` property. No navigation props (FK-nav-free per T1 pattern; relationships live in EF config only — G3 task).
- `using SmeAccounting.Domain.Events; using SmeAccounting.Domain.Exceptions;` required at top (copies `VoucherType.cs:1-2`); Domain currently has zero NuGet refs — new code must add none.

### 2. Four DomainException cases + exact messages (Design §5, replaces legacy `ArgumentNullException` at `PostingReference.cs:14`)
Order of guards follows `TransactionReason.cs:19-26` (companyId → FK-id → strings → ids):

| # | Guard (in this order) | Exception + message (verbatim) | Precedent |
|---|---|---|---|
| V1 | `companyId <= 0` | `DomainException("CompanyId must be greater than zero.")` | `VoucherType.cs:20-21`, `TransactionReason.cs:19-20`, `Bank.cs:18-19` identical string |
| V2 | `journalEntryId <= 0` | `DomainException("JournalEntryId must be greater than zero.")` | `TransactionReason.cs:21-22` `VoucherTypeId` guard shape, renamed id |
| V3 | `string.IsNullOrWhiteSpace(sourceType)` | `DomainException("SourceType is required.")` | `VoucherType.cs:22-23` `Code is required.` shape (covers null+empty+whitespace; null no longer `ArgumentNullException`) |
| V4 | `sourceId <= 0` | `DomainException("SourceId must be greater than zero.")` | Same `> 0` FK-id shape as V2 |
| — | `AddDomainEvent(new PostingReferenceCreated(Id, companyId, DateTimeOffset.UtcNow))` as last ctor statement | — | `VoucherType.cs:33`, `TransactionReason.cs:34`, `Bank.cs:30` identical call shape |

FAIL if: any `ArgumentNullException` remains; any guard omitted; `IsNullOrEmpty` used instead of `IsNullOrWhiteSpace` (whitespace `"  "` must throw — copies `Bank_Ctor_EmptyName` test precedent `BankAggregateTests.cs:37`); messages differ in wording/casing/punctuation.

### 3. Timing note — transient JournalEntryId=0 reconciled (Design §7; answers "how does caller pass Id 0?")
- The `journalEntryId > 0` / `sourceId > 0` guards CONTRADICT passing transient 0. Resolution per Design §7: **reference row is created post-JE-persist, when the JE id is assigned** — never with `Id == 0`.
- Caller pattern (verified from Bank flow): `CreateBankCommandHandler.cs:22-25` does `await repository.AddAsync(bank)` (EF `Add`, Id still 0 — `EfBankRepository.cs:35-38` is bare `AddAsync`, no Id assignment) → `await unitOfWork.SaveChangesAsync(...)` (**identity `bigint` PK assigned here** — `InitialCreate.cs:94-108` `id bigint identity`, config `ValueGeneratedOnAdd`) → `return new CreateBankResult(bank.Id)` (Id read AFTER save). PostingReference caller must follow the same two-phase order in one handler: `AddAsync(je)` → `SaveChangesAsync` (JE Id assigned) → `new PostingReference(companyId, je.Id, sourceType, sourceId)` → `AddAsync(pr)` → `SaveChangesAsync`. Single-`SaveChanges` with both adds does NOT work (no navigation props → no EF relationship fixup; PR `JournalEntryId` would persist as 0 → FK violation under G3 Restrict FK).
- No factory method exists on any entity (`grep` ctor pattern: all entities use public ctors, zero `Create` factories) — do NOT invent one; plain ctor post-persist is the pattern.
- Known breakage flagged, not fixed in G2: `OpeningBalancePeriod.cs:78` calls `journalEntry.SetSource("OpeningBalance", Id)` with pre-save `Id == 0` (transient-Id=0 pattern) — under hardened `SetSource`/`PostingReference` guards this call site throws; fixing it is out of scope (Design §9 item 3, handler bug separate task). Executor must NOT silently "fix" it inside G2.
- Test-fake caveat: `FakeBankRepository.AddAsync` (`Fakes.cs:19-23`) just `_banks.Add`, Id stays 0; `FakeUnitOfWork.SaveChangesAsync` (`Fakes.cs:54-58`) only counts calls, assigns no Ids. RED tests for the ctor need no Id generation; any handler-level test must assign `Id` manually on the fake-stored JE before constructing `PostingReference` (same as Bank handler tests reading `bank.Id` post-save).

### 4. PostingReferenceCreated event shape (Design §4, copies `VoucherTypeCreated.cs:1-17` renamed)
- Path: `src/SmeAccounting.Domain/Events/PostingReferenceCreated.cs`. `public class PostingReferenceCreated : DomainEvent`, props `long PostingReferenceId { get; }` + `long CompanyId { get; }`, ctor `(long postingReferenceId, long companyId, DateTimeOffset occurredOn) : base(occurredOn)`. Base `DomainEvent.cs:3-13` supplies `OccurredOn` + `EventId`.
- Minimal payload: Id + CompanyId + timestamp ONLY — no `SourceType`/`SourceId`/`JournalEntryId` (event-minimalism global standard). Raised in entity ctor with provisional `Id == 0` acknowledged (matches `Bank.cs:30` `new BankCreated(Id, ...)` — same provisional-0 semantics; `BankAggregateTests.cs:18-19` asserts `evt.CompanyId` only, never the Id).
- G2 does NOT wire `modelBuilder.Ignore<PostingReferenceCreated>` (DbContext wiring is G3); event class alone triggers no EF mapping failure at build/test time (all 47 existing events follow DbSet+Ignore pairing, but Ignore is only needed once the entity is queried — safe to defer per Design §10 non-goals).

### 5. IPostingReferenceRepository methods (Design §8; shaped per Bank ports)
- Path: `src/SmeAccounting.Domain/Ports/IPostingReferenceRepository.cs`. `using SmeAccounting.Domain.Entities;`, namespace `SmeAccounting.Domain.Ports`.
- Required (3 + idempotency query):
  - `Task<PostingReference?> GetByIdAsync(long id);` — copies `IBankRepository.cs:7`, `ITransactionReasonRepository.cs:7`.
  - `Task<PostingReference?> GetBySourceAsync(string sourceType, long sourceId, long companyId);` — idempotency pre-check named in Design §7–§8; analog of `GetByCodeAsync(string code, long companyId)` (`IBankRepository.cs:8`) with `(SourceType, SourceId)` replacing `Code` (composite natural key mirrors unique `(CompanyId, SourceType, SourceId)` index). Param order: sourceType, sourceId, companyId (Design §8 verbatim).
  - `Task AddAsync(PostingReference reference);` — copies `IBankRepository.cs:10`; no `UpdateAsync` (change tracking handles it — T1-repository pattern).
- Optional (only if executor needs it for G2 tests; NOT required): `GetAllByCompanyAsync(long companyId)` (Bank `GetAllByCompanyAsync` analog) or `GetByJournalEntryIdAsync(long journalEntryId)` (JE→reference lookup matching the kept non-unique `JournalEntryId` index). Verifier PASSES with just the 3 required; FAILS if `GetBySourceAsync` missing (idempotency fast-path has no query) or if method takes `Domain.Entities` types beyond `PostingReference` itself.
- No `UpdateAsync`/`DeleteAsync`: audit rows append-only (Design §9 item 8 — no Deactivate/event beyond Created).

### 6. Private parameterless ctor rule
- `private PostingReference() { }` PRESERVED verbatim (`PostingReference.cs:9`) — EF Core materialization without exposing invalid state (global MEMORY pattern; every entity `VoucherType.cs:16`, `TransactionReason.cs:15`, `Bank.cs:14` has it). FAIL if: removed, made `public`/`protected`/`internal`, or given parameters/body that sets state. Arch tests do not check ctor visibility, but EF materialization + invalid-state encapsulation require it.

### 7. JournalEntry.SetSource hardening (same G2 task, PLAN.md explicit)
- Current `JournalEntry.cs:32-36`: unconditional setter, no validation, callable when posted.
- Hardened (Design §5): three `DomainException` guards — `string.IsNullOrWhiteSpace(sourceType)` (`"SourceType is required."`), `sourceId <= 0` (`"SourceId must be greater than zero."`), `IsPosted` (`"Cannot modify a posted journal entry."` — copies `AddLine` guard message `JournalEntry.cs:47-48`). Stays a setter (no FK semantics, nullable cache columns unchanged — Design §10 non-goal).

### 8. Suggested approach
RED-first in `tests/SmeAccounting.BankTests/`: add `PostingReferenceAggregateTests.cs` with ctor happy-path (event assert `PostingReferenceCreated` CompanyId, cf. `BankAggregateTests.cs:11-20`) + 4 guard Facts (0/-1 companyId, 0 journalEntryId, null/empty/whitespace sourceType, 0 sourceId) + `SetSource` posted-rejection Fact, all failing against current stub; then harden entity + event + port to green. Reuse `FakeUnitOfWork`/`Fakes.cs` List-backed pattern — no EF InMemory, no new NuGet (Domain must stay zero-ref; BankTests references Domain+Application only).

### 9. Verification criteria (executor output checks)
- [ ] `dotnet build SmeAccounting.sln` 0 warnings/errors (TreatWarningsAsErrors).
- [ ] `dotnet test tests/SmeAccounting.ArchitectureTests/` 22/22 (entity in `Domain.Entities`, port `I*` in `Domain.Ports`, event in `Domain.Events`, zero new Domain refs).
- [ ] New `PostingReferenceAggregateTests` green: happy-path asserts props + single `PostingReferenceCreated` with CompanyId; 4 guard Facts each `Assert.Throws<DomainException>` (incl. whitespace sourceType); `SetSource`-on-posted-JE throws.
- [ ] `grep -rn 'ArgumentNullException' src/SmeAccounting.Domain/Entities/PostingReference.cs src/SmeAccounting.Domain/Entities/JournalEntry.cs` = 0 hits (legacy throw gone from hardened path; note `JournalEntry` ctor `:26` `entryNumber ?? throw` is pre-existing and NOT in scope).
- [ ] `grep -n 'private PostingReference()' src/.../PostingReference.cs` = 1 hit, still parameterless.
- [ ] `IPostingReferenceRepository.cs` contains `GetByIdAsync`, `GetBySourceAsync`, `AddAsync`; no `UpdateAsync`/`DeleteAsync`.
- [ ] No migration, DbContext, DI, Application, Api, or `OpeningBalancePeriod`/`PostOpeningBalancesHandler` changes in G2 diff (those are G3/G4/separate tasks).

### 10. Quality standards
Good: exact message strings, guard order companyId→journalEntryId→sourceType→sourceId, event-minimal payload, port mirroring Bank shape, RED tests written before entity change, stale-transient-0 behavior documented not patched. Anti-patterns: inventing a factory/`Create` method, "fixing" the `OpeningBalancePeriod:78` call site or handler bug inside G2, adding `Company`/`JournalEntry` navigation props, enum-izing `SourceType`, adding `UpdateAsync`/`Deactivate`, scaffolding a migration early.

## Task-Specific Research — [G1] FK vs polymorphic decision
Decision research only — planner writes DESIGN.md, executor writes code. All paths absolute under `/home/projects/sme_acct/`. Option labels from Requirements §6.

### 1. Evidence weighing (all re-verified 2026-09-22 from source)
- **1 live SourceType:** sole non-migration literal `"OpeningBalance"` at `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:78` (`journalEntry.SetSource("OpeningBalance", Id)`). `grep SetSource src` = definition (`JournalEntry.cs:32`) + this 1 caller. No other producer exists.
- **Dead null/null command path:** `CreateJournalEntryCommand.cs:10-11` carries optional `SourceType/SourceId`, but `JournalEntryController.cs:39-41` hardcodes `null, null`; no `CreateJournalEntry*Handler` exists (Application grep 0 hits); `CreateJournalEntryCommandValidator.cs:1-22` has zero source rules. Command source path is dead end-to-end.
- **CompanyId chain unenforced at 2 hops:** `JournalEntry.cs:7-17` has no `CompanyId`; `JournalEntryConfiguration.cs:26-27,50` maps bare `period_id` + non-unique index, zero `HasOne`. `FiscalPeriodConfiguration.cs:19-20,45` maps bare `year_id` + non-unique index, zero `HasOne`. Only hop 3 enforced: `FiscalYearConfiguration.cs:38-41` `HasOne<Company> Restrict` on `CompanyId`. Domain ctors validate neither `periodId` (`JournalEntry.cs:24-30`) nor `yearId` (FiscalPeriod ctor). Deriving tenant from the chain is convention-only.
- **Transient-Id hazard:** `OpeningBalancePeriod.cs:78` passes pre-save `Id` (0 per transient-Id=0 pattern) as `SourceId`; any persisted source id is unreliable until save completes.
- **No reversal fields:** `grep -rni 'revers|correction|void' src --include=*.cs` = 0 entity-field hits; `JournalEntry.cs:55-67` only `Post()` + `IsPosted` guard; `JournalEntryConfiguration.cs:1-57` confirms no reversal columns.
- **No idempotency guard:** `PostingReferenceConfiguration.cs:29-30` both indexes non-unique; `InitialCreate.cs:205-208` same; `journal_entries` has no source index (`JournalEntryConfiguration.cs:50-51`). In-memory `IsPosted/Status` guards (`OpeningBalancePeriod.cs:61-65`) are the only dedup.
- **Discarded-JE bug (scope blocker, not fixed here):** `PostOpeningBalancesHandler.cs:16-21` calls `period.PostOpeningBalances(...)` (which news up a `JournalEntry` inside `OpeningBalancePeriod.cs:77-85`) then `SaveChangesAsync` with no repository `Add` of that JE — the JE is discarded, only period flags persist. Any FK/idempotency design has zero end-to-end value until this is fixed in a separate task.
- **Tax snapshot independent:** `ADR-010:102-108` snapshots Tax Type/Code/Treatment/Rate/Rule Version/Effective Date/Legal Reference directly — zero `PostingReference` refs in `ADR-010` (full-file read). Hardening cannot break tax compliance.
- **VAS/Circular 99 silent:** `docs/` search `PostingReference|SourceType` returns only gap inventories + `PaymentMethod-Design-2026.md:79,136,158` (which states free-text `SetSource` linkage "suffices" for PaymentMethod scope — a loop-local decision, not a hardening constraint). No article/clause prescribes reference shape. Any "VAS requires field X" claim is UNKNOWN unless cited per ADR-010 §Critical Regulatory Rule.

### 2. Recommendation: Option A — FK to JournalEntry + keep SourceType/SourceId as origin trace
- **Why A over B:** B (status-quo shape, validation-only) leaves `posting_references.journal_entry_id` dangling — today NOTHING links it to `journal_entries` (`InitialCreate.cs:94-108` PK only, no FK). A closes the JE-side orphan hole with one relationship mapping, matching the universal Restrict-for-financial-data convention (configs grep: Restrict everywhere except dimension SetNull). B keeps every integrity rule in app code with no backstop plus undetectable cross-company `SourceId` mismatch (global long, no tenant scope).
- **Why A over C:** C (typed nullable FK per source) is the only option enforcing the source end, but today that buys exactly 1 column (`OpeningBalancePeriodId`) while future source count is UNKNOWN (Requirements §2: ~50 entities, none post journals). C pays nullable-column sprawl + per-row which-FK-populated discriminator + one migration per future source, yet still does not fix the discarded-JE bug by itself. With 1 live source type, C is over-engineering; revisit C only when a 2nd posting module is evidenced in source.
- **Dual-write sync rule (part of A):** `JournalEntry.SourceType/SourceId` (`JournalEntry.cs:13-14`) and `posting_references` rows are unsynced duplicates today. Under A, `posting_references` is canonical (idempotency + audit), JE columns stay as read-model cache only, written atomically in the same UoW/handler that persists the JE. `SetSource` gets DomainException guards (non-empty type, `sourceId > 0`, reject change once posted) but remains a setter — no FK semantics on the JE side.
- **CompanyId: direct column, not chain:** chain trust requires fixing 2 missing FKs (`PeriodId→fiscal_periods`, `YearId→fiscal_years`) first — out of scope here. A adds direct `CompanyId` on `posting_references` (`HasOne<Company> Restrict`, copied from `FiscalYearConfiguration.cs:38-41` / G2-cross-cutting pattern) populated from the source aggregate's `CompanyId` (e.g. `OpeningBalancePeriod.CompanyId`) at creation time, not derived via joins.

### 3. Migration impact per option
- **A (recommended):** 1 migration `PostingReferenceHarden`: (a) `AddColumn company_id bigint NOT NULL` (backfill plan required — existing rows get 0/default, must resolve per deployment); (b) `AddForeignKey posting_references→journal_entries (journal_entry_id) Restrict` + `AddForeignKey posting_references→companies (company_id) Restrict`; (c) replace non-unique `(SourceType,SourceId)` index with **unique `(CompanyId, SourceType, SourceId)`** (company-scoped idempotency — closes §5 double-post hole; plain unique `(SourceType,SourceId)` is the fallback if planner rejects direct CompanyId); (d) keep non-unique index on `JournalEntryId`; (e) snake_case + `xmin` unchanged. No new tables, no per-source columns, no check constraints. Rollback = drop FKs/indexes/column.
- **B (not recommended):** schema-optional: at most unique index on `(SourceType,SourceId)` (or `(CompanyId,…)` if CompanyId added) + optional `company_id` column. Zero FK DDL, zero orphan protection, zero source-end validity. Cheapest DDL, weakest guarantee.
- **C (deferred):** 1 migration today: nullable `opening_balance_period_id bigint NULL` + `FK→opening_balance_periods Restrict` + `CHECK (exactly one source FK non-null)` + unique index on that FK + still needs JE-side FK from A to avoid orphans. Each future source type = new nullable FK column + new CHECK/index + migration. Scales O(sources); unjustified at N=1.

### 4. Out of scope for this loop (explicit)
1. Fixing `PostOpeningBalancesHandler` discarded-JE bug — separate task; blocks end-to-end value of any option (Requirements unknown #4).
2. Adding real FKs on `JournalEntry.PeriodId→fiscal_periods` / `FiscalPeriod.YearId→fiscal_years` — pre-req for chain trust, separate migration (unknown #5).
3. Reversal/correction/void linkage (`ReversedById`, status enum) — zero evidence in src; UNKNOWN requirement (unknown #2).
4. Enum-izing `SourceType` or wiring `VoucherType/VoucherCategory` to it — no source links them; keep free string max100 + `DomainException` empty/whitespace guard only.
5. Tax snapshot / ADR-010 traceability changes — snapshot is self-contained, no dependency.
6. Backfill of historical `SourceId=0` rows from transient-Id posts — data-migration concern, not schema concern.
7. `IsActive`/soft-delete or effective-dating on PostingReference — audit-trail rows are append-only; no missing-patterns item beyond CompanyId/unique/DomainException/repo/CQRS is adopted.

### 5. Handoff to planner (DESIGN.md must lock)
Chosen option A; direct-vs-chain = direct `CompanyId`; unique index = yes `UNIQUE(company_id, source_type, source_id)`; JE columns = cache, PostingReference = canonical; scope exclusions = list above §4 items 1–7.

## Task-Specific Research — [G1] verification criteria
Verifier checklist for the DESIGN.md hardening spec (Option A: FK→JournalEntry Restrict + direct CompanyId + unique(CompanyId,SourceType,SourceId)). All paths absolute under `/home/projects/sme_acct/`. Do NOT write code — this section only defines pass/fail for the design doc.

### 0. Exact current column types (from InitialCreate — DESIGN must not contradict)
- `src/SmeAccounting.Infrastructure/Migrations/20260916051341_InitialCreate.cs:94-108`: `posting_references (id bigint identity PK, journal_entry_id bigint NOT NULL, source_type varchar(100) NOT NULL maxLength 100, source_id bigint NOT NULL, xmin xid rowversion)`, PK only, no FK. Indexes `:200-208`: `IX_posting_references_journal_entry_id (journal_entry_id)` non-unique + `IX_posting_references_source_type_source_id (source_type, source_id)` non-unique.
- `InitialCreate.cs:82-83`: `journal_entries.source_type varchar(100) NULL, source_id bigint NULL` — nullable cache columns, same varchar(100) width as posting_references.
- `PostingReferenceConfiguration.cs:18-30`: `journal_entry_id` (no Required/FK), `source_type` Required max100, `source_id`, both indexes non-unique, `xmin` rowversion last. `JournalEntryConfiguration.cs:33-38`: `source_type` max100 nullable, `source_id` nullable.
- Verdict: SourceType max length is **100, NOT 20**. Code=20 applies only to master-data `Code` props (`VoucherTypeConfiguration.cs:21-24`, `TransactionReasonConfiguration.cs:24-27` — `code` Required max20). SourceId is `long/bigint` — no length concept. DESIGN.md FAILS if it specifies `HasMaxLength(20)` for SourceType or any max length for SourceId; PASS requires `source_type` Required max100 (unchanged width, nullable→required already true) matching both tables.

### 1. Placement rules (file locations)
- PASS requires DESIGN to place: entity `src/SmeAccounting.Domain/Entities/PostingReference.cs`; event `src/SmeAccounting.Domain/Events/PostingReferenceCreated.cs`; port `src/SmeAccounting.Domain/Ports/IPostingReferenceRepository.cs` (only if G1 requires — under Option A yes); config `src/SmeAccounting.Infrastructure/Persistence/Configurations/PostingReferenceConfiguration.cs` (`internal sealed : IEntityTypeConfiguration<PostingReference>`); repo `src/SmeAccounting.Infrastructure/Repositories/EfPostingReferenceRepository.cs`; wiring `DbSet<PostingReference>` + `modelBuilder.Ignore<PostingReferenceCreated>()` in `SmeAccountingDbContext.cs` + `AddScoped<IPostingReferenceRepository, EfPostingReferenceRepository>()` in `DependencyInjection.cs` (copies T1-VoucherType checklist per global MEMORY).
- FAIL: event or port placed outside `Domain/Events/` or `Domain/Ports/`; config not `internal sealed`; navigation property (e.g. `JournalEntry JournalEntry`) added to entity (violates FK-nav-free pattern — `HasOne<JournalEntry>().WithMany()` in config only, no `Company` nav prop per T1 ref).

### 2. Length rules
- PASS: `source_type` `IsRequired().HasMaxLength(100)` (keeps InitialCreate width, consistent with `JournalEntry.source_type` max100); `company_id` bare `bigint` (no max length, copies `FiscalYearConfiguration.cs:19-20`); `journal_entry_id` / `source_id` bare `bigint`; table `posting_references`, columns snake_case (`id, journal_entry_id, company_id, source_type, source_id, xmin`).
- FAIL: SourceType max20 (Code-pattern misapplied); any `HasMaxLength` on long IDs; camelCase column names; `IsRequired()` dropped from `source_type`.

### 3. Unique rule (idempotency)
- PASS: DESIGN specifies `builder.HasIndex(e => new { e.CompanyId, e.SourceType, e.SourceId }).IsUnique()` REPLACING the current non-unique `(SourceType,SourceId)` index (`PostingReferenceConfiguration.cs:30`), keeps non-unique `HasIndex(e => e.JournalEntryId)` (`:29`) for JE→reference lookup. States semantics: company-scoped single-post guard — duplicate `(CompanyId,SourceType,SourceId)` insert rejected at DB; app pre-check (`GetBySourceAsync`) + `ValidationBehavior` is fast-path only, unique index is backstop (closes RESEARCH Requirements §5 double-post hole; in-memory `IsPosted/Status` guards `OpeningBalancePeriod.cs:61-65` insufficient under concurrency).
- FAIL: keeps non-unique `(SourceType,SourceId)` with no unique replacement; or specifies plain global unique `(SourceType,SourceId)` without CompanyId while also adding direct CompanyId (inconsistent tenant scope); or claims FK alone deduplicates (it does not — Requirements §6 table).

### 4. Restrict rules (both FKs)
- PASS: DESIGN specifies exactly two relationships, both `OnDelete(DeleteBehavior.Restrict)`, copied verbatim from `FiscalYearConfiguration.cs:38-41` / `TransactionReasonConfiguration.cs:44-52` (two-FK precedent):
  `builder.HasOne<JournalEntry>().WithMany().HasForeignKey(e => e.JournalEntryId).OnDelete(DeleteBehavior.Restrict);`
  `builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);`
  Never `Cascade`/`SetNull` on financial data (universal convention — configs grep: Restrict everywhere except dimension SetNull on `JournalEntryLine` optional dimension FKs).
- FAIL: either FK missing (B-shape status quo); `Cascade` or `SetNull` on either FK; `HasOne` with navigation property on entity; FK pointed at `FiscalPeriod`/`FiscalYear` chain instead of direct `CompanyId` (chain hops unenforced — `JournalEntryConfiguration.cs` zero `HasOne`, `FiscalPeriodConfiguration.cs:45` index-only).

### 5. xmin rule
- PASS: `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")` LAST statement in `Configure` (copies every config incl. `VoucherTypeConfiguration.cs:50-52`, `FiscalYearConfiguration.cs:43-45`).
- FAIL: xmin missing, not rowversion, or placed before indexes/FKs.

### 6. DomainException cases (entity ctor + SetSource)
- PASS: DESIGN lists `DomainException` (never `ArgumentNullException` — replaces `PostingReference.cs:14` legacy throw, per T1-invariant pattern): `companyId <= 0` ("CompanyId must be greater than zero." — copies `VoucherType.cs:20-21`); `journalEntryId <= 0` ("JournalEntryId must be greater than zero." — copies `TransactionReason.cs:21-22` VoucherTypeId guard); `string.IsNullOrWhiteSpace(sourceType)` ("SourceType is required."); `sourceId <= 0` ("SourceId must be greater than zero."). Ctor signature `(companyId, journalEntryId, sourceType, sourceId)` + private parameterless ctor preserved + `AddDomainEvent` in ctor. `JournalEntry.SetSource` hardened with non-empty-type + `sourceId > 0` + reject-change-once-posted guards (stays setter, no FK semantics — per §2 recommendation). DESIGN must state creation timing (reference row created post-JE-persist when JE id assigned) to reconcile `journalEntryId/sourceId > 0` guards with transient-Id=0 pattern (`OpeningBalancePeriod.cs:78` passes pre-save 0).
- FAIL: keeps `ArgumentNullException`; omits any of the four guards; allows empty/whitespace SourceType; specifies no timing note while requiring `> 0` (contradicts transient-0 evidence without explanation).

### 7. Event payload
- PASS: `public class PostingReferenceCreated : DomainEvent { long PostingReferenceId; long CompanyId; }` ctor `(postingReferenceId, companyId, occurredOn)` (copies `VoucherTypeCreated.cs:1-17` exactly, renamed ids) — minimal Id+CompanyId+timestamp only, NO SourceType/SourceId/JournalEntryId duplication (event-minimalism global standard); raised via `AddDomainEvent(new PostingReferenceCreated(Id, companyId, DateTimeOffset.UtcNow))` in entity ctor (copies `VoucherType.cs:33`, `TransactionReason.cs:34`); known Id=0 provisional at construction acknowledged. `DbContext` must `Ignore<PostingReferenceCreated>` (no table mapping).
- FAIL: event carries source payload fields; missing CompanyId; raised outside ctor without reason; no `Ignore<Event>` wiring specified.

### 8. Idempotency semantics
- PASS: DESIGN states `posting_references` canonical (idempotency + audit), `JournalEntry.SourceType/SourceId` read-model cache only (`JournalEntry.cs:13-14` nullable max100), both written atomically in same UoW/handler that persists JE; duplicate post → unique-violation conflict surfaced (not silent overwrite); pre-check query named (`GetBySourceAsync(sourceType, sourceId, companyId)`).
- FAIL: designates JE columns canonical and table secondary; or omits atomic same-UoW write rule (reintroduces dual-write drift, Context §1); or claims in-memory `IsPosted` guard suffices (contradicts §5 concurrency hole).

### 9. Out-of-scope list (each explicitly excluded with reason — DESIGN FAILS if any missing)
1. Reversal/correction/void linkage (`ReversedById`, status enum) — excluded: zero evidence (`grep revers|correction|void src` = 0 entity-field hits; `JournalEntry.cs:55-67` Post-only).
2. `JE→Period→Year` chain FK enforcement (`JournalEntry.PeriodId`, `FiscalPeriod.YearId` real FKs) — excluded: separate migration; direct CompanyId chosen precisely to avoid chain trust (Requirements §4 two unenforced hops).
3. `PostOpeningBalancesHandler.cs:16-21` discarded-JE bug fix — excluded: separate task; blocks end-to-end value of any option (Requirements unknown #4).
4. Dead null/null command path (`CreateJournalEntryCommand.cs:10-11` optional source + `JournalEntryController.cs:39-41` hardcoded nulls, no handler exists) — excluded: no handler to wire; not resurrected in this loop.
5. Enum-izing SourceType / wiring VoucherType/VoucherCategory — excluded: no source links them; keep free string max100 + empty/whitespace guard only.
6. Tax snapshot / ADR-010 traceability changes — excluded: snapshot self-contained (`ADR-010:102-108`), zero PostingReference refs.
7. Backfill of historical `SourceId=0` transient rows + `company_id` default-0 backfill plan detail — excluded as data-migration concern, not schema concern (migration adds non-null `company_id`; deployment backfill out of loop scope).
8. `IsActive`/soft-delete / effective-dating on PostingReference — excluded: audit rows append-only; no Deactivate/event beyond minimal Created.

## Task-Specific Research — [G2] domain TDD plan
Scope: domain only — entity `src/SmeAccounting.Domain/Entities/PostingReference.cs` + event `src/SmeAccounting.Domain/Events/PostingReferenceCreated.cs` + port `src/SmeAccounting.Domain/Ports/IPostingReferenceRepository.cs` (+ `JournalEntry.SetSource` guards per PLAN). NO EF/repo-impl/CQRS — those are G3. Normative spec: `docs/PostingReference-Design-2026.md` §3–§5 + RESEARCH [G2] domain spec §1–§10 above.
Context verified 2026-09-22 from source: stub ctor `(journalEntryId, sourceType, sourceId)` with legacy `sourceType ?? throw ArgumentNullException` (`PostingReference.cs:11-16`); no CompanyId, no event, no range/whitespace guards. `JournalEntry.SetSource` unconditional setter (`JournalEntry.cs:32-36`). Tests live in `tests/SmeAccounting.BankTests/` (extend — new file `PostingReferenceAggregateTests.cs`); csproj refs Domain+Application only, xunit 2.9.3 (`SmeAccounting.BankTests.csproj:1-23`); `InternalsVisibleTo SmeAccounting.BankTests` confirmed in `src/SmeAccounting.Application/SmeAccounting.Application.csproj:14`; `DomainEvents` public read-only on `BaseEntity.cs:10`; `DomainException : Exception` single-string ctor (`DomainException.cs:1-6`).

### RED-first test list (all must FAIL against current stub, then go green)
New file `tests/SmeAccounting.BankTests/PostingReferenceAggregateTests.cs`, `namespace SmeAccounting.BankTests`, usings `SmeAccounting.Domain.Entities/Events/Exceptions` (copies `BankAggregateTests.cs:1-4`). 6 Facts, no fakes needed (pure domain — no repo calls; port is interface-only, compile check suffices):

1. `PostingReference_Ctor_Valid_SetsPropsAndRaisesSingleCreatedEvent`
   Arrange: `companyId=1, journalEntryId=7, sourceType="OpeningBalance", sourceId=9`. Act: `new PostingReference(1, 7, "OpeningBalance", 9)` (new 4-param signature — RED fails to compile against 3-param stub, which is the correct RED signal). Assert: `CompanyId/JournalEntryId/SourceType/SourceId` equal inputs; `Assert.Single(ref.DomainEvents.OfType<PostingReferenceCreated>())`; `evt.CompanyId == 1` (copies `BankAggregateTests.cs:11-20`; provisional `Id==0` never asserted per transient-0 pattern).
2. `PostingReference_Ctor_CompanyIdZero_ThrowsDomainException` — Act `new PostingReference(0, 7, "OpeningBalance", 9)`; Assert `Assert.Throws<DomainException>` + `Assert.Equal("CompanyId must be greater than zero.", ex.Message)` (verbatim per Design §5 V1).
3. `PostingReference_Ctor_JournalEntryIdZero_ThrowsDomainException` — Act `new PostingReference(1, 0, "OpeningBalance", 9)`; Assert `DomainException` + `"JournalEntryId must be greater than zero."` (V2).
4. `PostingReference_Ctor_EmptySourceType_ThrowsDomainException` — 3 inputs in one Fact or `[Theory] [InlineData(null)] [InlineData("")] [InlineData("  ")]`: Act `new PostingReference(1, 7, input, 9)`; Assert `DomainException` + `"SourceType is required."` (V3; `IsNullOrWhiteSpace` — `IsNullOrEmpty` FAILs whitespace case; null must throw `DomainException`, NOT legacy `ArgumentNullException`).
5. `PostingReference_Ctor_SourceIdZero_ThrowsDomainException` — Act `new PostingReference(1, 7, "OpeningBalance", 0)`; Assert `DomainException` + `"SourceId must be greater than zero."` (V4).
6. `PostingReferenceCreated_Event_Payload_Minimal` — Act valid ctor; Assert event exposes ONLY `PostingReferenceId + CompanyId + OccurredOn` (no `SourceType/SourceId/JournalEntryId` props — event-minimalism); `Assert.Single(ref.DomainEvents)` (exactly one event).
   Optional 7th (SetSource is same G2 task per PLAN): `JournalEntry_SetSource_OnPosted_Throws` — Arrange posted JE (`new JournalEntry("JE-1", now, 1)` + balanced lines + `Post(...)`); Act `je.SetSource("OpeningBalance", 9)`; Assert `DomainException` `"Cannot modify a posted journal entry."` (copies `AddLine` guard `JournalEntry.cs:47-48`).

### Legacy behavior change note (explicit — verifier must NOT regress this)
Old ctor threw `ArgumentNullException` on null `sourceType` (`PostingReference.cs:14`). Hardened ctor throws `DomainException("SourceType is required.")` for null+empty+whitespace. There is deliberately NO test asserting `ArgumentNullException` — any such test FAILs the task. Verifier checks `grep -rn 'ArgumentNullException' PostingReference.cs JournalEntry.cs(SetSource only)` = 0 hits on hardened path (`JournalEntry` ctor `:26` `entryNumber ?? throw` pre-existing, out of scope).

### Guard order + port compile check
Guard order in ctor: companyId → journalEntryId → sourceType → sourceId (copies `TransactionReason` precedent). Port `IPostingReferenceRepository` (`Domain/Ports/`, `I*` naming): `GetByIdAsync(long)`, `GetBySourceAsync(string sourceType, long sourceId, long companyId)`, `AddAsync(PostingReference)` — no `UpdateAsync/DeleteAsync`; verified by compile + `grep`, no fake needed in G2.

### Verification criteria (verifier checks)
- [ ] `dotnet build SmeAccounting.sln` 0 warn/err; `dotnet test tests/SmeAccounting.ArchitectureTests/` 22/22.
- [ ] `dotnet test tests/SmeAccounting.BankTests/` green incl. 6 new Facts; RED proven (new tests fail vs old stub — 4-param ctor does not compile against 3-param stub; guard Facts throw wrong/no exception pre-harden).
- [ ] Exact message strings asserted (4 messages verbatim incl. trailing periods); whitespace `"  "` sourceType case present.
- [ ] Single `PostingReferenceCreated` with `CompanyId`; payload has no source/JE fields.
- [ ] No `ArgumentNullException` test exists; hardened files contain none on touched paths.
- [ ] Diff touches ONLY `Domain/Entities/PostingReference.cs`, `Domain/Events/PostingReferenceCreated.cs`, `Domain/Ports/IPostingReferenceRepository.cs`, `Domain/Entities/JournalEntry.cs` (SetSource), test file — no migration/DbContext/DI/Application/Api/`OpeningBalancePeriod` changes.

### Quality standards
Good: RED-first (tests written before entity change), exact strings, guard order, minimal event, whitespace covered, legacy-throw removal documented not re-tested, G3 files untouched. Anti-patterns: EF InMemory/new NuGet (banned — List-backed only, and unneeded for pure domain), `Create` factory invention, navigation props, enum-ized SourceType, `UpdateAsync`/`Deactivate`, "fixing" `OpeningBalancePeriod.cs:78` inside G2.

## Task-Specific Research — [G3] EF wiring spec
Exact spec for hardening EF persistence + repository wiring via TDD. All paths absolute under `/home/projects/sme_acct/`. Normative source: `docs/PostingReference-Design-2026.md` §3/§6/§8; every line below re-verified from source 2026-09-22.

### 1. Current PostingReferenceConfiguration.cs full content (what to change)
File `src/SmeAccounting.Infrastructure/Persistence/Configurations/PostingReferenceConfiguration.cs:1-36` verbatim today:
- `:7` `internal sealed class PostingReferenceConfiguration : IEntityTypeConfiguration<PostingReference>` — keep (T1 pattern).
- `:11` `ToTable("posting_references")` — keep.
- `:14-16` `Id` → `id` `ValueGeneratedOnAdd` — keep.
- `:18-19` `JournalEntryId` → `journal_entry_id` (no Required/FK) — keep mapping, ADD relationship (see §2).
- `:21-24` `SourceType` → `source_type` `IsRequired().HasMaxLength(100)` — KEEP EXACTLY (width 100 per Design E8; FAIL if changed to 20).
- `:26-27` `SourceId` → `source_id` — keep.
- `:29` `HasIndex(e => e.JournalEntryId)` non-unique — KEEP (JE→reference lookup).
- `:30` `HasIndex(e => new { e.SourceType, e.SourceId })` non-unique — REPLACE with unique triple (see §2).
- `:32-34` `xmin` rowversion last — KEEP LAST.
- Missing: no `CompanyId` property mapping (entity now HAS `CompanyId` per G2 `PostingReference.cs:8` — config is stale, EF maps it by convention to `CompanyId` camelCase column unless mapped); no `HasOne` of any kind.
Change list (diff must contain exactly these, in this order inside `Configure` — copies `TransactionReasonConfiguration.cs:18-56` two-FK layout):
1. After `JournalEntryId` property block, insert `CompanyId` → `company_id` bare `bigint` block (copies `TransactionReasonConfiguration.cs:18-19`, `BankConfiguration.cs:18-19`): `builder.Property(e => e.CompanyId).HasColumnName("company_id");` — no `IsRequired()` (long non-nullable is required by CLR type), no `HasMaxLength`.
2. Keep `SourceType`/`SourceId` blocks byte-identical.
3. Replace `:30` with `builder.HasIndex(e => new { e.CompanyId, e.SourceType, e.SourceId }).IsUnique();` — company-scoped idempotency backstop (Design §6.3).
4. After indexes, add two relationships (copies `TransactionReasonConfiguration.cs:44-52` verbatim shape, `Company` first then second FK — order matches TransactionReason: Company block then VoucherType block):
   `builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);`
   `builder.HasOne<JournalEntry>().WithMany().HasForeignKey(e => e.JournalEntryId).OnDelete(DeleteBehavior.Restrict);`
   No navigation props on entity (FK-nav-free — G2 entity has none, do NOT add). `DeleteBehavior` needs no new using (`Microsoft.EntityFrameworkCore` already imported at config `:1`).
5. `xmin` block stays LAST statement. FAIL if: `Cascade`/`SetNull` on either FK; `HasMaxLength(20)` on SourceType; any `HasMaxLength` on long IDs; camelCase columns; xmin moved above indexes/FKs.

### 2. EfPostingReferenceRepository shape (copy EfBankRepository)
New file `src/SmeAccounting.Infrastructure/Repositories/EfPostingReferenceRepository.cs`, `public class EfPostingReferenceRepository : IPostingReferenceRepository` (public, non-sealed — copies `EfBankRepository.cs:8`). Usings: `SmeAccounting.Domain.Entities` (only needed if signature names type — interface already carries it; Bank repo imports Entities+Ports+Persistence), `SmeAccounting.Domain.Ports`, `SmeAccounting.Infrastructure.Persistence`. Ctor: `public EfPostingReferenceRepository(SmeAccountingDbContext context) => _context = context;` with `private readonly SmeAccountingDbContext _context;` (copies `:10-12`).
Methods (3, mirroring port `IPostingReferenceRepository.cs:7-9`):
- `GetByIdAsync(long id)` → `await _context.PostingReferences.FirstOrDefaultAsync(e => e.Id == id);` TRACKED (copies `EfBankRepository.cs:14-18` — single-entity lookups stay tracked, no `AsNoTracking`).
- `GetBySourceAsync(string sourceType, long sourceId, long companyId)` → `await _context.PostingReferences.FirstOrDefaultAsync(e => e.SourceType == sourceType && e.SourceId == sourceId && e.CompanyId == companyId);` TRACKED (analog of Bank `GetByCodeAsync(code, companyId)` `:20-24` with `(SourceType, SourceId)` replacing `Code`). Param order sourceType, sourceId, companyId per port.
- `AddAsync(PostingReference reference)` → `await _context.PostingReferences.AddAsync(reference);` (copies `:35-38` bare delegate, no SaveChanges — UoW owns it).
No `GetAllByCompanyAsync` (port has none — do NOT invent). Hence NO `AsNoTracking` and NO `OrderBy` in this repo: Bank uses `AsNoTracking()+OrderBy(Code)` ONLY on its list query (`:26-33`); with no list method there is nothing to detach or order. FAIL if: `UpdateAsync`/`DeleteAsync` added; `SaveChangesAsync` called inside repo; `DbSet` other than `PostingReferences` touched.

### 3. DbContext exact lines to add
File `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs`:
- `DbSet<PostingReference> PostingReferences` ALREADY EXISTS at `:16` (`DbSet<PostingReference> PostingReferences => Set<PostingReference>();`) — NO DbSet edit needed. Verifier checks zero diff on `:16`.
- ADD ONE line in `OnModelCreating`: `modelBuilder.Ignore<PostingReferenceCreated>();` — placement copies BankCreated pattern at `:106-108`: append after `modelBuilder.Ignore<BankAccountCreated>();` (`:108`), i.e. as new last Ignore line before `:110` `ApplyConfigurationsFromAssembly`. `PostingReferenceCreated` resolves via existing `using SmeAccounting.Domain.Events;` (`:3`) — no new using. FAIL if: second `DbSet<PostingReference>` added; Ignore placed before `Ignore<DomainEvent>`; `ApplyConfigurationsFromAssembly` line touched.

### 4. DI exact line
File `src/SmeAccounting.Infrastructure/DependencyInjection.cs`: add ONE line `services.AddScoped<IPostingReferenceRepository, EfPostingReferenceRepository>();` — placement after Bank block (`:66-68` `IBank...` lines), i.e. after `:68` `AddScoped<IBankAccountRepository, EfBankAccountRepository>` and before `:69` `IUsersRepository` line (keeps Bank-group adjacency; PostingReference groups with Bank/posting area, not alphabetically). No new usings (`Domain.Ports` `:4` + `Infrastructure.Repositories` `:7` already imported). FAIL if: `AddSingleton`/`AddTransient` lifetime used; interface/impl names misspelled; line added outside `AddInfrastructure` method.

### 5. Repository test approach (BankTests fake-repo + TDD)
- RED-first in `tests/SmeAccounting.BankTests/`: new `FakePostingReferenceRepository : IPostingReferenceRepository` in `Fakes.cs` (copies `FakeBankRepository` `Fakes.cs:6-26` List-backed shape): `List<PostingReference> _items`, `GetByIdAsync` by Id, `GetBySourceAsync(sourceType, sourceId, companyId)` by triple match (copies `GetByCodeAsync(code, companyId)` `:13-14` two-field match extended to three), `AddAsync` list-add, `Stored` accessor. Reuse existing `FakeUnitOfWork` (`:50-59`, counts saves, assigns no Ids) — no new UoW fake.
- RED tests fail meaningfully: `GetBySourceAsync` on empty store returns null (idempotency pre-check negative path); after `AddAsync` + manual-Id assignment the triple lookup returns the row (positive path). Id stays 0 in fakes (EF `ValueGeneratedOnAdd` identity only assigns on real `SaveChanges` — same caveat as RESEARCH [G2] §3 timing note); handler-level tests must assign Id manually before constructing dependent rows.
- NO EF InMemory, NO new NuGet (BankTests refs Domain+Application only per `SmeAccounting.BankTests.csproj`; Ef repo impl itself is NOT unit-tested — build + `dotnet ef migrations` check-only review in G4 covers it, per PaymentMethod G3 pattern). FAIL if: `Microsoft.EntityFrameworkCore.InMemory` package added; test references Infrastructure project.
- SIBLING-TASK DEPENDENCY (CQRS task): `GetBySourceAsync` fake is REQUIRED by the sibling Application-CQRS task's duplicate-post validator/handler tests (idempotency pre-check `GetBySourceAsync(sourceType, sourceId, companyId)` returning non-null → conflict path). G3 must land the fake + interface-conformant `AddAsync`/`GetByIdAsync` FIRST so the CQRS task reuses `FakePostingReferenceRepository` without modification; if CQRS lands first it must stub the same triple-match signature verbatim or G3 overwrites it. Flag in STATUS when G3 fake lands.

### Suggested Approach
Apply config diff (§1) + new Ef repo (§2) + one-line DbContext Ignore + one-line DI (§3–§4), RED-first with FakePostingReferenceRepository in BankTests (§5); build + BankTests green, arch 22/22, no migration scaffold in G3 (G4 owns check-only `migrations add` review).

### Verification Criteria
- [ ] `dotnet build SmeAccounting.sln` 0 warn/err.
- [ ] `dotnet test tests/SmeAccounting.ArchitectureTests/` 22/22.
- [ ] `dotnet test tests/SmeAccounting.BankTests/` green incl. new fake-backed `GetBySourceAsync` null + found Facts.
- [ ] `grep -n 'company_id' PostingReferenceConfiguration.cs` = 1 hit; `grep -c 'HasOne' PostingReferenceConfiguration.cs` = 2; `grep -n 'IsUnique' PostingReferenceConfiguration.cs` = 1 (triple); `grep -n 'HasMaxLength(100)' PostingReferenceConfiguration.cs` = 1 (SourceType only); `Restrict` = 2 hits, `Cascade|SetNull` = 0.
- [ ] `grep -n 'Ignore<PostingReferenceCreated>' SmeAccountingDbContext.cs` = 1; `DbSet<PostingReference>` count still 1.
- [ ] `grep -n 'IPostingReferenceRepository, EfPostingReferenceRepository' DependencyInjection.cs` = 1 with `AddScoped`.
- [ ] `grep -rn 'InMemory' tests/SmeAccounting.BankTests/*.csproj` = 0; no Infrastructure reference from BankTests.
- [ ] Diff touches ONLY config + new repo + DbContext(1 line) + DI(1 line) + BankTests fake/tests — no entity/event/port/Application/Api/migration changes.

### Quality Standards
Good: byte-identical copy of Bank/TransactionReason shapes with only triple-index + GetBySource delta, xmin-last preserved, tracked single-lookups (no cargo-cult AsNoTracking), sibling-task fake reuse noted. Anti-patterns: `AsNoTracking` on single-entity lookups, invented `GetAllByCompanyAsync`/`UpdateAsync`, second DbSet, `Cascade`, SourceType max20, EF InMemory package, scaffolding migration inside G3.

## Task-Specific Research — [G3] CQRS spec
Exact spec for Application CQRS + Api edge via TDD. All paths absolute under `/home/projects/sme_acct/`. Normative source: `docs/PostingReference-Design-2026.md` §7–§8; every line below re-verified from source 2026-09-22.

### 1. Flat vs feature-folder layout — FLAT (PaymentMethod-faithful)
- PaymentMethod (the loop-mandated precedent) is FLAT at Application root: `Application/Commands/CreatePaymentMethodCommand.cs` (namespace `SmeAccounting.Application.Commands`), `Application/Handlers/CreatePaymentMethodHandler.cs` (`...Handlers`), `Application/Queries/GetPaymentMethodQuery.cs` + `GetPaymentMethodsByCompanyQuery.cs` (`...Queries`), `Application/Validators/CreatePaymentMethodCommandValidator.cs` (`...Validators`), `Application/DTOs/PaymentMethodDto.cs` (`...DTOs`). Verified by glob `**/*PaymentMethod*` = 10 files, zero under a `PaymentMethods/` feature folder.
- BankAccounts is the COUNTER-pattern (feature folder): `Application/BankAccounts/Commands/CreateBankAccountCommand.cs` (namespace `SmeAccounting.Application.BankAccounts.Commands`), `BankAccounts/Queries/*`, `BankAccounts/DTOs/BankAccountDto.cs`. Verified by glob — `BankAccounts/`, `BankBranches/` folders exist; PaymentMethod/PaymentTerm/CompanySetting files do NOT live in feature folders.
- Global MEMORY (PaymentMethod slice, task G2) locks the decision: "flat Application layout (Commands/Handlers/Queries/Validators/DTOs) over Bank feature-folders". Executor follows flat — new files go to Application root folders, namespaces `SmeAccounting.Application.Commands|Handlers|Queries|Validators|DTOs`. FAIL if: `Application/PostingReferences/` feature folder created; `...PostingReferences.Commands` namespaces used.

### 2. CreatePostingReferenceCommand fields + validator rules
- Command (copies `CreatePaymentMethodCommand.cs:6-12` record shape, `string` SourceType instead of enum Category):
  `public record CreatePostingReferenceCommand(long CompanyId, long JournalEntryId, string SourceType, long SourceId) : IRequest<CreatePostingReferenceResult>;`
  `public record CreatePostingReferenceResult(long Id);`
  Path `Application/Commands/CreatePostingReferenceCommand.cs`. Field order mirrors entity ctor `(companyId, journalEntryId, sourceType, sourceId)` (`PostingReference.cs:15`). No optional params (all four guarded `> 0`/non-empty in domain — Design §5 V1–V4).
- Validator (copies `CreatePaymentMethodCommandValidator.cs:1-27` rule shape), path `Application/Validators/CreatePostingReferenceCommandValidator.cs`:
  - `CompanyId` → `GreaterThan(0)` ("Company ID is required." — copies PaymentMethod `:10-11` / PaymentTerm `:10-11` verbatim).
  - `JournalEntryId` → `GreaterThan(0)` ("Journal entry ID is required." — same sentence shape, new field).
  - `SourceType` → `NotEmpty()` ("Source type is required.") + `MaximumLength(100)` ("Source type cannot exceed 100 characters." — width 100 per Design E8 / InitialCreate varchar(100); FAIL if 20). NO `IsInEnum` — SourceType is `string`, not an enum; the PaymentMethod `Category IsInEnum` rule (`:21-22`) applies only to enum-typed members and PaymentMethod-slice G2 explicitly rejected enum-izing SourceType (Design §9 item 5).
  - `SourceId` → `GreaterThan(0)` ("Source ID is required.").
  Each rule mirrors a domain guard (V1–V4) so ValidationBehavior rejects before the handler constructs the entity; domain ctor remains the backstop.

### 3. Idempotency path — DECISION: throw on duplicate (not return-existing)
- Spawn prompt suggested return-existing (idempotent create). REJECTED with reason: normative Design §7 states "Duplicate post → unique-violation conflict surfaced (not silent overwrite)". Return-existing would silently swallow the second post and return the old Id — exactly the "silent" behavior the design forbids.
- Codebase evidence supports throw: NO handler in `Application/Handlers/` performs a return-existing pre-check (grep `GetBySourceAsync|already exists|conflict` in src = only port signature + one domain-level account-entry guard in `OpeningBalancePeriod.cs:52`, zero handler-level duplicate patterns). The universal handler failure type is `InvalidOperationException` — all 18 Deactivate handlers throw `InvalidOperationException($"... with ID ... not found.")` (e.g. `DeactivatePaymentMethodHandler.cs:18`). No `DuplicatePostException`/custom conflict type exists anywhere.
- Specified handler behavior (`Application/Handlers/CreatePostingReferenceHandler.cs`, copies `CreatePaymentMethodHandler.cs:1-30` shape, `internal sealed`, ctor `(IPostingReferenceRepository repository, IUnitOfWork unitOfWork)`):
  1. `var existing = await repository.GetBySourceAsync(request.SourceType, request.SourceId, request.CompanyId);`
  2. `if (existing is not null) throw new InvalidOperationException($"Posting reference for source '{request.SourceType}' with ID {request.SourceId} already exists.");`
  3. Else `new PostingReference(...)` → `AddAsync` → `SaveChangesAsync` → `return new CreatePostingReferenceResult(reference.Id);`
  Param order `GetBySourceAsync(sourceType, sourceId, companyId)` verbatim per port (`IPostingReferenceRepository.cs:8`). Unique triple index (G3-EF task) is the DB backstop; this pre-check is the fast-path only.

### 4. GetById + GetBySource queries + DTO shape
- `Application/Queries/GetPostingReferenceByIdQuery.cs`: `public record GetPostingReferenceByIdQuery(long PostingReferenceId) : IRequest<PostingReferenceDto?>;` (copies `GetPaymentMethodQuery.cs:6` naming `XxxId`, nullable-DTO return).
- `Application/Queries/GetPostingReferenceBySourceQuery.cs`: `public record GetPostingReferenceBySourceQuery(string SourceType, long SourceId, long CompanyId) : IRequest<PostingReferenceDto?>;` (param order matches port signature).
- Handlers (copy `GetPaymentMethodHandler.cs:1-27`): `internal sealed`, repo-only ctor, `GetByIdAsync`/`GetBySourceAsync` call, `entity is null ? null : new PostingReferenceDto(...)` null-passthrough (no not-found throw on reads — matches PaymentMethod read shape).
- DTO `Application/DTOs/PostingReferenceDto.cs` (copies `PaymentMethodDto.cs:1-11` positional-record shape, all-scalar, no domain refs):
  `public record PostingReferenceDto(long Id, long CompanyId, long JournalEntryId, string SourceType, long SourceId);`
  No `IsActive` (audit rows append-only, Design §9 item 8 — no Deactivate), no `Category.ToString()` mapping (no enum member). FAIL if DTO references `Domain.Entities`.

### 5. Thin controller pattern — copy PaymentTermController.cs
- Exact file: `src/SmeAccounting.Api/Controllers/PaymentTermController.cs` (64 lines; `PaymentMethodController.cs` is byte-identical in shape — either is a valid copy source; PaymentTerm named first per spawn order). Pattern, adapted (PostingReference has NO enum → drop the `Enum.Parse` line; no Deactivate action → drop it, audit append-only):
  - `public class PostingReferenceController : Controller` with ctor `IMediator _mediator` (`:13-18`).
  - Read action: `[HttpGet] Index` or `Details(long id)` → `await _mediator.Send(new GetPostingReferenceByIdQuery(id), ct)` → `View(dto)` (copies `:20-25` Index shape).
  - `[HttpGet] Create() => View(new CreatePostingReferenceViewModel())` + `[HttpPost][ValidateAntiForgeryToken] Create(model, ct)` with `if (!ModelState.IsValid) return View(model);` then `try { var command = new CreatePostingReferenceCommand(...); await _mediator.Send(command, ct); return RedirectToAction(...); } catch (ValidationException ex) { foreach errors ModelState.AddModelError(...); return View(model); }` (copies `:30-55`, minus `Enum.Parse<...>` line `:38`).
  - `using` allow-list: `FluentValidation` (for `ValidationException`), `MediatR`, `Microsoft.AspNetCore.Mvc`, `SmeAccounting.Api.ViewModels`, `SmeAccounting.Application.Commands`, `SmeAccounting.Application.Queries`. FAIL if `using SmeAccounting.Domain.Entities` or `Domain.Ports` appears in Api (arch rule — controllers must never reference them; PaymentMethod-slice precedent: `Domain.ValueObjects` enum using passes only when an enum crosses the boundary — PostingReference has none, so no Domain using at all).

### 6. ValidationBehavior pipeline — auto-run, no manual wiring
- `Application/DependencyInjection.cs:10-21`: `AddMediatR(cfg => { cfg.RegisterServicesFromAssembly(...); cfg.AddOpenBehavior(typeof(ValidationBehavior<,>)); })` + `services.AddValidatorsFromAssembly(typeof(DependencyInjection).Assembly)` (`:18`). Any `AbstractValidator<CreatePostingReferenceCommand>` in the assembly is picked up by the scan; `ValidationBehavior.cs:6-32` runs ALL `IValidator<T>` before the handler and throws `ValidationException` on failure. Executor adds ZERO wiring — placing the validator class in `Application/Validators/` suffices. Verifier checks `DependencyInjection.cs` zero-diff.

### 7. Test plan (RED-first BankTests, List-backed fakes, no EF InMemory)
- Harness facts (re-verified): `SmeAccounting.BankTests.csproj` refs Domain+Application only (`:15-16`), xunit 2.9.3; `Application.csproj:14` has `InternalsVisibleTo SmeAccounting.BankTests` (internal handlers visible); `Fakes.cs` holds `FakeBankRepository`/`FakePaymentMethodRepository` List-backed shapes + `FakeUnitOfWork` (counts saves, assigns no Ids — `:50-59`).
- New `FakePostingReferenceRepository : IPostingReferenceRepository` in `Fakes.cs` — OWNED by sibling G3-EF task (RESEARCH [G3] EF §5): `List<PostingReference> _items`, `GetByIdAsync` by Id, `GetBySourceAsync(sourceType, sourceId, companyId)` by TRIPLE match (extends Bank `GetByCodeAsync(code, companyId)` two-field match `:13-14` to three), `AddAsync` list-add, `Stored` accessor. CQRS executor reuses it verbatim — if EF task has not landed, CQRS stubs the same triple-match signature byte-identically or EF overwrites. Id stays 0 in fakes (EF identity only assigns on real SaveChanges — [G2] §3 timing note); tests assert `Stored.Count`/`SaveCalledCount`, never generated Ids.
- RED tests (new file, e.g. `PostingReferenceCqrsTests.cs`), all FAIL before Application files exist (correct RED = does-not-compile, same as G2 4-param-ctor RED):
  1. Validator-pass: valid command `(1, 7, "OpeningBalance", 9)` → `new CreatePostingReferenceCommandValidator().ValidateAsync(cmd)` `IsValid`.
  2. Validator-fail ×4 (mirrors domain V1–V4): `CompanyId=0`, `JournalEntryId=0`, `SourceType=""` (+ `"  "` whitespace — `NotEmpty` covers both, same as domain `IsNullOrWhiteSpace`), `SourceId=0` → each `!IsValid`.
  3. Validator-fail length: `SourceType = new string('x', 101)` → `!IsValid` (max100 boundary).
  4. Handler happy path: empty fake → `await handler.Handle(validCmd)` → `Stored.Count == 1`, `SaveCalledCount == 1`, result is `CreatePostingReferenceResult`.
  5. Handler duplicate-post path: fake pre-seeded via `new PostingReference(1, 7, "OpeningBalance", 9)` + `AddAsync` → `await handler.Handle(sameTripleCmd)` → `Assert.ThrowsAsync<InvalidOperationException>`; `Stored.Count` still 1, second save NOT called (or called once with no add — assert count unchanged).
  6. Query null-passthrough: `GetPostingReferenceByIdHandler` on empty fake → null; after add → DTO with equal `CompanyId/JournalEntryId/SourceType/SourceId`.
- FAIL if: `Microsoft.EntityFrameworkCore.InMemory` added; BankTests references Infrastructure; tests assert generated `Id != 0` from fakes (impossible — fakes assign no Ids).

### Suggested Approach
Add flat-layout command+result, validator (NotEmpty+Max100, no IsInEnum), idempotent-throw handler (GetBySourceAsync pre-check → InvalidOperationException per Design §7), two queries+handlers+DTO, thin controller copied from PaymentTermController minus Enum.Parse/Deactivate; RED-first BankTests reusing the EF-task `FakePostingReferenceRepository` triple-match fake.

### Verification Criteria
- [ ] `dotnet build SmeAccounting.sln` 0 warn/err; ArchitectureTests 22/22 (commands in `Application.Commands`, handlers `internal sealed`, no `Domain.Entities` using in Api).
- [ ] New files ONLY at `Application/{Commands,Handlers,Queries,Validators,DTOs}/` + `Api/Controllers/PostingReferenceController.cs` + BankTests test file (`Fakes.cs` fake owned by EF task — CQRS diff must not alter its signature).
- [ ] Validator: pass + 4 guard-fails + 101-char length-fail green; no `IsInEnum` on SourceType.
- [ ] Handler: happy path stores 1 + saves once; duplicate triple throws `InvalidOperationException`, store count unchanged.
- [ ] Controller compiles with zero `SmeAccounting.Domain.*` usings; `DependencyInjection.cs` zero-diff (pipeline auto-run).
- [ ] No migration/DbContext/DI/entity/event/port changes in CQRS diff.

### Quality Standards
Good: PaymentMethod-faithful flat files, message sentences matching validator conventions ("... is required." / "... cannot exceed 100 characters."), duplicate-throw decision traced to Design §7 + InvalidOperationException precedent (not invented exception type), fake reuse without signature drift. Anti-patterns: feature-folder layout, `IsInEnum` on string SourceType, max20 on SourceType, return-existing silent idempotency, Deactivate action on append-only audit rows, manual validator wiring, EF InMemory, asserting fake-generated Ids.

## Task-Specific Research — [G4] gate protocol
Exact verify-only protocol for core-to-edge gate. All commands run from `/home/projects/sme_acct/` (repo root, where `SmeAccounting.sln` lives). Executor writes NO code in G4 except the check-only scaffolded migration files produced by `migrations add` (reviewed, never applied); verifier re-runs steps 1–3 to confirm. Normative expectations: PLAN.md [G4] + docs/PostingReference-Design-2026.md §3/§6 + RESEARCH [G1] §3 (Option A migration impact) + [G3] EF §1–§4 + [G3] CQRS Verification Criteria.

### 1. Step 1 — build (0 warn / 0 err)
- Command: `dotnet build SmeAccounting.sln`
- Expected: `0 Warning(s)`, `0 Error(s)` (TreatWarningsAsErrors=true per Directory.Build.props — any code warning fails the build).
- Benign (PASS, not failure): NuGet package locale/code-page warnings on restore — global MEMORY confirms TreatWarningsAsErrors does NOT promote NuGet locale warnings to errors.
- Failure: any `error` line; any `warning CSxxxx` from `src/`/`tests/` code (unused using CS8019/CS0219, missing using CS0246, DTO record CS8955, nullable CS8600-family); build abort/OOM (if OOM: `pkill -f MSBuild` per G3-batch learning, then re-run — do NOT count as pass).

### 2. Step 2 — architecture tests (22/22)
- Command: `dotnet test tests/SmeAccounting.ArchitectureTests/`
- Expected: `Failed: 0, Passed: 22, Skipped: 0, Total: 22` (22 NetArchTest rules: entity in Domain.Entities, port `I*` in Domain.Ports, event in Domain.Events, controllers never reference Domain.Entities/Domain.Ports, Domain zero NuGet refs).
- Failure: any Failed or Skipped ≠ 0; any Arch failure from PostingReference files (wrong namespace, Api `using SmeAccounting.Domain.*`, new Domain NuGet ref).
- Benign: locale warnings in test-host output; timing fluctuations. A skipped test is a failure, never benign.

### 3. Step 3 — BankTests regression (45/45)
- Command: `dotnet test tests/SmeAccounting.BankTests/`
- Expected: `Failed: 0, Passed: 45, Skipped: 0, Total: 45` with count breakdown (matches MEMORY ledger):
  - 27 pre-existing (Bank hierarchy + PaymentMethod + sibling coverage before this loop),
  - +6 domain (`PostingReferenceAggregateTests.cs` per [G2] TDD plan RED 1–6: happy-path, companyId, journalEntryId, sourceType null/empty/whitespace, sourceId, minimal-payload),
  - +2 EF (`PostingReferenceRepositoryTests.cs`: empty-store null + after-add triple-match per [G3] EF §5),
  - +10 CQRS (`PostingReferenceCqrsTests.cs`: validator pass + 4 guard-fails + 101-char length + handler happy + handler duplicate-throw + 2 query null-passthrough per [G3] CQRS §7),
  - 27 + 6 + 2 + 10 = 45.
- Failure: any Failed/Skipped; total ≠ 45 (missing file = scope leak; extra > 45 without PLAN change = unapproved scope); tests asserting fake-generated `Id != 0` (fakes assign no Ids — [G2] §3 timing note); `InMemory` package or Infrastructure reference added to BankTests csproj.
- Benign: locale warnings only. Flaky-timing retries are NOT benign — must go green on clean re-run.

### 4. Step 4 — check-only migration review (scaffold + read, NEVER apply)
- Precondition: steps 1–3 green (EF Core reads compiled assemblies — build must succeed first per G3-batch learning).
- Scaffold command ONLY: `dotnet ef migrations add PostingReferenceHarden --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- FORBIDDEN without explicit approval: `dotnet ef database update` (any args), `dotnet ef database drop`, any `psql` write/DDL against `sme_acct_dev`. Scaffold/script render offline; `update` needs live DB + approval (PaymentMethod G3 check-only precedent).
- Review artifacts: new `<Timestamp>_PostingReferenceHarden.cs` (`Up`/`Down`) + Designer + snapshot diff under `src/SmeAccounting.Infrastructure/Migrations/`.
- Expected `Up()` (Option A per [G1] §3 — alter existing table, NO new table):
  1. `AddColumn company_id bigint NOT NULL` on `posting_references` (backfill note: existing rows get `defaultValue: 0L` — production backfill out of loop scope per Design §9 item 7);
  2. `AddForeignKey posting_references→journal_entries (journal_entry_id) Restrict` + `AddForeignKey posting_references→companies (company_id) Restrict`;
  3. replace non-unique `(source_type, source_id)` index with `CreateIndex UNIQUE(company_id, source_type, source_id)`;
  4. keep non-unique `IX_posting_references_journal_entry_id`; snake_case names; `xmin` untouched.
- Expected `Down()`: exact reversal only (drop FKs → drop unique index → restore prior non-unique index → drop `company_id` column).
- R1–R7 per-item verdicts (each quoted PASS/FAIL in executor report, copied from PaymentMethod G3 pattern):
  - R1 single purpose: migration touches ONLY `posting_references` (+ its indexes/FKs) — FAIL if any other table altered/created.
  - R2 unique: `IsUnique` triple `(company_id, source_type, source_id)` present exactly once — FAIL if non-unique kept with no unique replacement, or global `(source_type, source_id)` unique without CompanyId.
  - R3 Restrict: exactly 2 `ReferentialAction.Restrict` (JE + Company), `Cascade`/`SetNull` count 0 — FAIL otherwise.
  - R4 widths: `source_type varchar(100)` unchanged, NO `HasMaxLength(20)`, no length on bigint IDs — FAIL on Code-20 misapplication.
  - R5 snake_case: table `posting_references`, columns `id/journal_entry_id/company_id/source_type/source_id/xmin` — FAIL on camelCase.
  - R6 xmin: `xmin xid rowversion` preserved, rowversion last — FAIL if dropped/moved/converted.
  - R7 Down reversal: `Down()` drops exactly what `Up()` added in reverse order — FAIL if lossy (drops unrelated index/table) or no-op.
- Failure: any R-FAIL; `Up()` creating a second table; `database update` run without approval (process violation even if SQL is correct).
- Benign: scaffold timestamp-prefix differences; Designer whitespace churn. Nothing else.

### Suggested Approach
Run steps 1→2→3 in order from repo root, record verbatim tallies; only then scaffold step 4 and publish R1–R7 quoted verdicts; never run `database update`.

### Verification Criteria
- [ ] `dotnet build SmeAccounting.sln` → 0 Warning(s) / 0 Error(s) (locale warnings only).
- [ ] `dotnet test tests/SmeAccounting.ArchitectureTests/` → 22/22, 0 failed/skipped.
- [ ] `dotnet test tests/SmeAccounting.BankTests/` → 45/45 with 27+6+2+10 composition, 0 failed/skipped.
- [ ] `PostingReferenceHarden` migration scaffolded, `Up` = AddColumn + 2 Restrict FKs + unique triple (R1–R7 all PASS quoted), `Down` = exact reversal.
- [ ] No `database update`/DB write ran; no src/test file changed in G4 diff except scaffolded migration files.

### Quality Standards
Good: exact commands from repo root, verbatim tallies, count arithmetic shown, R1–R7 each with quoted evidence line, benign-locale vs real-failure split explicit. Anti-patterns: running `database update` without approval, counting locale warnings as failures, accepting skipped tests, asserting fake-generated Ids, scaffolding migration before build+tests green.

## Task-Specific Research — [G4] migration expectations
Check-only scaffold expectations for `dotnet ef migrations add PostingReferenceHarden` (never `database update`). All paths absolute under `/home/projects/sme_acct/`. Ground truth re-verified 2026-09-22: config hardened (`PostingReferenceConfiguration.cs:1-50` — `company_id` `:21-22`, unique triple `:33-34`, dual Restrict `:36-44`, xmin last `:46-48`), entity 4-param ctor with CompanyId (`PostingReference.cs:8,15`), snapshot/migrations STALE (snapshot `:1722-1758` has no `CompanyId`, no FKs, non-unique indexes — matches `InitialCreate.cs:94-108` + `:200-208`). The model-vs-snapshot delta is exactly the hardening, so the scaffolded migration must be ALTER-only.

### 1. ALTER, not CreateTable — why
- Table `posting_references` already exists since `InitialCreate.cs:94-108` (columns `id`, `journal_entry_id`, `source_type varchar(100)`, `source_id`, `xmin`; PK only, no FK). Every later Designer + snapshot repeats that shape (e.g. `AddPaymentMethod.Designer.cs` posting_references block, snapshot `:1722-1758`).
- The ONLY model changes since the last migration are the G3 config edits (new `CompanyId` property, 2 `HasOne` relationships, index replacement). EF Core therefore renders `AddColumn` + `AddForeignKey` + `DropIndex`/`CreateIndex` — never `CreateTable`.
- FAIL if `Up()` contains `CreateTable(name: "posting_references")` (duplicate-table scaffold = stale build or wrong baseline; rebuild first per G3-batch learning).

### 2. Expected Up() — exact operations
1. `AddColumn company_id bigint NOT NULL` on `posting_references` — precedent `AccountingFoundation.cs:33-38` (`fiscal_years.company_id`, `:81-86` `accounts.company_id`, `:102-107` `account_groups.company_id`, all `nullable: false, defaultValue: 0L`).
2. `AddForeignKey FK_posting_references_journal_entries_journal_entry_id → journal_entries(id) Restrict` + `AddForeignKey FK_posting_references_companies_company_id → companies(id) Restrict` — precedent `AccountingFoundation.cs:337-342` (`FK_fiscal_years_companies_company_id ... Restrict`); expected names follow EF convention `FK_posting_references_<principal>_<column>`.
3. `DropIndex IX_posting_references_source_type_source_id` (the old non-unique pair from `InitialCreate.cs:205-208`) + `CreateIndex IX_posting_references_company_id_source_type_source_id UNIQUE(company_id, source_type, source_id)`.
4. Keep: non-unique `IX_posting_references_journal_entry_id` (`InitialCreate.cs:200-203`), `source_type varchar(100)` width, `xmin xid rowversion`.
- Expected Down(): exact reversal in reverse order — drop 2 FKs → drop unique triple index → restore prior non-unique `(source_type, source_id)` index → drop `company_id` column. Nothing else.

### 3. R1–R7 adapted verdicts (executor must quote one PASS/FAIL line each)
- R1 no-destroy: no `DropTable`, no `DropColumn` on `id`/`journal_entry_id`/`source_type`/`source_id`/`xmin` — FAIL on any of these (destructive op on existing data columns).
- R2 no-Cascade: `ReferentialAction.Restrict` count exactly 2, `Cascade`/`SetNull` count 0 — FAIL otherwise (SetNull precedent exists ONLY for optional dimension FKs on `JournalEntryLine`, `AccountingFoundation.cs:350-366` — PostingReference FKs are required, Restrict only).
- R3 unique present: `IsUnique` triple `(company_id, source_type, source_id)` exactly once; old non-unique pair dropped — FAIL if triple missing, non-unique kept without replacement, or global `(source_type, source_id)` unique without CompanyId.
- R4 correct names: table `posting_references`, columns `company_id/journal_entry_id/source_type/source_id/xmin` snake_case; FK names `FK_posting_references_*` — FAIL on camelCase (`CompanyId`) or misnamed FK.
- R5 widths preserved: `source_type character varying(100)`, no `HasMaxLength(20)` (Code-20 misapplication), no length on bigint IDs — FAIL otherwise.
- R6 xmin preserved: `xmin xid rowversion` untouched — FAIL if dropped/converted/moved.
- R7 Down reverses: `Down()` drops exactly what `Up()` added, restores old index — FAIL if lossy (drops unrelated objects) or no-op.

### 4. Data-loss risk — non-nullable company_id on a table WITH existing rows (explicit)
- EF renders non-nullable `AddColumn` with `defaultValue: 0L` (precedent `AccountingFoundation.cs:38,86,107` — "existing rows get 0, must be backfilled in production" per global MEMORY G3 batch note). `0` matches no real `companies.id` (identity starts at 1), so:
  - (a) If the migration ALSO creates the `FK_posting_references_companies_company_id` in the same `Up()`, existing rows carrying `company_id = 0` VIOLATE the FK at migrate time → **runtime migration failure on any database that already has posting_references rows**. Executor must flag this in the report: scaffold PASS on SQL shape does NOT mean safe to apply; production needs a backfill (update existing rows to real company ids) before/within the same deployment.
  - (b) The safe alternative (nullable `company_id` + backfill + later alter to non-nullable) is NOT what the current config renders (CLR `long` non-nullable → `nullable: false`). Executor must NOT hand-edit the scaffold to nullable inside G4 — report the risk, leave the DDL as scaffolded, defer the backfill strategy to a follow-up task (Design §9 item 7 declares backfill out of loop scope).
- Verifier: PASS = risk stated explicitly in executor report + `Up()` shape matches §2; FAIL = risk unmentioned, or executor silently edited scaffold nullability, or `database update` run to "prove" it works.

### 5. CHECK ONLY — forbidden ops
- FORBIDDEN without explicit approval: `dotnet ef database update` (any args), `database drop`, any `psql` write/DDL. Scaffold + `dotnet ef migrations script` render offline only (PaymentMethod G3 check-only precedent).
- G4 diff must contain ONLY the 3 scaffolded files (`<Timestamp>_PostingReferenceHarden.cs` + Designer + snapshot edit). Any `src/`/`tests/` hand-edit inside G4 = scope leak, FAIL.
