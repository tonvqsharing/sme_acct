# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings

### T1: Voucher Type Domain + Infrastructure (Sep 2026)
- VoucherCategory enum placed in `Domain/ValueObjects/` (not `Domain/Enums/`) to match existing convention — all 7 enums now live there
- VoucherType entity follows Department/CostCenter/Project pattern exactly: CompanyId + Code + Name + IsActive + DomainException invariants
- `Deactivate()` method does NOT raise a domain event (matches plan; can add `VoucherTypeDeactivated` later if Application layer needs it)
- VoucherCategory stored as string via `HasConversion<string>()` — same as all other enums in the codebase
- Unique index on `(CompanyId, Code)` enforces per-company code uniqueness at DB level
- Repository pattern: tracked queries for GetById/GetByCode, `AsNoTracking()` for GetAll — consistent across all 9 repos
- 14 entities total now, 14 DbSets, 13 ignored domain events

### T1 Consolidated Learnings — Reusable Patterns
- **New entity template (6 files):** Entity + Enum + Event + Port + EF Config + Repository — all in `Domain/ValueObjects/`, `Domain/Entities/`, `Domain/Events/`, `Domain/Ports/`, `Infrastructure/Persistence/Configurations/`, `Infrastructure/Repositories/`
- **DbContext add:** DbSet property + `modelBuilder.Ignore<NewEvent>()` — two edits, same file
- **DI add:** `services.AddScoped<INewRepo, EfNewRepo>()` — one line in DependencyInjection.cs
- **Invariant validation:** `DomainException` for all new entities (not `ArgumentNullException` — that's legacy Account/Company pattern)
- **Event minimalism:** Entity ID + CompanyId + occurredOn — nothing else
- **Deactivate() pattern:** No domain event — matches plan; can add `XxxDeactivated` later if Application layer needs it
- **Id=0 in constructor:** Known pattern — real ID assigned by EF Core after SaveChanges; events carry provisional 0
- **No navigation properties on CompanyId FK:** `HasOne<Company>().WithMany()` — no nav on entity, no nav on Company
- **Code max length 20, Name 200, Description 500:** Domain has no constraints; EF config enforces via HasMaxLength
- **All 22 architecture tests pass** when entity follows established patterns — no test changes needed

### T4: Posting Configuration Domain + Infrastructure (Sep 2026)
- **No domain event:** PostingConfiguration does NOT raise a domain event — same pattern as DocumentNumberingSeries (T2). No event file, no `modelBuilder.Ignore<>()` needed
- **Five FKs — most in codebase:** Company (Restrict), VoucherType (Restrict), Account as DebitAccount (Restrict), Account as CreditAccount (Restrict), TransactionReason (nullable, Restrict)
- **Two Account FKs need explicit HasForeignKey:** `HasForeignKey(e => e.DebitAccountId)` and `HasForeignKey(e => e.CreditAccountId)` — without explicit FK, EF Core throws ambiguous relationship error
- **DebitAccountId != CreditAccountId domain invariant:** Core accounting rule enforced in constructor via DomainException
- **"Both accounts same company" is Application-level only:** Entity only has account IDs (longs), cannot validate account ownership — Application layer (Task 6) must load accounts and verify CompanyId match
- **Nullable TransactionReasonId:** null means "default posting rule for this voucher type." Constructor validates > 0 only when non-null
- **Non-unique composite index:** `(VoucherTypeId, TransactionReasonId)` for query performance — no `.IsUnique()`, unlike Department/VoucherType/TransactionReason
- **OrderBy DisplayOrder:** Both GetAll methods sort by DisplayOrder, not Code (entity has no Code property)
- **GetAllByVoucherTypeAsync scoped by companyId:** Two filter params (voucherTypeId, companyId) — different from TransactionReason's single-param version
- **17 DbSets, 14 ignored events** after T4

### T2: Document Numbering Series Domain + Infrastructure (Sep 2026)
- **No domain event:** DocumentNumberingSeries constructor does NOT raise a domain event — intentional per plan. No event file, no `modelBuilder.Ignore<>()` needed in DbContext
- **Dual FK pattern:** Two FKs (CompanyId + VoucherTypeId) both use `HasOne<X>().WithMany().HasForeignKey().OnDelete(Restrict)` — no navigation properties on entity
- **Three-column unique index:** `(VoucherTypeId, CompanyId, Prefix)` — different from Department/VoucherType two-column `(CompanyId, Code)` pattern
- **No Code property:** Uses `Prefix` instead. Repo has `GetDefaultAsync(voucherTypeId, companyId)` not `GetByCodeAsync`. `GetAllByCompanyAsync` scoped by CompanyId not `GetAllAsync()`
- **Domain methods:** `Increment()` advances NextNumber by 1, `Reset(startFrom)` resets it — both validate invariants with `DomainException`
- **DbSet naming:** `DocumentNumberingSeries` (singular) — must be consistent with table name `document_numbering_series` (snake_case plural via `ToTable()`)
- **16 entities total now, 15 ports**

### T5: Opening Balance Mapping Domain + Infrastructure (Sep 2026)
- **No domain event:** OpeningBalanceMapping does NOT raise a domain event — same pattern as PostingConfiguration (T4) and DocumentNumberingSeries (T2)
- **Simplified PostingConfiguration:** 6 properties (CompanyId, VoucherTypeId, DebitAccountId, CreditAccountId, IsActive, Description) — no DisplayOrder, no TransactionReasonId
- **Dual Account FK pattern:** Same as PostingConfiguration — `HasOne<Account>().WithMany().HasForeignKey(e => e.DebitAccountId)` and `HasForeignKey(e => e.CreditAccountId)` — explicit FK naming required
- **Four-column UNIQUE index:** `(CompanyId, VoucherTypeId, DebitAccountId, CreditAccountId)` — widest unique index in codebase, prevents duplicate mappings
- **DebitAccountId != CreditAccountId invariant:** Same core accounting rule as PostingConfiguration, enforced via DomainException
- **3-method port:** Only GetByIdAsync, GetAllByCompanyAsync, AddAsync — fewer than PostingConfiguration (no voucher-type-scoped query)
- **GetAllByCompanyAsync sorted by VoucherTypeId then DebitAccountId:** No DisplayOrder, natural sort key
- **18 DbSets, 14 ignored events** after T5
- **Architecture tests:** 22/22 pass — entity follows established patterns

### T6: Application Layer — Commands + Queries for All 5 Slices (Sep 2026)
- **40 new files created:** 5 DTOs + 10 commands + 10 queries + 5 validators + 10 handlers (in new `Handlers/` directory)
- **No existing files modified:** DI already has assembly scan (`AddMediatR` + `AddValidatorsFromAssembly`), auto-discovers new handlers and validators
- **Handler pattern:** `internal sealed class` with primary constructor injection of port interfaces + IUnitOfWork. Create handlers: new entity → repo.AddAsync → unitOfWork.SaveChangesAsync → return result. Deactivate/Reset: repo.GetByIdAsync → entity.Deactivate()/Reset() → SaveChangesAsync → return empty result. Query handlers: repo.GetByIdAsync → map to DTO → return.
- **Deactivate/Reset result records are parameterless:** `DeactivateVoucherTypeResult`, `ResetNumberingSeriesResult`, etc. have no properties — unlike `DeprecateAccountResult(long AccountId)` which echoes the ID
- **DeactivateTransactionReasonCommand uses `ReasonId`:** Not `TransactionReasonId` — follow plan exactly
- **DeactivatePostingConfigurationCommand uses `ConfigId`:** Not `PostingConfigurationId`
- **DeactivateOpeningBalanceMappingCommand uses `MappingId`:** Not `OpeningBalanceMappingId`
- **PostingConfiguration has no DisplayOrder in create command:** Entity defaults to 0. Command omits DisplayOrder per plan
- **GetVoucherTypesByCompanyHandler filters in memory:** `IVoucherTypeRepository.GetAllAsync()` returns all companies — handler applies `.Where(e => e.CompanyId == request.CompanyId)`. All other repos have company-scoped methods
- **Enum-to-string in DTOs:** `entity.VoucherCategory.ToString()` — matches existing AccountDto pattern
- **20 handlers total for 20 request types:** 10 commands + 10 queries = 20 handlers. Existing Phase 1 commands/queries (12 total) have NO handlers — out of scope for T6
- **Build:** 0 warnings, 0 errors. **Architecture tests:** 22/22 pass
