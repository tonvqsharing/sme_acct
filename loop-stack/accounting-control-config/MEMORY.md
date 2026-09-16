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
