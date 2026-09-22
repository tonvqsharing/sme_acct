# PostingReference Hardening — Design (Option A Locked)

**Status:** LOCKED — 2026-09-22
**Scope:** Design only. No code changes in this task.
**Loop:** `loop-stack/posting-reference-harden/` — task [G1]
**Sources:** `loop-stack/posting-reference-harden/RESEARCH.md` (Context §§1–6, Task-Specific §[G1] decision + verification criteria); all file:line refs absolute under `/home/projects/sme_acct/`.

## 1. Decision

**Option A — FK to JournalEntry + keep SourceType/SourceId as origin trace — LOCKED.**

- Add `HasOne<JournalEntry>().WithMany().HasForeignKey(JournalEntryId).OnDelete(Restrict)` to the PostingReference EF configuration plus migration; keep free-string `SourceType`/`SourceId` columns as origin-trace payload.
- Add direct `CompanyId` on `posting_references` (`HasOne<Company> Restrict`, copied from `src/SmeAccounting.Infrastructure/Persistence/Configurations/FiscalYearConfiguration.cs:38-41`), populated from the source aggregate's `CompanyId` (e.g. `OpeningBalancePeriod.CompanyId`) at creation time — NOT derived via joins.
- Replace the non-unique `(SourceType, SourceId)` index with **unique `(CompanyId, SourceType, SourceId)`** (company-scoped idempotency).
- `posting_references` is **canonical** for idempotency + audit. `JournalEntry.SourceType/SourceId` (`src/SmeAccounting.Domain/Entities/JournalEntry.cs:13-14`) stay as **origin-trace cache (read model) only**, written atomically in the same UoW/handler that persists the JE.
- Rejected: Option B (validation-only, status-quo shape — leaves `journal_entry_id` dangling, zero orphan protection). Deferred: Option C (typed nullable FK per source — buys exactly 1 column today, future source count UNKNOWN; revisit only when a 2nd posting module is evidenced in source).

## 2. Evidence table

| # | Claim | Evidence |
|---|-------|----------|
| E1 | Exactly 1 live SourceType | Sole non-migration literal `"OpeningBalance"` at `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs:78` (`journalEntry.SetSource("OpeningBalance", Id)`). `grep SetSource src` = definition (`src/SmeAccounting.Domain/Entities/JournalEntry.cs:32`) + this 1 caller. No other producer exists. |
| E2 | Dead null/null command path | `src/SmeAccounting.Application/Commands/CreateJournalEntryCommand.cs:10-11` carries optional `SourceType`/`SourceId`, but `src/SmeAccounting.Api/Controllers/JournalEntryController.cs:39-41` hardcodes `null, null`; no `CreateJournalEntry*Handler` exists (Application grep 0 hits); `src/SmeAccounting.Application/Validators/CreateJournalEntryCommandValidator.cs:1-22` has zero source rules. Command source path is dead end-to-end. |
| E3 | CompanyId chain unenforced at 2 hops | `src/SmeAccounting.Domain/Entities/JournalEntry.cs:7-17` has no `CompanyId`; `src/SmeAccounting.Infrastructure/Persistence/Configurations/JournalEntryConfiguration.cs:26-27,50` maps bare `period_id` + non-unique index, zero `HasOne`. `src/SmeAccounting.Infrastructure/Persistence/Configurations/FiscalPeriodConfiguration.cs:19-20,45` maps bare `year_id` + non-unique index, zero `HasOne`. Only hop 3 enforced: `FiscalYearConfiguration.cs:38-41` `HasOne<Company> Restrict`. Domain ctors validate neither `periodId` (`JournalEntry.cs:24-30`) nor `yearId` (FiscalPeriod ctor). Deriving tenant from the chain is convention-only — hence direct `CompanyId` on `posting_references`. |
| E4 | No reversal / correction fields | `grep -rni 'revers\|correction\|void' src --include=*.cs` = 0 entity-field hits. `JournalEntry.cs:55-67` has only `Post()` + `IsPosted` guard; `JournalEntryConfiguration.cs:1-57` confirms no reversal columns. |
| E5 | No idempotency guard anywhere | `src/SmeAccounting.Infrastructure/Persistence/Configurations/PostingReferenceConfiguration.cs:29-30` both indexes non-unique; `src/SmeAccounting.Infrastructure/Migrations/20260916051341_InitialCreate.cs:205-208` same; `journal_entries` has no source index (`JournalEntryConfiguration.cs:50-51`). In-memory `IsPosted`/`Status` guards (`OpeningBalancePeriod.cs:61-65`) are the only dedup — insufficient under concurrency. |
| E6 | Transient-Id hazard | `OpeningBalancePeriod.cs:78` passes pre-save `Id` (0 per transient-Id=0 pattern) as `SourceId`; any persisted source id is unreliable until save completes. Reference row creation timing (§7) reconciles this with `> 0` guards. |
| E7 | Discarded-JE handler bug (out of scope, blocks end-to-end value) | `src/SmeAccounting.Application/Handlers/PostOpeningBalancesHandler.cs:16-21` calls `period.PostOpeningBalances(...)` (which news up a `JournalEntry` inside `OpeningBalancePeriod.cs:77-85`) then `SaveChangesAsync` with no repository `Add` of that JE — the JE is discarded, only period flags persist. Fixed in a separate task, not this loop. |
| E8 | Column widths from InitialCreate (normative) | `InitialCreate.cs:94-108`: `posting_references (id bigint identity PK, journal_entry_id bigint NOT NULL, source_type varchar(100) NOT NULL, source_id bigint NOT NULL, xmin xid rowversion)`, PK only, no FK. Indexes `:200-208`: `IX_posting_references_journal_entry_id` non-unique + `IX_posting_references_source_type_source_id` non-unique. `InitialCreate.cs:82-83`: `journal_entries.source_type varchar(100) NULL, source_id bigint NULL` — same varchar(100) width. `PostingReferenceConfiguration.cs:18-30`: `source_type` Required max100; `JournalEntryConfiguration.cs:33-38`: `source_type` max100 nullable. **SourceType max length is 100, NOT 20.** Code=20 applies only to master-data `Code` props (`VoucherTypeConfiguration.cs:21-24`, `TransactionReasonConfiguration.cs:24-27`). SourceId is `long`/`bigint` — no length concept. |
| E9 | No regulatory mandate on shape | `docs/architecture/ADR-010-tax-foundation-regulatory-traceability.md:1-148` contains zero `PostingReference`/`SourceType`/`SourceId` mentions; tax snapshot (`ADR-010:102-108`) is self-contained. `docs/` search returns only gap inventories + `docs/PaymentMethod-Design-2026.md:79,136,158` (PaymentMethod-loop-local "free-text suffices" decision, not a hardening constraint). No VAS / Circular 99 article prescribes reference shape. |

## 3. Field table (EF column spec — normative)

Table `posting_references`, snake_case columns. Widths keep InitialCreate values; only nullability/relationships/indexes change.

| Property | Column | Type / constraint | Notes |
|----------|--------|-------------------|-------|
| `Id` | `id` | `bigint` identity PK (`HasKey`, `ValueGeneratedOnAdd`) | Unchanged. |
| `CompanyId` | `company_id` | `bigint` NOT NULL, FK → `companies` Restrict | **New.** Direct tenant scope; populated from source aggregate's `CompanyId` at creation. Bare `bigint`, no max length (copies `FiscalYearConfiguration.cs:19-20`). No `Company` navigation property on entity (FK-nav-free pattern). |
| `JournalEntryId` | `journal_entry_id` | `bigint` NOT NULL, FK → `journal_entries` Restrict | Bare `bigint`, no max length. Relationship in config only: `HasOne<JournalEntry>().WithMany().HasForeignKey(e => e.JournalEntryId).OnDelete(Restrict)`. No navigation property on entity. |
| `SourceType` | `source_type` | `varchar(100)` NOT NULL, `IsRequired().HasMaxLength(100)` | **Width unchanged (100).** Free string + `DomainException` empty/whitespace guard only; not enum-ized. Matches `journal_entries.source_type` width. |
| `SourceId` | `source_id` | `bigint` NOT NULL | Bare `bigint`, no max length. Origin-trace id; `> 0` guard with post-JE-persist creation timing (§7). |
| `xmin` | `xmin` | `uint` rowversion (`IsRowVersion()`) | `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")` as LAST statement in `Configure`. |

Entity rules: `internal` EF config `PostingReferenceConfiguration : IEntityTypeConfiguration<PostingReference>`; entity in `src/SmeAccounting.Domain/Entities/PostingReference.cs` with private parameterless ctor (EF) + public ctor `(companyId, journalEntryId, sourceType, sourceId)` + `AddDomainEvent` in ctor; no navigation properties.

## 4. Domain event

`src/SmeAccounting.Domain/Events/PostingReferenceCreated.cs` (copies `VoucherTypeCreated` shape, renamed ids):

```csharp
public class PostingReferenceCreated : DomainEvent
{
    public long PostingReferenceId { get; }
    public long CompanyId { get; }
    public PostingReferenceCreated(long postingReferenceId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        PostingReferenceId = postingReferenceId;
        CompanyId = companyId;
    }
}
```

- Minimal payload: Id + CompanyId + timestamp only. NO `SourceType`/`SourceId`/`JournalEntryId` duplication (event-minimalism standard).
- Raised in entity ctor: `AddDomainEvent(new PostingReferenceCreated(Id, companyId, DateTimeOffset.UtcNow))` (copies `VoucherType.cs:33`, `TransactionReason.cs:34`). Provisional Id=0 at construction acknowledged (transient-Id pattern).
- Wiring: `modelBuilder.Ignore<PostingReferenceCreated>()` in `SmeAccountingDbContext.cs` (no table mapping).

## 5. Validation matrix (DomainException — never ArgumentNullException)

Replaces the legacy `sourceType ?? throw ArgumentNullException` at `PostingReference.cs:14` per the T1-invariant pattern.

| # | Guard | Exception | Message |
|---|-------|-----------|---------|
| V1 | `companyId <= 0` | `DomainException` | `CompanyId must be greater than zero.` (copies `VoucherType.cs:20-21`) |
| V2 | `journalEntryId <= 0` | `DomainException` | `JournalEntryId must be greater than zero.` (copies `TransactionReason.cs:21-22` VoucherTypeId guard) |
| V3 | `string.IsNullOrWhiteSpace(sourceType)` | `DomainException` | `SourceType is required.` |
| V4 | `sourceId <= 0` | `DomainException` | `SourceId must be greater than zero.` |

`JournalEntry.SetSource` hardening (stays a setter, no FK semantics): non-empty-type guard + `sourceId > 0` guard + reject-change-once-posted guard, all `DomainException`. No `ArgumentNullException` anywhere in the hardened path.

## 6. Persistence constraints (EF configuration — normative)

1. Table `posting_references`, snake_case columns (`id, company_id, journal_entry_id, source_type, source_id, xmin`).
2. Exactly two relationships, both `OnDelete(DeleteBehavior.Restrict)` (copies `FiscalYearConfiguration.cs:38-41` / `TransactionReasonConfiguration.cs:44-52` two-FK precedent; never `Cascade`/`SetNull` on financial data):
   - `builder.HasOne<JournalEntry>().WithMany().HasForeignKey(e => e.JournalEntryId).OnDelete(DeleteBehavior.Restrict);`
   - `builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);`
3. Indexes: `builder.HasIndex(e => new { e.CompanyId, e.SourceType, e.SourceId }).IsUnique()` **replacing** the current non-unique `(SourceType, SourceId)` index (`PostingReferenceConfiguration.cs:30`); keep non-unique `HasIndex(e => e.JournalEntryId)` (`:29`) for JE→reference lookup.
4. Column mapping: `source_type IsRequired().HasMaxLength(100)`; `company_id`/`journal_entry_id`/`source_id` bare `bigint`; no `HasMaxLength` on long IDs; no camelCase columns.
5. `xmin` rowversion LAST statement in `Configure` (copies `VoucherTypeConfiguration.cs:50-52`, `FiscalYearConfiguration.cs:43-45`).
6. Migration `PostingReferenceHarden`: (a) `AddColumn company_id bigint NOT NULL`; (b) two `AddForeignKey` Restrict (→ `journal_entries`, → `companies`); (c) unique index swap per (3); (d) keep JE index; (e) snake_case + `xmin` unchanged. No new tables, no per-source columns, no check constraints. Rollback = drop FKs/indexes/column.

## 7. Idempotency semantics

- `posting_references` is canonical (idempotency + audit); `JournalEntry.SourceType/SourceId` are read-model cache only.
- Both written atomically in the same UoW/handler that persists the JE (closes dual-write drift; Context: currently no sync).
- Creation timing: reference row created post-JE-persist when the JE id is assigned — reconciles `journalEntryId > 0` / `sourceId > 0` guards with the transient-Id=0 pattern (`OpeningBalancePeriod.cs:78` passes pre-save 0).
- Duplicate post → unique-violation conflict surfaced (not silent overwrite). App pre-check `GetBySourceAsync(sourceType, sourceId, companyId)` + `ValidationBehavior` fast-path only; the unique index is the backstop (in-memory `IsPosted`/`Status` guards insufficient under concurrency).
- FK alone does not deduplicate — the unique index is required.

## 8. File placement (downstream tasks)

| Artifact | Path |
|----------|------|
| Entity | `src/SmeAccounting.Domain/Entities/PostingReference.cs` |
| Event | `src/SmeAccounting.Domain/Events/PostingReferenceCreated.cs` |
| Port | `src/SmeAccounting.Domain/Ports/IPostingReferenceRepository.cs` (required under Option A; exposes `GetBySourceAsync(sourceType, sourceId, companyId)` + standard `GetByIdAsync`/`AddAsync`) |
| EF config | `src/SmeAccounting.Infrastructure/Persistence/Configurations/PostingReferenceConfiguration.cs` (`internal sealed : IEntityTypeConfiguration<PostingReference>`) |
| Repository | `src/SmeAccounting.Infrastructure/Repositories/EfPostingReferenceRepository.cs` |
| Wiring | `DbSet<PostingReference>` + `modelBuilder.Ignore<PostingReferenceCreated>()` in `SmeAccountingDbContext.cs`; `AddScoped<IPostingReferenceRepository, EfPostingReferenceRepository>()` in `DependencyInjection.cs` |

## 9. Out of scope (each excluded with reason)

1. **Reversal/correction/void linkage** (`ReversedById`, status enum) — excluded: zero evidence (`grep revers|correction|void src` = 0 entity-field hits; `JournalEntry.cs:55-67` Post-only).
2. **`JE→Period→Year` chain FK enforcement** (`JournalEntry.PeriodId`, `FiscalPeriod.YearId` real FKs) — excluded: separate migration; direct `CompanyId` chosen precisely to avoid chain trust (two unenforced hops, E3).
3. **`PostOpeningBalancesHandler.cs:16-21` discarded-JE bug fix** — excluded: separate task; blocks end-to-end value of any option.
4. **Dead null/null command path** (`CreateJournalEntryCommand.cs:10-11` optional source + `JournalEntryController.cs:39-41` hardcoded nulls, no handler exists) — excluded: no handler to wire; not resurrected in this loop.
5. **Enum-izing SourceType / wiring VoucherType/VoucherCategory** — excluded: no source links them; keep free string max100 + empty/whitespace guard only.
6. **Tax snapshot / ADR-010 traceability changes** — excluded: snapshot self-contained (`ADR-010:102-108`), zero PostingReference refs.
7. **Backfill of historical `SourceId=0` transient rows + `company_id` default-0 backfill plan detail** — excluded as data-migration concern, not schema concern (migration adds non-null `company_id`; deployment backfill out of loop scope).
8. **`IsActive`/soft-delete / effective-dating on PostingReference** — excluded: audit rows append-only; no Deactivate/event beyond minimal Created.

## 10. Non-goals

- No Application CQRS, repository implementation, controller, migration scaffolding, or test code in this task (downstream tasks G2–G4 own them).
- No change to `JournalEntry.SourceType/SourceId` column widths or nullability (nullable `varchar(100)` cache stays).
- No new tables, enums, check constraints, or per-source FK columns.
- No VAS / Circular 99 compliance claim beyond E9 (silent — structure is an integrity decision, not a regulatory mandate).
