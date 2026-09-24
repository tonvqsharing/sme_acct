# Research Log — Module 03 Inventory & Items

## Context & Prior Work

### Critical finding: 8 of 16 requested components ALREADY EXIST

The `product-inventory-foundation` loop (closed 2026-09-23, code committed) already built the core of Module 03: **Item, ItemCategory, Uom, UomConversion, Warehouse, InventoryValuationPolicy, InventoryAccountingConfiguration, InventoryAdjustmentReason** — each with full 5-layer vertical slice (Domain entity + event + port, EF config, repository, flat CQRS + FluentValidation + DTO, thin MediatR controller) and a migration. The `business-partners` loop (closed 2026-09-24, **code UNCOMMITTED — still in working tree**) added SupplierItem (link entity referencing Item). **The remaining work is 8 genuinely missing components, not 16.**

### Inventory-status CLASSIFICATION TABLE (16 components from PLAN.md)

| # | Component | Status | Evidence (exact paths) |
|---|-----------|--------|------------------------|
| 1 | Item | **EXISTS** | `src/SmeAccounting.Domain/Entities/Item.cs`; `ItemConfiguration.cs`; `EfItemRepository.cs`; `IItemRepository.cs`; `CreateItemCommand.cs`/`CreateItemHandler.cs`/`GetItemQuery.cs`(+GetItemsByCompanyQuery co-located)/`ItemDto.cs`/`CreateItemCommandValidator.cs`; `Api/Controllers/ItemController.cs`; table `items` (migration `20260921022726_AddItemAndServiceItem`). Fields: CompanyId, Code(20), Name(200), ItemCategoryId?, UomId?, IsStockItem, IsServiceItem, IsActive, Description(500). Unique (CompanyId,Code); 3 Restrict FKs. **No TaxTypeId, no DefaultWarehouseId** (research doc proposed them; not implemented). |
| 2 | ItemCategory | **EXISTS** | `Entities/ItemCategory.cs` (self-ref `ParentId`); `ItemCategoryConfiguration.cs` (self-FK Restrict); `EfItemCategoryRepository.cs`; full CQRS + `ItemCategoryController.cs`; table `item_categories` (`20260921020615_AddItemCategory`). |
| 3 | ItemGroup | **MISSING** | Zero hits for `ItemGroup`/`item_group` in src/, tests/, docs/, migrations. No entity, no table. |
| 4 | ItemBarcode / GTIN | **MISSING** | Zero hits for `Barcode`/`GTIN` anywhere. No entity, no table. |
| 5 | ItemPriceList / PriceList | **MISSING** | Zero hits for `PriceList`/`ItemPrice`. No entity, no table. `Money` VO exists (`Domain/ValueObjects/Money.cs`, `string Currency`) as the price-typing building block. |
| 6 | ItemReorderLevel | **MISSING** | Zero hits for `ReorderLevel`. No entity, no table. |
| 7 | ItemSupplierPrice | **PARTIAL** | `SupplierItem` link entity EXISTS: `Entities/SupplierItem.cs` = (CompanyId, SupplierId, ItemId, IsActive) — **pure link, NO price/cost fields**. Table `supplier_items` (`20260924003244_AddPartnerGroupsAndSupplierItems`, APPLIED to live DB), partial unique index `(company_id, supplier_id, item_id) WHERE is_active` (first `HasFilter` in codebase). A price-bearing ItemSupplierPrice entity is MISSING. |
| 8 | ItemTaxClass | **MISSING** | No entity. `Item` has **no TaxTypeId FK**. Integration targets exist: `TaxType` (`Entities/TaxType.cs`, TaxCategory enum), `TaxRate` (effective-dated), both from phase3-tax-foundation. |
| 9 | Uom | **EXISTS** | `Entities/Uom.cs` (Code/Name/Symbol/IsActive/Description); `UomConfiguration.cs`; full CQRS + `UomController.cs`; table `uoms` (`20260917111153_AddUom`). |
| 10 | UomConversion | **EXISTS** | `Entities/UomConversion.cs` (FromUomId, ToUomId, Factor; invariants: from≠to, factor>0); `UomConversionConfiguration.cs`; full CQRS + `UomConversionController.cs`; table `uom_conversions` (`20260921021609_AddUomConversion`). Unique (CompanyId, FromUomId, ToUomId). |
| 11 | UomClass | **MISSING** | Zero hits. No entity, no table. |
| 12 | Warehouse | **EXISTS** | `Entities/Warehouse.cs` (Code/Name/Address?/IsActive/Description); `WarehouseConfiguration.cs`; full CQRS + `WarehouseController.cs`; table `warehouses` (`20260921020956_AddWarehouse`). |
| 13 | WarehouseLocation / Bin | **MISSING** | Zero hits. No entity, no table. Warehouse exists as FK target. |
| 14 | InventoryValuationPolicy | **EXISTS** | `Entities/InventoryValuationPolicy.cs` + `ValuationMethod` enum (FIFO/LIFO/WeightedAverage — matches VAS 02); `InventoryValuationPolicyConfiguration.cs`; full CQRS + controller; table `inventory_valuation_policies` (`20260921024242_AddInventoryValuationPolicyAndAdjustmentReason`). |
| 15 | InventoryAccountingConfiguration | **EXISTS** | `Entities/InventoryAccountingConfiguration.cs` = (CompanyId, InventoryAccountId, CogsAccountId, InventoryAdjustmentGainAccountId?, InventoryAdjustmentLossAccountId?); 4 Account FKs all Restrict; **unique index on CompanyId (1:1 per company)**; table `inventory_accounting_configurations` (`20260921025725_AddInventoryAccountingConfiguration`). No Code/Name/ValuationPolicyId (research doc proposed them; not implemented). |
| 16 | InventoryAdjustmentReason | **EXISTS** | `Entities/InventoryAdjustmentReason.cs`; full CQRS + controller; table `inventory_adjustment_reasons` (`20260921024242`). |

**Summary: 8 EXISTS (no work needed unless new components force FK additions to Item), 1 PARTIAL (SupplierItem — link only, no price), 7 MISSING (ItemGroup, ItemBarcode/GTIN, PriceList, ItemReorderLevel, ItemSupplierPrice, ItemTaxClass, UomClass, WarehouseLocation/Bin).**

### Prior loops — direct relevance

| Loop | Relevance | What it built |
|------|-----------|---------------|
| `product-inventory-foundation_DONE` | **DIRECT — built 8/16 components** | Uom, ItemCategory, Warehouse, UomConversion, Item, ServiceItem, InventoryValuationPolicy, InventoryAdjustmentReason, InventoryAccountingConfiguration. REPORT.md + MEMORY.md confirm all VERIFIED. Its RESEARCH.md design doc is **aspirational** — actual entities are simpler (e.g., Item lacks proposed TaxTypeId/DefaultWarehouseId; InventoryAccountingConfiguration lacks proposed Code/Name/ValuationPolicyId). |
| `business-partners_DONE` | **DIRECT — SupplierItem (Item FK target), uncommitted** | CustomerGroup, SupplierGroup, SupplierItem full slices + Customer/Supplier nullable group FKs + migration `20260924003244` **APPLIED to live DB**. Git integration was deliberately OFF — **entire module is untracked/modified in working tree**. BankTests 115/115. |
| `phase3-tax-foundation_DONE` | ItemTaxClass integration target | TaxType (TaxCategory enum), TaxRate (effective-dated), TaxTreatment, TaxAuthority, TaxRule, TaxExemptionReason, TaxPeriod, TaxAccountingMapping. |
| `accounting-control-config_DONE` | Account-mapping precedent | VoucherType, DocumentNumberingSeries, PostingConfiguration, TransactionReason, OpeningBalanceMapping. |
| `phase4-business-partner_DONE` | Master-data conventions | Customer, Supplier, Employee, PaymentTerm; GetAllByCompanyAsync pattern. |
| `implement-gen-acct-02_DONE` | Bank hierarchy (parent/child shape) | Bank→BankBranch→BankAccount — the closest precedent for Warehouse→WarehouseLocation/Bin and Item→ItemBarcode child entities. BankTests minimal-test pattern. |
| `accounting-foundation-build_DONE` | Account/JournalEntry | Company, Currency, FiscalYear/FiscalPeriod, ExchangeRate, dimensions; FK-to-Company pattern. |
| `01-system-security_DONE`, `company-opening-user-mgmt_DONE` | Company/User/security | CompanySetting (1:1 per company — same shape as InventoryAccountingConfiguration), global User + CompanyMembership, Role. **No authorization on any controller** — auth not yet wired app-wide. |

### Current uncommitted WIP (business-partners — must be handled before/with this loop)

`git status` shows the entire business-partners module uncommitted: 3 new entities (CustomerGroup, SupplierGroup, SupplierItem) + events + ports + configs + repos + 3 controllers + 3 ViewModels + 18 Application files + 3 test files + migration `20260924003244_AddPartnerGroupsAndSupplierItems` + modified Customer.cs/Supplier.cs/CustomerConfiguration.cs/SupplierConfiguration.cs/DbContext/DI/Fakes.cs. **Build is GREEN with this WIP (0 warnings/0 errors), BankTests 115/115, arch 22/22.** The inventory loop's migration will be #19 on top of the current snapshot (which already includes AddPartnerGroupsAndSupplierItems). Open question for planner: commit the partners WIP first (it's a complete, verified module) or fold into inventory commits.

### Existing conventions summary (canonical, cross-loop verified)

- **IDs**: `long` identity, `ValueGeneratedOnAdd`, `BaseEntity.Id` has **public setter** (tests set Id directly). Transient Id=0 at construction; EF assigns on save.
- **Audit**: `xmin` row version on every table (`Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")`). No CreatedAt/UpdatedAt columns. Domain events raised in ctors (minimal: EntityId + CompanyId + OccurredOn), ignored in DbContext.
- **Soft delete**: `IsActive` bool, `Deactivate()` sets false, no hard delete, no Reactivate. Link entities use **partial unique index** `HasFilter("\"is_active\"")` (SupplierItem precedent) so deactivate→re-add works.
- **Company scope**: non-nullable `long CompanyId` on all master data; FK `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`; **no navigation property** on entities.
- **Validation**: `DomainException` hierarchy in entity ctors (CompanyId>0, Code/Name non-whitespace, cross-field invariants); FluentValidation in Application (English messages, `GreaterThan(0)`, `MaximumLength`); max lengths enforced in EF config only (Code=20, Name=200, Description=500).
- **Authorization**: NONE anywhere — controllers are thin MediatR dispatch, no `[Authorize]`. CompanyId passed as command/route param.
- **Migrations**: one per cohesive feature, descriptive name; build must pass before `dotnet ef migrations add`; check-only unless user approves `database update`; 18 migrations / 37 .cs files; latest `20260924003244` APPLIED to live DB `sme_acct_dev` (54 tables).
- **Seeding**: `docs/seed-system-security-defaults.md` documents company-scoped default masters (VoucherType/TransactionReason/NumberingSeries) — doc only, no seed code confirmed.
- **Tests**: BankTests 115/115 (72 pre-partners + 43 partners), ArchitectureTests 22/22, build 0/0. List-backed fakes in `tests/SmeAccounting.BankTests/Fakes.cs`; Deactivate-happy facts set `entity.Id = 5` before AddAsync; `InternalsVisibleTo("SmeAccounting.BankTests")` in Application.csproj.
- **DbContext**: DbSet for most entities; partners use **Ignore-only** (no DbSet) + `Set<T>()` in repo — both styles coexist. New event = one `modelBuilder.Ignore<...>()` line.
- **DI**: `AddScoped<IXxx, EfXxx>()` per repo in `Infrastructure/DependencyInjection.cs` (currently 50+ registrations).
- **CQRS**: flat Application layout (Commands/Queries/Handlers/Validators/DTOs — no feature folders except Bank), records implementing `IRequest<T>`, MediatR 14.x, `ValidationBehavior` pipeline, manual DTO mapping (no AutoMapper), CompanyId FIRST param in Create commands.
- **Controllers**: thin, MediatR dispatch only, zero `Domain.*` usings (arch-enforced), `RedirectToAction` on result Id, `[ValidateAntiForgeryToken]` on POSTs. Views exist only for ChartOfAccounts/FiscalPeriod/JournalEntry/Reporting/Settings — **master-data views skipped app-wide** (precedent).

### Dependency map (integration targets for the 7 missing components)

```
Item ──► ItemCategory (nullable FK, Restrict)          [EXISTS]
Item ──► Uom (nullable FK, Restrict)                   [EXISTS]
Item ──► Company (Restrict)                            [EXISTS]
SupplierItem ──► Supplier + Item (both Restrict)       [EXISTS — Item is FK target]
InventoryAccountingConfiguration ──► Account ×4 + Company (Restrict, 1:1 per company) [EXISTS]
UomConversion ──► Uom ×2 (Restrict)                    [EXISTS]
ItemCategory ──► ItemCategory (self-ref ParentId)      [EXISTS]
TaxType/TaxRate (phase3) ──► ItemTaxClass target       [MISSING component]
Warehouse ──► WarehouseLocation/Bin target             [MISSING component]
Money VO (string Currency) ──► PriceList/ItemPrice typing [MISSING component]
Account 156 (inventory) per VAS 02 ──► InventoryAccountingConfiguration [EXISTS]
JournalEntry/JournalEntryLine ──► future stock ledger (out of scope per PLAN)
```

### Regulatory anchor

- **VAS 02 (Hàng tồn kho, IAS 2)** — Core standard → Inventory module: FIFO/weighted-avg valuation, Account 156. `InventoryValuationPolicy.ValuationMethod` (FIFO/LIFO/WeightedAverage) already aligns. Traceability matrix in `loop-stack/vietnamese-acct-architecture_DONE/docs/regulatory/VAS-compliance.md` lists `InventoryTests` as Planned.
- Circular 99/2025/TT-BTC account mappings (1331/156/632 etc.) — InventoryAccountingConfiguration's Account FKs cover this.

## Existing Tools & Resources

- All tools from `loop-stack/.global/TOOLS.md` verified: dotnet 10.0.401, dotnet-ef 10.0.12, psql 18.4 client, PostgreSQL 16.14 reachable at 172.21.208.1. No codegraph index — use grep/glob/read.
- No new online resources needed — this is a codebase-convention-following task, fully answerable from existing code. (No entries added to Newly Discovered Resources.)

## Requirements & Constraints

- **Non-negotiables**: build 0 warnings/0 errors (TreatWarningsAsErrors), arch tests 22/22, BankTests stay green (115/115 baseline), Domain zero NuGet refs, controllers zero `Domain.*` usings, snake_case + xmin + FK Restrict + unique (CompanyId,Code) patterns, DomainException validation, soft delete only.
- **Scope guard (PLAN)**: master-data and configuration foundation ONLY — no warehouse transaction engine, purchasing, sales, or stock ledger. Existing 8 components likely need zero changes unless a new component requires an Item FK addition (e.g., ItemTaxClass → TaxTypeId on Item, or ItemReorderLevel → ItemId FK).
- **Migration**: will be #19; must be generated on top of current snapshot (includes uncommitted AddPartnerGroupsAndSupplierItems). Check-only unless user approves DB update.
- **Design decisions needed** (planner/executor): ItemGroup vs ItemCategory (duplicate-risk — ItemCategory already provides hierarchy); ItemSupplierPrice as new entity vs extending SupplierItem; ItemTaxClass as Item FK vs link entity; UomClass semantics; barcode uniqueness scope (per-company vs global GTIN); PriceList currency handling via Money VO.

### 1. Architecture test rules — the exact 22 NetArchTest constraints (all in `tests/SmeAccounting.ArchitectureTests/`)

Every implementation must satisfy ALL of these. Violation = build break (NetArchTest runs in test step, not build, but arch failure blocks PASS).

**DependencyRulesTests.cs (7):**
1. `Domain_Should_Not_Depend_On_Application` — Domain assembly has no dependency on `SmeAccounting.Application`
2. `Domain_Should_Not_Depend_On_Infrastructure` — Domain assembly has no dependency on `SmeAccounting.Infrastructure`
3. `Domain_Should_Not_Depend_On_Api` — Domain assembly has no dependency on `SmeAccounting.Api`
4. `Application_Should_Not_Depend_On_Infrastructure` — Application assembly has no dependency on `SmeAccounting.Infrastructure`
5. `Application_Should_Not_Depend_On_Api` — Application assembly has no dependency on `SmeAccounting.Api`
6. `Infrastructure_Should_Not_Depend_On_Api` — Infrastructure assembly has no dependency on `SmeAccounting.Api`
7. `Api_Controllers_Should_Not_Depend_On_Infrastructure` — types in `SmeAccounting.Api.Controllers` have no dependency on `SmeAccounting.Infrastructure` (only composition root may)

**DomainPurityTests.cs (3):**
8. `Domain_Should_Have_No_NuGet_PackageReferences` — Domain.csproj contains zero `<PackageReference>` elements
9. `Domain_Should_Not_Reference_Microsoft_Or_Npgsql_Packages` — no package whose Include starts with `Microsoft.`, `Npgsql.`, `Serilog.`, or `EFCore.`
10. `Domain_Should_Have_No_EntityFramework_Assembly_Dependency` — Domain types have no dependency on `Microsoft.EntityFrameworkCore`

**LayerCouplingTests.cs (4):**
11. `Controllers_Should_Not_Reference_Domain_Entities_Namespace` — controllers have no dependency on `SmeAccounting.Domain.Entities`
12. `Controllers_Should_Not_Reference_Domain_Ports_Namespace` — controllers have no dependency on `SmeAccounting.Domain.Ports`
13. `Application_Handlers_Should_Not_Reference_Infrastructure_Namespace` — types implementing `MediatR.IRequestHandler<,>` have no dependency on `SmeAccounting.Infrastructure`
14. `Infrastructure_Should_Not_Reference_Api_Namespace` — Infrastructure types have no dependency on `SmeAccounting.Api`

**NamingConventionsTests.cs (6):**
15. `Entities_Inheriting_BaseEntity_Should_Reside_In_Entities_Namespace` — every `BaseEntity` subclass lives in `SmeAccounting.Domain.Entities`
16. `Repository_Interfaces_Should_Start_With_I` — every interface named `*Repository` starts with `I`
17. `Commands_In_Commands_Namespace_Should_End_With_Command` — `IRequest<>` types in `SmeAccounting.Application.Commands` end with `Command`
18. `Queries_In_Queries_Namespace_Should_End_With_Query` — classes in `SmeAccounting.Application.Queries` end with `Query`
19. `DTOs_Should_End_With_Dto` — types in `SmeAccounting.Application.DTOs` end with `Dto`
20. `Controllers_Should_End_With_Controller` — classes in `SmeAccounting.Api.Controllers` end with `Controller`

**PostingRuleIsolationTests.cs (2):**
21. `IPostingService_Should_Reside_In_Domain_Assembly` — `IPostingService` lives in the Domain assembly
22. `JournalEntry_Balance_Rule_Should_Be_Enforceable_In_Domain` — `JournalEntry`, `Money`, `IPostingService` all live in the Domain assembly (posting rules enforceable in pure domain)

### 2. Coding constraints checklist (non-negotiable)

- **C# 13**, nullable enabled, implicit usings, `var` preferred
- **Private fields `_camelCase`** (enforced by .editorconfig — build fails on violation)
- **4-space indent, LF line endings**; 2-space for csproj/json/yaml
- **Records for DTOs and value objects** (e.g., `UomDto`, `CreateUomCommand`, `Money`)
- **FluentValidation auto-pipeline** via `ValidationBehavior` — validators auto-discovered (`AddValidatorsFromAssembly`); handler never validates manually
- **TreatWarningsAsErrors=true** — build must be 0 warnings / 0 errors. CS-series warnings (CS0162, CS8629, CS0219, CS0246, CS0535, CS8955, CS1056) are compile failures
- **Domain zero NuGet refs** (rules 8–10) — no EF, no MediatR, no FluentValidation in Domain
- **Controllers never reference `Domain.Entities` or `Domain.Ports`** (rules 11–12) — thin MediatR dispatch only
- **DomainException hierarchy** for invariant validation in entity ctors (never `ArgumentNullException`/`ArgumentOutOfRangeException`)
- **Private parameterless ctor** for EF materialization + public ctor with required params
- **No navigation properties** on entities — FK-only; `HasOne<Company>().WithMany()` in EF config
- **No AutoMapper** — manual DTO mapping in handlers
- **No `UpdateAsync` in repos** — change tracking persists mutations
- **Enums stored as string** via `HasConversion<string>()` in EF config; enum types live in `Domain/ValueObjects/` (no `Domain/Enums/` dir)
- **Max lengths in EF config only**: Code=20, Name=200, Description=500
- **CompanyId FIRST param** in Create commands (30/32 precedent)
- **Domain events minimal**: `{Entity}Created(EntityId, CompanyId, OccurredOn)` — never duplicate entity payload
- **xmin row version** on every entity (`Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")`)
- **snake_case** table/column naming (`EFCore.NamingConventions`)
- **decimal for money/quantity** — never float/double (Money VO uses `decimal` + `string Currency`)

### 3. Verification Criteria template (derived from the goal's 25-item Definition of Done)

The DoD checklist from the goal brief (reconstructed from PLAN.md goal + task enumeration — the 25 items below are the verifier's per-task gate). **Passing = ALL items green; any red = task fails.**

| # | DoD item | Verifier check |
|---|----------|----------------|
| 1 | Build warning-free | `dotnet build SmeAccounting.sln` → 0 warnings, 0 errors |
| 2 | Architecture tests pass | `dotnet test tests/SmeAccounting.ArchitectureTests/` → 22/22 |
| 3 | No test regression | `dotnet test tests/SmeAccounting.BankTests/` → ≥115/115 (new Facts for new entities) |
| 4 | Domain purity preserved | Domain.csproj unchanged — zero NuGet refs (rules 8–10) |
| 5 | Controllers thin | Zero `Domain.*` usings in new controllers (rules 11–12, 7) |
| 6 | Project identity preserved | sme_acct solution/project names/structure unchanged; no new projects, no parallel app |
| 7 | Conventions reused | Company scope, long IDs, snake_case, xmin, soft delete, DomainException, FluentValidation, thin controllers, flat CQRS — no invented alternatives |
| 8 | No duplicate concepts | ItemGroup reconciled with ItemCategory (not duplicated); no duplicate Supplier/Account/TaxType/UOM/Warehouse entities or tables |
| 9 | decimal for money/quantity | No float/double anywhere in new code; Money VO for prices |
| 10 | Company isolation | CompanyId FK Restrict on every new entity; unique (CompanyId, Code) (or partial-unique for link entities) |
| 11 | Historical integrity | No hard delete of referenced items; no silent overwrite of prices/tax/valuation — new versions/effective-dates instead |
| 12 | No valuation engine without stock ledger | No valuation/COGS computation logic in this module (master-data only) |
| 13 | TDD per slice | RED→GREEN evidence per slice: failing Facts recorded before implementation, green after |
| 14 | Evidence-based reporting | Verifier re-runs every gate independently (STATUS.md numbers are hypotheses, not facts); evidence quoted per task |
| 15 | Master-data + configuration only | No transaction engine, purchasing, sales, stock ledger code |
| 16 | No serial/lot tracking | Not implemented without explicit design |
| 17 | No PO generation | No purchase-order code |
| 18 | No forecasting | No demand/forecast code |
| 19 | Migration discipline | One migration per cohesive slice; check-only (never `database update` without user approval); no pre-existing migration modified; snake_case + xmin + Restrict FKs + unique indexes verified in Up(); Down() reverses exactly |
| 20 | DbContext + DI wiring | New event → one `modelBuilder.Ignore<...>()` line; new repo → one `AddScoped<IXxx, EfXxx>()` line |
| 21 | Entity checklist complete | Entity + Enum(if needed) + Event + Port + EF Config + Repository + Command/Query/Handler/Validator/DTO + Controller — all 5 layers per new entity |
| 22 | No placeholders/TODOs | Grep new files for TODO/placeholder — zero hits |
| 23 | Existing entities untouched | Item/ItemCategory/Uom/UomConversion/Warehouse/Inventory* parity preserved — no modification without stated reason (nullable-FK append allowed only with backwards-compatible ctor expansion, param LAST) |
| 24 | Commit hygiene | Commits stage ONLY inventory-loop files — business-partners WIP (58 untracked + 11 modified) never swept in; `git diff-tree --name-only -r <commit>` per commit |
| 25 | Migration baseline correct | New migration is #19 on top of current snapshot (18 migrations / 37 .cs on disk); count + latest-timestamp + zero-new-migration-file evidence for no-migration tasks |

### 4. Anti-scope-creep guardrails

- **Master data + configuration ONLY** — the module's ceiling. No warehouse transaction engine, purchasing module, sales module, or stock ledger unless discovery proves integration required (PLAN.md).
- **No PO generation, no forecasting, no serial/lot tracking** — explicitly out of scope; serial/lot only with a design first.
- **No valuation engine without stock ledger** — `ValuationMethod` enum (FIFO/LIFO/WeightedAverage) is configuration data, not computation. Do NOT implement valuation math.
- **No duplicate concepts** — the goal's #1 domain rule: ItemGroup vs ItemCategory must be RECONCILED (ItemCategory already provides self-ref hierarchy — ItemGroup must not duplicate it); no duplicate Supplier/Account/TaxType/UOM/Warehouse entities or tables. Reuse existing FK targets (TaxType from phase3, Supplier from business-partners, Account from foundation, Uom/Warehouse from product-inventory-foundation).
- **decimal, never float** — for money and quantity.
- **Company isolation** — every new entity company-scoped with FK Restrict; per-company uniqueness at DB level.
- **Historical integrity** — no hard delete of referenced items; no silent overwrite of prices/tax/valuation (effective-dating or new-version pattern, TaxRate precedent).
- **Existing 8 entities are parity-verify only** — zero changes unless a new component requires an Item FK addition (e.g., ItemTaxClass → TaxTypeId on Item), and then only via backwards-compatible nullable-FK append (param LAST, `HasValue && <= 0` guard, nullable AddColumn with NO defaultValue — zero backfill risk).
- **No new NuGet packages** — Domain zero; other projects unchanged unless a stated, justified need.
- **No new projects / no parallel app** — extend the existing 6-project solution.

### 5. Project identity preservation rules

- Keep `SmeAccounting.sln` (6 projects) and all project names: `SmeAccounting.Domain`, `SmeAccounting.Application`, `SmeAccounting.Infrastructure`, `SmeAccounting.Api`, `SmeAccounting.ArchitectureTests`, `SmeAccounting.BankTests`.
- No parallel app, no new solution, no renamed projects.
- Reuse established conventions for: company scope (CompanyId FK Restrict), IDs (long identity), DB naming (snake_case), audit fields (xmin), soft delete (IsActive + Deactivate()), validation (DomainException + FluentValidation), authorization (none app-wide — do not invent per-controller auth), migrations (check-only), error handling (ValidationException → ModelState in controllers), tests (BankTests List-backed fakes), UI/endpoints (thin MediatR controllers; master-data views skipped app-wide — precedent).
- New code goes into the existing 4 src projects + BankTests — never a new project.
- **Commit hygiene is part of identity preservation**: the working tree contains the complete uncommitted business-partners module (CustomerGroup/SupplierGroup/SupplierItem + migration `20260924003244`). Inventory commits must stage only their own files; the partners WIP must be committed separately (or explicitly folded) — never mixed into inventory commits.

## Suggested Approach

1. Planner: treat 8 EXIST as parity-verify (no-op or minimal), 1 PARTIAL (SupplierItem) as design-input, 7 MISSING as the real build. Group the 7 missing into cohesive slices by dependency: (a) Item extensions + ItemTaxClass + ItemBarcode/GTIN (Item-adjacent), (b) ItemGroup + UomClass (classification masters), (c) PriceList + ItemSupplierPrice (pricing), (d) ItemReorderLevel + WarehouseLocation/Bin (operations). One consolidated migration per slice, following the SupplierItem partial-unique-index and nullable-FK-append canons.
2. Executor: copy the exact 5-layer pattern from an existing inventory entity (Item/Uom are the cleanest templates), flat CQRS, thin controller, List-backed-fake tests in BankTests, build→arch→tests→migration order.
3. Resolve the uncommitted business-partners WIP first (commit it or explicitly fold it in) so the inventory loop's commits are clean.

## Verification Criteria

- **Passing**: build 0/0; arch 22/22; BankTests ≥115/115 (new Facts for new entities); new tables/columns present in exactly one new migration with snake_case, xmin, Restrict FKs, unique (CompanyId,Code) (or partial-unique for link entities); no pre-existing migration modified; DbContext Ignore lines + DI registrations present; controllers have zero `Domain.*` usings; Domain.csproj unchanged (zero NuGet).
- **Failing**: any pre-existing migration touched; hard delete anywhere; Cascade/SetNull on master-data FKs; non-nullable AddColumn without defaultValue on a table with existing rows (backfill risk); arch test failure; BankTests regression; Item/SupplierItem/etc. existing entities modified without a stated reason (parity must be preserved).

## Quality Standards

- Follow the entity checklist exactly: Entity(`Domain/Entities/`), Enum(`Domain/ValueObjects/` if needed), Event(`Domain/Events/`), Port(`Domain/Ports/`), EF Config(`Infrastructure/Persistence/Configurations/`), Repository(`Infrastructure/Repositories/`), DbContext Ignore, DI AddScoped, flat CQRS (Command/Query/Handler/Validator/DTO), thin controller.
- Anti-patterns: AutoMapper, navigation properties, `UpdateAsync` in repos, hard delete, non-DomainException validation, feature-folders in Application (Bank precedent is the exception), views for master data (app-wide precedent skips them).
- Good vs functional: cross-field invariants in domain ctor (like UomConversion's from≠to, factor>0), partial unique index for link entities (SupplierItem precedent), backwards-compatible ctor expansion for any existing-entity append (nullable param LAST, `HasValue && <= 0` guard).

## Prior Attempt Analysis

No prior attempts on THIS loop (fresh). Relevant prior-loop failure modes to avoid (from .global/MEMORY.md): parallel-task shared-file races on DbContext/DI (re-read before edit); MSBuild zombie OOM (`pkill -f "MSBuild.dll"`); stale LSP diagnostics ≠ real errors (build is arbiter); `grep -i <feature>` over Migrations is invalid zero-evidence (use migration count + timestamps + diff); never `database update` without explicit user approval.

## Environment & Integration

### 1. Stack summary (verified 2026-09-24)

| Layer | Tech | Version |
|-------|------|---------|
| SDK | .NET SDK | 10.0.401 (no global.json; `Directory.Build.props` sets net10.0, C# 13, nullable, implicit usings, **TreatWarningsAsErrors=true**) |
| ORM | EF Core (`Microsoft.EntityFrameworkCore`) | 10.0.4 |
| Provider | `Npgsql.EntityFrameworkCore.PostgreSQL` | 10.0.3 |
| Naming | `EFCore.NamingConventions` | 10.0.* (snake_case) |
| CQRS | MediatR | 14.2.0 |
| Validation | FluentValidation + DependencyInjectionExtensions | 12.1.0 |
| API | ASP.NET Core MVC (`AddControllersWithViews`) + Swashbuckle | 10.0.12 runtime / 10.2.3 |
| DB | PostgreSQL server | 16.14 @ `172.21.208.1`/`sme_acct_dev` (dev/123456, plaintext in appsettings.json) — **REACHABLE** ✓ |
| Tests | xunit + runner + Test.Sdk + coverlet | 2.9.3 / 3.1.4 / 17.14.1 / 6.0.4 |
| Arch tests | NetArchTest.Rules | 1.3.2 |
| EF tooling | dotnet-ef global tool | 10.0.12 |

**Baseline gates (re-verified this research):** `dotnet build SmeAccounting.sln` → 0 warnings / 0 errors (~6s). Arch tests 22/22. BankTests 115/115. DB: 54 tables, 18 migrations applied (`__EFMigrationsHistory` — note: table name is case-sensitive, query as `"__EFMigrationsHistory"`), latest `20260924003244_AddPartnerGroupsAndSupplierItems`.

**Solution layout (6 projects):** `src/SmeAccounting.Domain` (zero NuGet refs — arch-enforced), `src/SmeAccounting.Application` (MediatR CQRS, `InternalsVisibleTo("SmeAccounting.BankTests")`), `src/SmeAccounting.Infrastructure` (EF Core), `src/SmeAccounting.Api` (MVC, refs Application+Infrastructure only), `tests/SmeAccounting.ArchitectureTests` (22 NetArchTest rules, refs all 4 src projects), `tests/SmeAccounting.BankTests` (refs Domain+Application only, xunit Facts, List-backed fakes in `Fakes.cs`).

### 2. End-to-end canonical slice pattern — Item slice as template

The exact 5-layer vertical slice to replicate for each new entity. Template files (all verified):

| Layer | Template file | Pattern |
|-------|--------------|---------|
| Entity | `src/SmeAccounting.Domain/Entities/Item.cs` | `class Item : BaseEntity`; private parameterless ctor (EF) + public ctor with `DomainException` guards (CompanyId>0, Code/Name non-whitespace, cross-field invariants); `AddDomainEvent(new ItemCreated(Id, companyId, DateTimeOffset.UtcNow))`; `Deactivate() => IsActive = false` (soft delete only); no navigation properties |
| Event | `src/SmeAccounting.Domain/Events/ItemCreated.cs` | Minimal: `(long ItemId, long CompanyId, DateTimeOffset OccurredOn)` — entity ID + company ID + timestamp only |
| Port | `src/SmeAccounting.Domain/Ports/IItemRepository.cs` | `GetByIdAsync(long)`, `GetByCodeAsync(string code, long companyId)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(T)` — **no `UpdateAsync`** (change tracking) |
| EF config | `src/SmeAccounting.Infrastructure/Persistence/Configurations/ItemConfiguration.cs` | `internal sealed class ... : IEntityTypeConfiguration<T>`; `ToTable("items")` snake_case; `HasColumnName` per property; `HasConversion<string>()` for enums; `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` (no nav prop); composite unique `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()`; `Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")` last; max lengths Code=20/Name=200/Description=500 enforced here, not domain |
| Repo | `src/SmeAccounting.Infrastructure/Repositories/EfItemRepository.cs` | `public class EfItemRepository : IItemRepository`; tracked for GetById/GetByCode, `AsNoTracking()` for GetAllByCompanyAsync (`.Where(e => e.CompanyId == companyId).OrderBy(e => e.Code)`), `AddAsync` delegates to DbSet |
| Command | `src/SmeAccounting.Application/Commands/CreateItemCommand.cs` | `public record CreateItemCommand(long CompanyId, ...) : IRequest<CreateItemResult>` — **CompanyId FIRST param** (30/32 Create commands); result `record CreateItemResult(long Id)` in same file |
| Handler | `src/SmeAccounting.Application/Handlers/CreateItemHandler.cs` | `internal sealed class` (InternalsVisibleTo); ctor-injected `(IItemRepository repository, IUnitOfWork unitOfWork)`; construct domain entity → `AddAsync` → `unitOfWork.SaveChangesAsync(ct)` → return `new CreateItemResult(item.Id)` |
| Validator | `src/SmeAccounting.Application/Validators/CreateItemCommandValidator.cs` | FluentValidation `AbstractValidator<CreateItemCommand>`; English messages; `GreaterThan(0)` for CompanyId, `NotEmpty().MaximumLength(...)`, cross-field `RuleFor(x => x).Must(...)` |
| Query | `src/SmeAccounting.Application/Queries/GetItemQuery.cs` | **Multiple records per file**: `GetItemQuery(long Id)` + `GetItemsByCompanyQuery(long CompanyId)` co-located |
| Query handler | `src/SmeAccounting.Application/Handlers/GetItemHandler.cs` | One class implements both `IRequestHandler<GetItemQuery, ItemDto?>` and `IRequestHandler<GetItemsByCompanyQuery, IReadOnlyList<ItemDto>>`; private static `Map` to DTO (manual, no AutoMapper) |
| DTO | `src/SmeAccounting.Application/DTOs/ItemDto.cs` | Plain record mirroring entity, no domain refs, enums as strings |
| Controller | `src/SmeAccounting.Api/Controllers/ItemController.cs` | Thin: `IMediator` only, zero `Domain.*` usings (arch-enforced); `[HttpGet] Index(long companyId)` → `View(await _mediator.Send(new GetItemsByCompanyQuery(companyId)))`; `[HttpPost][ValidateAntiForgeryToken] Create(...)` catches `ValidationException` → `ModelState.AddModelError` → `View()`; `Deactivate` → `RedirectToAction(nameof(Index), new { companyId })` |
| Test | `tests/SmeAccounting.BankTests/SupplierItemAggregateTests.cs` + `Fakes.cs` | xunit Facts per entity (`{Entity}AggregateTests`); List-backed fakes implementing the exact port (missing member = CS0535); Deactivate-happy facts set `entity.Id = 5` BEFORE AddAsync (BaseEntity.Id public setter); explicit `using SmeAccounting.Application.Handlers;` (internal handlers, CS0246 otherwise) |

**Wiring (3 edits per entity):** DbContext `DbSet<T>` property (or Ignore-only + `Set<T>()` in repo — both styles coexist) + `modelBuilder.Ignore<XxxCreated>()` line in `SmeAccountingDbContext.cs`; one `AddScoped<IXxx, EfXxx>()` in `Infrastructure/DependencyInjection.cs` (50+ registrations, insert adjacent to related entity's line). Application DI is assembly-scanned (`AddMediatR` + `AddValidatorsFromAssembly`) — no per-handler registration.

**Views:** master-data controllers have NO views app-wide (Views/ only has ChartOfAccounts, FiscalPeriod, Home, JournalEntry, Reporting, Settings) — precedent is to skip views for master data.

### 3. Company isolation + authorization — exact mechanism

- **Authorization: NONE.** Zero `[Authorize]` attributes in any controller. `Program.cs` registers `AddAuthentication("PlaceholderScheme")` with **no scheme handler** — placeholder only, no claims, no membership checks. `AddAuthorization()` present but unused. Do NOT add auth to new controllers (matches app-wide precedent).
- **Company isolation: command/query-level, not DB-level.** No EF global query filter in `SmeAccountingDbContext.OnModelCreating` (only Ignore lines + ApplyConfigurationsFromAssembly). Isolation = (a) `CompanyId` non-nullable `long` on every master-data entity, (b) explicit `.Where(e => e.CompanyId == companyId)` in repo `GetAllByCompanyAsync`, (c) `CompanyId` first param of every Create command (client-supplied), (d) composite unique `(CompanyId, Code)` indexes as DB-level per-company uniqueness. JournalEntry has NO CompanyId column — company scoping there is command-level only.
- **FK-to-Company canon:** `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — universal, no navigation property on entity.

### 4. Migration / seed / error-handling patterns

- **Migrations:** one consolidated migration per cohesive feature, descriptive name (`AddPartnerGroupsAndSupplierItems` precedent). Generate ONLY after build+arch+tests green (`dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`; first invocation slow ~2min; use `--no-build` for list). **Check-only** — never `database update` without explicit user approval. Migration SQL: snake_case, `xmin` xid row version, all FKs `Restrict` (never Cascade/SetNull for master data), `IdentityByDefaultColumn` PKs. **Link entities** (soft-delete): partial unique index `HasIndex(...).IsUnique().HasFilter("\"is_active\"")` (SupplierItem precedent — uniqueness among ACTIVE rows only, renders `filter: "is_active"` in migration). **Nullable-FK append to existing entity:** `AddColumn nullable:true` with NO defaultValue (zero backfill risk; MEMORY:248 trap). Non-nullable AddColumn on populated table needs `defaultValue: 0L` + explicit backfill risk statement.
- **Seed:** `src/SmeAccounting.Infrastructure/Persistence/Seeds/SystemSecuritySeed.cs` — commented template only, NO `HasData` anywhere. Per-company defaults seeded via Application services, not EF. `docs/seed-system-security-defaults.md` documents the intent.
- **Error handling:** NO ProblemDetails, NO custom exception middleware, NO IExceptionHandler. Non-dev: `UseExceptionHandler("/Home/Error")` (HomeController.Error → Error view). Dev: default developer exception page. FluentValidation `ValidationException` thrown by `ValidationBehavior` pipeline, caught in controllers → `ModelState.AddModelError(propertyName, message)` → re-render `View()`. Response shape = MVC view re-render, not JSON envelope.

### 5. Table inventory — item-adjacent (all verified live in DB)

| Table | Key columns | FKs / indexes | Notes |
|-------|------------|---------------|-------|
| `items` | id, company_id, code(20), name(200), item_category_id?, uom_id?, is_stock_item, is_service_item, is_active, description(500) | unique (company_id, code); Restrict → companies/item_categories/uoms | **No tax, barcode, price, or warehouse columns** — ItemTaxClass/ItemBarcode/PriceList/ReorderLevel genuinely absent |
| `item_categories` | + parent_id? | self-FK Restrict, unique (company_id, code) | Self-ref hierarchy |
| `service_items` | + uom_id? | unique (company_id, code), Restrict → uoms | |
| `uoms` | + symbol(20)? | unique (company_id, code) | |
| `uom_conversions` | from_uom_id, to_uom_id, factor numeric(18,6) | unique (company_id, from_uom_id, to_uom_id); 2× Restrict → uoms | Invariants: from≠to, factor>0 |
| `warehouses` | + address(500)? | unique (company_id, code) | FK target for missing WarehouseLocation/Bin |
| `inventory_valuation_policies` | + valuation_method (text, enum-as-string) | unique (company_id, code) | FIFO/LIFO/WeightedAverage |
| `inventory_accounting_configurations` | inventory_account_id, cogs_account_id, inventory_adjustment_gain_account_id?, inventory_adjustment_loss_account_id? | **unique (company_id)** — 1:1 per company; 4× Restrict → accounts | No Code/Name/ValuationPolicyId |
| `inventory_adjustment_reasons` | code, name, is_active, description | unique (company_id, code) | |
| `supplier_items` | company_id, supplier_id, item_id, is_active | **partial unique (company_id, supplier_id, item_id) WHERE is_active**; Restrict → companies/suppliers/items | Pure link, NO price/cost fields — ItemSupplierPrice gap |
| `journal_entry_lines` | entry_id, account_id, debit/credit_amount + currency(3), description, cost_center_id?, department_id?, project_id? | SetNull on dimensions | **No item_id** — stock ledger out of scope per PLAN |

Only `supplier_items.item_id` references `items` (verified via pg_constraint). `Money` VO (`Domain/ValueObjects/Money.cs`, `string Currency`) exists as price-typing building block; `TaxType`/`TaxRate` (phase3) are ItemTaxClass integration targets.

### 6. Git workflow + dirty-tree warning

- **Branch:** main only (no feature branches). Commit styles: `feat:` / `fix:` / `test:` / `chore:` for code; `loop: ...` for loop-state commits (state files committed separately from code, e.g. `loop: close journal-entry-handlers`). Loop dirs renamed `_DONE` on close.
- **⚠️ DIRTY WORKING TREE (pre-existing, must not be swept in):** the entire business-partners G3 module (~70 files) is **UNCOMMITTED** — untracked: CustomerGroup/SupplierGroup/SupplierItem entities+events+ports+configs+repos+controllers+ViewModels+18 Application files+3 test files+migration `20260924003244_AddPartnerGroupsAndSupplierItems`; modified: Customer.cs, Supplier.cs, CustomerConfiguration.cs, SupplierConfiguration.cs, DbContext, DI, Fakes.cs, `.opencode/agents/verifier.md`, `loop-stack/.global/*`. **DB is AHEAD of git** (migration applied 2026-09-24, code never committed). Build is GREEN with this WIP (0/0), BankTests 115/115, arch 22/22.
- **Executor rule: NEVER `git add -A` / `git add .`** — stage only own files explicitly. On-disk migration baseline = 18 migrations / 37 .cs (includes uncommitted AddPartnerGroupsAndSupplierItems); committed baseline = 17. Inventory migration will be **#19 on disk** on top of the current snapshot. Open planner question: commit partners WIP first (complete verified module) or fold into inventory commits.

## Task-Specific Research — G1 Adversarial Review

**Date:** 2026-09-24. **Agent:** researcher (adversarial review of G1 design directions BEFORE lock-in). All evidence read from actual source; live-DB row counts verified via psql. Format: [Risk] [Evidence] [Design must include X].

### Axis 1 — Historical integrity (deactivation flows vs FK choices)

- **[R1] UomConversion's FULL unique index contradicts its own soft-delete — deactivate→re-add same (from,to) pair = DbUpdateException.** `UomConversionConfiguration.cs:24` `HasIndex((CompanyId, FromUomId, ToUomId)).IsUnique()` has NO `HasFilter`; `UomConversion.cs:32` has `Deactivate() => IsActive = false`. This is the EXACT dead-end SupplierItem fixed (global MEMORY:263: "plain unique triple on a soft-delete link entity = dead-end on deactivate→re-add"). UomConversion IS a link entity (IsActive + Deactivate) — the only link entity in the codebase with a full unique index. **Design must include:** decision on `uom_conversions` — either partial-unique `HasFilter("\"is_active\"")` on the triple (consistent with SupplierItem; requires a migration ALTER of the existing index — new index + drop old, or accept the limitation and document it). G1 must not silently carry the existing full-unique forward while adding 8 new soft-delete link entities with partial-unique.
- **[R2] Uom deactivated while conversions reference it — FK Restrict keeps rows, but nothing filters Uom.IsActive.** `UomConversionConfiguration.cs:21-22` (2× Restrict → Uom). A conversion to a deactivated Uom remains "active" — future stock math would silently use it. **Design must include:** stated query contract — conversion effective = `conversion.IsActive AND fromUom.IsActive AND toUom.IsActive` (document-only today; no conversion query exists).
- **[R3] Item deactivated while ItemBarcode/ItemPriceList/ItemSupplierPrice/ItemTaxClass/ItemReorderLevel rows active.** All child FKs must be `Restrict` — NEVER SetNull. The SetNull precedent (`JournalEntryLineConfiguration.cs:57-70`) is for OPTIONAL dimensions on JE lines, NOT for item children; SetNull on an item child would silently orphan price/tax/barcode history. **Design must include:** explicit "all item-child FKs Restrict" rule + stated query contract (child rows survive item deactivation; reads must filter `Item.IsActive`).
- **[R4] Supplier deactivated while SupplierItem/ItemSupplierPrice rows active** — same Restrict + `Supplier.IsActive` filter requirement. `Supplier.cs:49-52` Deactivate is soft-only; `SupplierItemConfiguration.cs:42-50` Restrict. **Design must include:** same query-filter statement for supplier-referencing entities.
- **[R5] PriceList deactivated while ItemPriceList rows active** — Restrict keeps rows; reads must filter `PriceList.IsActive`. Master entities (PriceList) use full unique `(CompanyId, Code)` — deactivate→re-add same code is BLOCKED (accepted master precedent: no Reactivate anywhere; `UomConfiguration.cs:42-43`). **Design must include:** classify PriceList as master (full unique, no Reactivate) and state the deactivate→re-add limitation explicitly.
- **[R6] journal_entry_lines has NO item_id** (`JournalEntryLine.cs:7-14` — EntryId/AccountId/Money/Description/dimensions only; verified live). No stock-ledger link exists. ItemSupplierPrice/ItemBarcode history survives item deactivation ONLY because soft-delete keeps the item row. **Design must include:** zero hard-delete anywhere in the 8 entities; no new FK from JE lines (out of scope).

### Axis 2 — Uniqueness + concurrency

- **[R7] Partial-unique HasFilter applies ONLY to IsActive-only link entities; effective-dated entities need full unique on the effective key.** Precedent split: SupplierItem partial-unique (`SupplierItemConfiguration.cs:30-32`) vs TaxRate full unique `(CompanyId, TaxTypeId, RateValue, EffectiveFrom)` (`TaxRateConfiguration.cs:46-47`). **Design must include:** per-entity classification of all 8 — master (full unique (CompanyId,Code)), link (partial-unique HasFilter), effective-dated (full unique incl. EffectiveFrom). ItemBarcode: partial-unique IF it has Deactivate(); ItemPriceList/ItemSupplierPrice/ItemTaxClass: partial-unique if IsActive-only, full-unique-on-effective-key if effective-dated. Mixed designs (IsActive AND EffectiveFrom) must pick the TaxRate shape (full unique on effective key; deactivate→re-add same date collides — accepted).
- **[R8] ItemTaxClass with nullable TaxRateId (exempt items) — unique index must NOT include TaxRateId.** PostgreSQL treats NULLs as distinct: unique `(CompanyId, ItemId, TaxTypeId, TaxRateId, EffectiveFrom)` allows unlimited rows with NULL TaxRateId. TaxRule precedent: TaxRateId nullable for exempt (`ADR-010:57`, `TaxRule` 4-FK shape). **Design must include:** unique on `(CompanyId, ItemId, TaxTypeId, EffectiveFrom)` — TaxRateId excluded from the key.
- **[R9] ItemReorderLevel with nullable WarehouseId — PostgreSQL unique treats NULLs as distinct.** Unique `(CompanyId, ItemId, WarehouseId)` with nullable WarehouseId allows unlimited NULL-warehouse rows for the same item (silent duplicate reorder levels). **Design must include:** decision — WarehouseId REQUIRED (per-item-per-warehouse, unique triple) OR nullable with partial unique `WHERE warehouse_id IS NULL` for per-item rows. Do not ship a nullable-WarehouseId full-unique triple.
- **[R10] xmin covers row-level optimistic concurrency on Deactivate() mutations only; insert races are covered by unique indexes only.** `SmeAccountingDbContext.cs:119-134` SaveChangesAsync + xmin row version on every table. Concurrent deactivate+re-add on a link entity → unique violation on the partial index = correct protection. **Design must include:** every new entity gets BOTH xmin AND its unique index; no reliance on application-level pre-checks (GetByCodeAsync pre-check is TOCTOU-ineffective — global MEMORY:257).
- **[R11] Composite (CompanyId, Code) races** — DB-level unique index is the real protection; port `GetByCodeAsync(code, companyId)` is a UX pre-check only. **Design must include:** `GetByCodeAsync` on master-entity ports (precedent `IItemRepository`), but design docs must not claim it prevents races.

### Axis 3 — Company isolation

- **[R12] UomClass global-vs-company: consistency argument wins — company-scoped.** Uom/ItemCategory are company-scoped (`UomConfiguration.cs:42-43` unique (CompanyId,Code); `ItemCategory.cs:9` CompanyId). A global UomClass (no CompanyId) breaks: FK-to-Company canon, unique (CompanyId,Code) pattern, `GetAllByCompanyAsync` repo pattern, and the 22-arch-rule convention set. **Design must include:** UomClass company-scoped (CompanyId + unique (CompanyId,Code) + FK Restrict). CONSEQUENCE: `Uom.UomClassId` must reference a SAME-company UomClass — cross-entity validation impossible in domain ctor (only IDs available) → Application-layer validation or document-only.
- **[R13] GTIN uniqueness scope: per-company, NOT global.** Two companies legitimately catalog the same product (same GTIN). Global unique Barcode would break multi-tenant. **Design must include:** unique `(CompanyId, Barcode)`; document that cross-company GTIN duplication is legal and expected.
- **[R14] Cross-company FK gap: child carries CompanyId + ItemId but FK is on ItemId only.** `SupplierItemConfiguration.cs:37-50` — no DB constraint prevents CompanyId=A child referencing an Item of Company=B (SupplierItem precedent accepts this). **Design must include:** stated acknowledgment — same-company consistency of (CompanyId, ItemId) pairs is Application-layer validation, not DB-enforced; do not invent composite FKs (would deviate from canon).

### Axis 4 — Accounting/tax

- **[R15] ItemTaxClass is tax CLASSIFICATION; TaxAccountingMapping is ACCOUNT mapping — must not merge.** `TaxAccountingMapping.cs:9-13` (CompanyId, TaxTypeId, TaxTreatmentId, AccountId, MappingType) + `ADR-010:63-72` (Circular 99 Art. 28 → 1331/3331/3334/3335). Goal §10 rule (tax accounting mapping) is satisfied by keeping the two mechanisms separate: ItemTaxClass says WHICH tax applies to the item; posting accounts still resolve via TaxAccountingMapping at transaction time. **Design must include:** NO Account FK on ItemTaxClass; explicit reconciliation statement in the design doc (ItemTaxClass ↔ TaxAccountingMapping are complementary, not alternatives).
- **[R16] ItemTaxClass referencing TaxRateId duplicates effective dating.** TaxRate already has EffectiveFrom/EffectiveTo (`TaxRate.cs:12-13`). If ItemTaxClass also carries EffectiveFrom/EffectiveTo, two independent date axes govern the same tax outcome. **Design must include:** pick ONE — (a) reference TaxTypeId only, rate resolved at transaction time via TaxRate effective-date query (cleaner, no duplicated dating; "TaxRate" in the name becomes a misnomer — document), or (b) reference TaxRateId + own effective dating for item-level tax changes (unique key must include own EffectiveFrom per R8). Recommend (a).
- **[R17] InventoryAccountingConfiguration is 1:1 per company with 4 Account FKs — does NOT cover item/category-scoped mapping.** `InventoryAccountingConfigurationConfiguration.cs:21` unique (CompanyId); entity has no Code/Name/ValuationPolicyId (RESEARCH.md:27). If the goal's per-item-scope requirement means per-item ACCOUNT mapping, that duplicates TaxAccountingMapping's role. **Design must include:** decision — keep company-level only (recommended: per-item account mapping is a transaction-module concern, out of scope) and document that the existing 1:1 entity is NOT extended; do not silently add scoped fields.
- **[R18] TaxRate deactivated while ItemTaxClass references it** — Restrict keeps row (`TaxRateConfiguration.cs:54-57`); effective-date query must also check `TaxRate.IsActive` (`TaxRate.cs:48-51`). **Design must include:** query contract — item tax resolution = ItemTaxClass active AND TaxType active AND (if rate referenced) TaxRate active + effective-date window.

### Axis 5 — Regulatory

- **[R19] ValuationMethod enum has LIFO (VAS-02-literal but NOT operative) and MISSES SpecificIdentification (operative).** `InventoryValuationPolicy.cs:6-11` = FIFO/LIFO/WeightedAverage. VAS 02 para 13 lists specific id, weighted avg, FIFO, LIFO (TOOLS.md:14); operative Circular 200/2014 regime = 3 methods (weighted avg, specific id, FIFO) — NO LIFO (TOOLS.md:15). **Design must include:** document BOTH facts precisely (not just "LIFO known limitation"): LIFO present-but-non-operative; SpecificIdentification operative-but-absent. No enum mutation without user approval (PLAN decision 5). Enum stored as string (`HasConversion<string>` canon) — adding SpecificIdentification later is additive/migration-free; removing LIFO is breaking.
- **[R20] UOM conversion factor decimal(18,6) — inverse factors round; reversibility not guaranteed.** `UomConversionConfiguration.cs:17` HasPrecision(18,6). 1/3 → 0.333333; inverse 3.000003 ≠ 3. **Design must include:** decision — store BOTH directions as explicit rows (allowed: unique (CompanyId, FromUomId, ToUomId) permits A→B and B→A as separate rows) vs compute inverse (rounding drift). No rounding rule exists for conversion math — document-only (no stock math in scope). Also: UomClassId append (if decided) enables class-compatibility validation of conversions — but domain ctor has only IDs → Application-layer or document-only (PLAN decision 4).
- **[R21] GTIN check-digit Mod-10 weights 3/1 — validate ONLY for GTIN lengths 8/12/13/14.** GS1 §7.10 (TOOLS.md:11-13). Generic internal barcodes must NOT be check-digit-validated (would reject valid internal codes). **Design must include:** length-based validation (validate check digit iff length ∈ {8,12,13,14}) OR a BarcodeType discriminator (GTIN vs internal); test vectors from GS1 calculator (TOOLS.md:13). Check-digit math is pure — domain ctor OK.

### Axis 6 — Empty-value traps

- **[R22] Uom.UomClassId append surface = 6 files; live DB has 0 uom rows (verified psql) — zero backfill risk.** `uoms` count = 0; no test constructs Uom (grep over tests = 0 hits); only callsite `CreateUomHandler.cs:15` passes 5 positional args — ctor param LAST keeps it compiling. **Design must include:** the full 6-file surface in the design doc: Uom entity ctor (param LAST, `HasValue && <= 0` guard per Supplier.cs:31-32 precedent), CreateUomCommand (+`long? UomClassId = null`), CreateUomCommandValidator, UomDto, GetUomHandler Map, UomConfiguration (nullable AddColumn NO defaultValue). Missing any = compile break or silent null DTO field.
- **[R23] Money VO throws ArgumentNullException, not DomainException — exception-hierarchy inconsistency if used on new entities.** `Money.cs:13` `?? throw new ArgumentNullException`. DomainException hierarchy is canon (global MEMORY:17). Also Money has NO ISO 4217/uppercase validation. **Design must include:** PLAN's stated choice (scalar `decimal` + `string Currency` on ItemPriceList/ItemSupplierPrice, NOT the Money VO) — avoids the inconsistency; currency format validation (3 uppercase) at Application layer.
- **[R24] Money mapping precedent is OwnsOne, not scalar — pick ONE and state column names.** `JournalEntryLineConfiguration.cs:28-46` maps Money via `OwnsOne` → `debit_amount`/`debit_currency` columns. If ItemPriceList used Money as owned type, columns = `price_amount`/`price_currency`; if scalar, `price` + `currency`. **Design must include:** explicit column names + precision (`HasPrecision` — codebase sets precision explicitly everywhere: UomConversion 18,6; TaxRate 5,2). Recommend decimal(18,2) for VND prices, decimal(18,6) for quantities.

### Axis 7 — Scope creep

- **[R25] ItemReorderLevel = threshold master data only.** Must NOT include min/max computation, PO suggestion, or stock-on-hand math. Applies to stock items only (`Item.cs:25` `isStockItem && !uomId.HasValue` invariant) — cross-entity validation (Item.IsStockItem) in Application layer. **Design must include:** scope statement — threshold storage only.
- **[R26] WarehouseLocation/Bin must NOT carry stock quantities** (that is a stock ledger — out of scope). Location = master data (Code/Name/type). Bank→BankBranch precedent: `BankBranchConfiguration.cs:41-42` unique (CompanyId, BankId, Code); `BankBranch.cs:17` ctor shape. **Design must include:** WarehouseLocation = (CompanyId, WarehouseId, Code, Name, IsActive, Description), unique (CompanyId, WarehouseId, Code), FK Restrict to Warehouse — no quantity columns.
- **[R27] ItemPriceList/ItemSupplierPrice = price master data** — no discount math, no price calculation, no currency conversion. **Design must include:** scope statement.
- **[R28] ItemTaxClass = classification** — no tax calculation. **Design must include:** scope statement (calculation lives in future transaction modules per ADR-010:135-144).
- **[R29] ItemGroup vs ItemCategory — ItemCategory ALREADY provides self-ref hierarchy.** `ItemCategory.cs:11` ParentId + `ItemCategoryConfiguration` self-FK Restrict. A second hierarchy on Item = duplicate concept (goal's #1 domain rule, RESEARCH.md:195). **Design must include:** pick ONE — absorb ItemGroup into ItemCategory (recommended: no duplicate hierarchy; document the absorb) OR define ItemGroup as a distinct FLAT grouping (no self-ref) with a stated distinct role (e.g., purchasing/statistical grouping vs accounting classification). Do not ship two self-ref hierarchies.
- **[R30] GTIN check-digit validation is in-scope (pure validation); GS1 company-prefix/registry lookups are NOT** (external service — out of scope). **Design must include:** scope statement.

### Cross-cutting

- **[R31] ItemBarcode references Item only — ServiceItem (separate entity/table `service_items`) cannot have barcodes.** `SmeAccountingDbContext.cs:41` ServiceItems DbSet; `Item.cs` is the only barcode target. **Design must include:** stated limitation (service-item barcodes unsupported) or explicit extension decision.
- **[R32] Migration #19 shape:** 8 CreateTable + 1 nullable AddColumn (`uoms.uom_class_id`, NO defaultValue — 0 rows verified, zero backfill risk) + partial-unique HasFilter for link entities + all FKs Restrict + xmin. Generated on top of the UNCOMMITTED partners snapshot (18 migrations / 37 .cs on disk; RESEARCH.md:311). **Design must include:** consolidated-migration checklist per G4 task; check-only; never `database update` without user approval.

### Verdict for G1

The PLAN's 5 open conflicts are correctly framed, but the design must additionally resolve: R1 (existing uom_conversions full-unique vs soft-delete — the one EXISTING table with the SupplierItem dead-end), R8/R9 (NULL-distinct unique-index traps on ItemTaxClass.TaxRateId and ItemReorderLevel.WarehouseId), R16 (ItemTaxClass effective-dating duplication with TaxRate), R19 (ValuationMethod: LIFO non-operative AND SpecificIdentification missing — both facts), R22 (6-file UomClassId append surface), R29 (ItemGroup absorb-or-distinct-role). These are the failure points a primary designer following the happy-path canon will miss.

## Task-Specific Research — G1 Design Deep-Dive

**Scope:** Final design for the 8 missing inventory entities (ItemGroup, ItemBarcode/GTIN, PriceList+ItemPriceList, ItemReorderLevel, ItemSupplierPrice, ItemTaxClass, UomClass, WarehouseLocation/Bin). Every decision grounded in verified source files (read 2026-09-24) AND reconciled against the G1 Adversarial Review (R1–R32 above). Executor transcribes verbatim; verifier checks against cited files + R-numbers.

### Verified ground truth (source files read this research)

| Fact | Source |
|------|--------|
| `Item` = CompanyId, Code(20), Name(200), ItemCategoryId?, UomId?, IsStockItem, IsServiceItem, IsActive, Description(500). Ctor: `(companyId, code, name, isStockItem, isServiceItem, itemCategoryId=null, uomId=null, description=null)`. **No TaxTypeId, no GroupId, no Barcode, no Price.** | `Domain/Entities/Item.cs` |
| `ItemCategory` = CompanyId, Code, Name, **ParentId? (self-ref Restrict)**, IsActive, Description. Hierarchy already exists. | `Domain/Entities/ItemCategory.cs` + `ItemCategoryConfiguration.cs` |
| `Uom` = CompanyId, Code, Name, Symbol?, IsActive, Description. **No class.** Ctor: `(companyId, code, name, symbol=null, description=null)`. | `Domain/Entities/Uom.cs` |
| `UomConversion` = CompanyId, FromUomId, ToUomId, **Factor decimal(18,6)** (`HasPrecision(18,6)`), IsActive. Invariants: from≠to, factor>0. Unique `(CompanyId, FromUomId, ToUomId)` **FULL unique, NO HasFilter — the SupplierItem dead-end (R1)**. Entity has only IDs — no access to Uom.UomClassId (no nav props, no repo in Domain). | `Domain/Entities/UomConversion.cs` + `UomConversionConfiguration.cs` |
| `Warehouse` = CompanyId, Code(20), Name(200), Address?(500), IsActive, Description. | `Domain/Entities/Warehouse.cs` + `WarehouseConfiguration.cs` |
| `InventoryValuationPolicy` + enum: **`ValuationMethod { FIFO, LIFO, WeightedAverage }` — LIFO present, SpecificIdentification ABSENT (R19)**. Enum stored as string (`HasConversion<string>()`). | `Domain/Entities/InventoryValuationPolicy.cs` + `InventoryValuationPolicyConfiguration.cs` |
| `InventoryAccountingConfiguration` = CompanyId + 4 Account FKs (2 required, 2 nullable), **unique index on CompanyId alone (1:1 per company)**. NOT extended (R17). | `Domain/Entities/InventoryAccountingConfiguration.cs` + config |
| `InventoryAdjustmentReason` = CompanyId, Code, Name, IsActive, Description. | `Domain/Entities/InventoryAdjustmentReason.cs` |
| `Supplier` = CompanyId, Code, Name, TaxCode?, Address?, Phone?, Email?, PaymentTermId?, DefaultTaxTypeId?, Description?, **SupplierGroupId? LAST param with `HasValue && <= 0` guard** (nullable-FK append canon). SupplierId is `long`. | `Domain/Entities/Supplier.cs` |
| `SupplierItem` = CompanyId, SupplierId, ItemId, IsActive — **pure link, NO price fields**. Partial unique `(CompanyId, SupplierId, ItemId)` `HasFilter("\"is_active\"")`. Port: GetByIdAsync, GetAllByCompanyAsync, AddAsync (**no GetByCodeAsync**). Repo uses `Set<T>()` (Ignore-only DbContext). | `Domain/Entities/SupplierItem.cs` + `SupplierItemConfiguration.cs` + `ISupplierItemRepository.cs` + `EfSupplierItemRepository.cs` |
| `TaxType` = CompanyId, Code, Name, TaxCategory (enum), IsActive, Description. | `Domain/Entities/TaxType.cs` |
| `TaxRate` = CompanyId, TaxTypeId, **RateValue decimal(5,2)**, RateName, **EffectiveFrom DateOnly (required) + EffectiveTo DateOnly? (nullable=indefinite)**, IsActive. Unique `(CompanyId, TaxTypeId, RateValue, EffectiveFrom)` — **effective-dated versioning key, plain full unique (no HasFilter)**. | `Domain/Entities/TaxRate.cs` + `TaxRateConfiguration.cs` |
| `TaxRule` = glue entity: CompanyId, TaxTypeId, TaxRateId? (nullable, `HasValue && <= 0` guard), TaxTreatmentId, Code, Name, Conditions?, LegalReference, EffectiveFrom, EffectiveTo?, IsActive. | `Domain/Entities/TaxRule.cs` |
| `Bank`→`BankBranch` parent/child: BankBranch = CompanyId, BankId, Code(50), Name(200), IsActive, Description. **Unique `(CompanyId, BankId, Code)`**, FK Restrict to Bank. | `Domain/Entities/BankBranch.cs` + `BankBranchConfiguration.cs` |
| `Money` VO = `decimal Amount` + `string Currency` (string, not FK). `BankAccount.CurrencyCode` is `string?` — currency-as-string precedent. **Money VO throws ArgumentNullException (R23) — do NOT use on new entities; use scalar decimal + string.** | `Domain/ValueObjects/Money.cs`, `Domain/Entities/BankAccount.cs` |
| `ExchangeRate` = effective-date precedent: `DateOnly EffectiveDate` (single date, not range). | `Domain/Entities/ExchangeRate.cs` |
| Canonical slice: `CreateItemCommand` (CompanyId FIRST) → `CreateItemHandler` (internal, repo+UoW) → `CreateItemCommandValidator` (FluentValidation, English msgs) → thin `ItemController` (MediatR only, catches ValidationException → ModelState). | `Application/Commands/CreateItemCommand.cs`, `Handlers/CreateItemHandler.cs`, `Validators/CreateItemCommandValidator.cs`, `Api/Controllers/ItemController.cs` |
| Uom slice (R22 6-file surface): `CreateUomHandler.cs:15` passes 5 positional args — ctor param LAST keeps it compiling. `CreateUomCommand` = (CompanyId, Code, Name, Symbol?, Description?). `UomDto` = (Id, CompanyId, Code, Name, Symbol, IsActive, Description). `GetUomHandler.Map` maps all 7. | `Handlers/CreateUomHandler.cs`, `Commands/CreateUomCommand.cs`, `DTOs/UomDto.cs`, `Validators/CreateUomCommandValidator.cs`, `Handlers/GetUomHandler.cs` |
| DbContext: DbSet per entity + one `modelBuilder.Ignore<Event>()` per event; partners use Ignore-only + `Set<T>()` (both styles coexist). DI: one `AddScoped<IXxx, EfXxx>()` per repo. | `SmeAccountingDbContext.cs`, `DependencyInjection.cs` |
| Migration baseline: **18 migrations / 37 .cs** on disk (incl. uncommitted `20260924003244_AddPartnerGroupsAndSupplierItems`). Inventory migration = **#19**. | `Migrations/` dir listing |
| GS1 check digit (verified): Mod-10, **right-to-left from rightmost data digit, weights 3/1 alternating (3 on first)**, `checkDigit = (10 - (sum % 10)) % 10`. GTIN-8/12/13/14 = 7/11/12/13 data digits + 1 check digit. | gs1.org/services/how-calculate-check-digit-manually; ref.gs1.org genspecs §7.10 |

---

### Conflict resolutions (ONE decision each, reconciled with R1–R32)

#### C1. ItemGroup vs ItemCategory — DISTINCT ROLES, no hierarchy duplication (R29 option 2)

**Decision:** ItemCategory keeps the self-ref classification hierarchy (exists, untouched). ItemGroup is a NEW flat master entity (CompanyId, Code, Name, IsActive, Description) for pricing/tax/accounting/reporting grouping, with a **nullable ItemGroupId FK appended on Item** (canon: ctor param LAST, `HasValue && <= 0` guard, AddColumn nullable NO defaultValue). **ItemGroup gets NO ParentId** — hierarchy is ItemCategory's job.

**Rationale (from code):** `ItemCategory` already provides hierarchy via `ParentId` self-ref Restrict (`ItemCategory.cs:11`, `ItemCategoryConfiguration.cs:24`) and `Item.ItemCategoryId` FK exists (`Item.cs:11`). Duplicating a hierarchy in ItemGroup would violate the goal's "reconcile, don't duplicate" and DoD #8. But ItemCategory is classification-only (Code/Name/ParentId) — it carries no pricing/tax/accounting semantics. ItemGroup's role is the flat operational grouping that pricing rules (ItemPriceList), tax classes, and reorder policies can reference. Precedent: CustomerGroup/SupplierGroup are flat group masters; `Supplier.SupplierGroupId` is the nullable-FK-append canon (`Supplier.cs:23,31-32`).

**Consequence:** 1 new table `item_groups` + 1 nullable AddColumn `item_group_id` on `items` (NO defaultValue). Item ctor gains `long? itemGroupId = null` LAST — existing callers compile unchanged. ItemGroup is a full master slice (GetByCodeAsync in port).

#### C2. ItemTaxClass — LINK ENTITY, TaxTypeId-only, effective-dated (R16 option a; R8 moot)

**Decision:** New link entity `ItemTaxClass` = CompanyId, ItemId, TaxTypeId, EffectiveFrom (DateOnly, required), EffectiveTo? (DateOnly?, nullable=indefinite), IsActive. Unique `(CompanyId, ItemId, TaxTypeId, EffectiveFrom)` — plain full unique, TaxRate versioning-key precedent. 3 FKs (Company, Item, TaxType) all Restrict. **NO TaxRateId, NO AccountId** (R16: TaxRate already effective-dated — referencing it duplicates the date axis; R15: account mapping stays in TaxAccountingMapping).

**Rationale (from code):** `TaxRate` is effective-dated (`TaxRate.cs:12-13`) — a single `TaxTypeId` FK on Item is a point-in-time snapshot that cannot answer "which tax applies on date X" and would be silently overwritten, violating DoD #11. `TaxRule` is the glue-entity precedent (`TaxRule.cs:8-18`). R16: if ItemTaxClass also carried EffectiveFrom/EffectiveTo AND referenced TaxRateId, two independent date axes govern the same tax outcome — pick ONE. **Decision: reference TaxTypeId only; the rate is resolved at transaction time via TaxRate's own effective-date query** (`EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive` — TaxRate canon, MEMORY:93). "TaxClass" name is accurate: it classifies WHICH tax type applies to the item, not which rate. R8 (nullable TaxRateId in unique key) is moot — no TaxRateId column at all. R15: ItemTaxClass ↔ TaxAccountingMapping are complementary (classification vs account mapping) — no Account FK here.

**Consequence:** 1 new table `item_tax_classes`. Item unchanged. Query contract (R18): item tax resolution = ItemTaxClass active AND TaxType active AND TaxRate (resolved by type+date) active.

#### C3. ItemSupplierPrice — NEW price-bearing entity (do NOT extend SupplierItem)

**Decision:** New entity `ItemSupplierPrice` = CompanyId, SupplierId, ItemId, UnitPrice decimal(18,2), CurrencyCode string(3), EffectiveFrom (DateOnly, required), EffectiveTo? (DateOnly?), IsActive. Unique `(CompanyId, SupplierId, ItemId, CurrencyCode, EffectiveFrom)` — plain full unique versioning key. 3 FKs (Company, Supplier, Item) all Restrict. **SupplierItem untouched.**

**Rationale (from code):** `SupplierItem` is a pure link (CompanyId, SupplierId, ItemId, IsActive — `SupplierItem.cs:8-11`) with partial-unique HasFilter — its job is "this supplier supplies this item" (approved-vendor list). A supplier+item pair has MANY prices over time; adding price columns to the link would (a) break the partial-unique semantics (one row per pair vs. N price versions), (b) mix link semantics with versioned data. Price is versioned data → needs its own rows with effective dating, exactly like TaxRate versions a TaxType. Supplier confirmed: CompanyId FIRST, SupplierId is `long` (`Supplier.cs`). PLAN.md G3 explicitly: "do NOT modify SupplierItem". R4: Supplier deactivation is soft-only; child rows survive; reads filter `Supplier.IsActive`.

**Consequence:** 1 new table `item_supplier_prices`. SupplierItem, Supplier, Item all untouched. CurrencyCode as string(3) per Money VO / BankAccount.CurrencyCode precedent (no FK to Currency; R23 — scalar, not Money VO).

#### C4. UomClass — nullable UomClassId append on Uom + handler-level class-compat check (R12, R20, R22)

**Decision:** New master entity `UomClass` = CompanyId, Code, Name, IsActive, Description, unique `(CompanyId, Code)` — **company-scoped** (R12: consistency with Uom/ItemCategory wins; global breaks FK-to-Company canon + GetAllByCompanyAsync pattern). **Nullable `UomClassId` appended on Uom** (canon: ctor param LAST, `HasValue && <= 0` guard, AddColumn nullable NO defaultValue, FK Restrict to UomClass). **Class-compatibility check lives in `CreateUomConversionHandler`** (Application layer), NOT the entity, NOT the validator.

**Rationale (from code):** Uom has no class (`Uom.cs`); UomConversion stores only FromUomId/ToUomId longs (`UomConversion.cs:9-10`) with no navigation properties and Domain has no repo access — **the entity physically cannot validate class compatibility at construction** (R12 consequence: cross-entity validation impossible in domain ctor — only IDs available). FluentValidation validators are sync-shape checks — async cross-entity repo lookups in validators are an anti-pattern here and the codebase has no precedent. The handler already has repo access (CreateItemHandler pattern) — it loads both Uoms via `IUomRepository.GetByIdAsync`, and if **both** have UomClassId and they differ → throw `DomainException`. If either Uom is unclassified (null) → allow (existing UOMs have no class; blocking would break existing conversions). Rule: reject only when both classes are present and unequal.

**R22 — full 6-file Uom append surface (missing any = compile break or silent null DTO field):**
1. `Uom.cs` — ctor gains `long? uomClassId = null` LAST + `if (uomClassId.HasValue && uomClassId <= 0) throw new DomainException(...)` (Supplier.cs:31-32 precedent); property `UomClassId` placed before `IsActive` (Supplier.cs:17 precedent).
2. `CreateUomCommand.cs` — gains `long? UomClassId = null` LAST (after Description).
3. `CreateUomCommandValidator.cs` — gains `RuleFor(x => x.UomClassId).GreaterThan(0).When(x => x.UomClassId.HasValue)`.
4. `UomDto.cs` — gains `long? UomClassId` (before IsActive, mirroring entity).
5. `GetUomHandler.cs` Map — passes `u.UomClassId` (line 26).
6. `UomConfiguration.cs` — `HasOne<UomClass>().WithMany().HasForeignKey(e => e.UomClassId).OnDelete(Restrict)`; migration = **AddColumn nullable NO defaultValue** (live `uoms` table 0 rows — zero backfill risk, R22 verified).

**R1 — uom_conversions full-unique vs soft-delete (EXISTING table, must not silently carry forward):** `UomConversionConfiguration.cs:24` full unique `(CompanyId, FromUomId, ToUomId)` + `Deactivate()` = deactivate→re-add same pair = DbUpdateException (the exact SupplierItem dead-end, MEMORY:263). **Decision: document-only limitation — do NOT alter the existing index in migration #19.** Rationale: (a) uom_conversions is an EXISTING committed table; altering its index in #19 expands migration surface and touches a parity-verify entity (DoD #23 — no modification without stated reason); (b) the codebase has NO Reactivate anywhere — the dead-end only triggers on deactivate-then-create-new-same-pair, a rare admin flow; (c) all 8 NEW entities get partial-unique where they are IsActive-only link entities, so the codebase moves forward consistently. Remediation (partial-unique HasFilter on uom_conversions) = one-line config change + migration, deferred to a future loop with user approval. **R20:** store BOTH conversion directions as explicit rows (A→B and B→A are distinct rows under the unique key) — no inverse computation, no rounding drift; document-only (no stock math in scope).

**Consequence:** 1 new table `uom_classes` + 1 nullable AddColumn `uom_class_id` on `uoms` (NO defaultValue). UomConversion entity/config unchanged. CreateUomConversionHandler gains the compat check + 2 repo lookups.

#### C5. ValuationMethod LIFO/SpecificIdentification — DOCUMENT-ONLY known limitation, no enum mutation (R19)

**Decision:** Do NOT mutate `ValuationMethod`. Document as known limitation in RESEARCH.md + G5 report. Enum stays `{ FIFO, LIFO, WeightedAverage }` exactly as committed.

**Rationale (from code + regulation):** Verified from source: `ValuationMethod { FIFO, LIFO, WeightedAverage }` (`InventoryValuationPolicy.cs:6-11`), stored as string in DB (`HasConversion<string>()`), referenced by existing CQRS + tests. **R19 — document BOTH facts precisely:** (a) LIFO is present-but-NON-OPERATIVE — VAS 02 para 13 lists it (TOOLS.md:14) but the operative VN regime (Circular 200/2014, 133/2016, 99/2025) permits only weighted avg / specific id / FIFO (TOOLS.md:15); (b) SpecificIdentification is operative-but-ABSENT from the enum. Mutating the enum breaks existing committed code/data/tests, is a compliance-relevant change requiring user approval, and this module is master-data only (no valuation engine — DoD #12). PLAN.md G1 explicitly: "no enum mutation without user approval". Enum stored as string — adding SpecificIdentification later is additive/migration-free; removing LIFO is breaking.

**Consequence:** Zero code change. G5 report lists both facts + remediation path (add SpecificIdentification, remove LIFO, remap rows) requiring user approval + migration.

---

### Entity-by-entity design blocks (executor transcribes verbatim)

#### E1. ItemGroup (new master) — C1

| Aspect | Design |
|--------|--------|
| Fields | `CompanyId long`, `Code string(20)`, `Name string(200)`, `IsActive bool = true`, `Description string?(500)` |
| Ctor | `(long companyId, string code, string name, string? description = null)` — guards: companyId>0, Code/Name non-whitespace (DomainException) |
| Company scope | FK Restrict to Company, no nav prop |
| Uniqueness | `HasIndex((CompanyId, Code)).IsUnique()` — full unique, master classification (R7) |
| Effective dates | none (master data) |
| Soft delete | `IsActive` + `Deactivate()` — deactivate→re-add same code BLOCKED (accepted master precedent, R5) |
| Events | `ItemGroupCreated(ItemGroupId, CompanyId, OccurredOn)` — minimal |
| Port | `IItemGroupRepository`: GetByIdAsync, **GetByCodeAsync(code, companyId)**, GetAllByCompanyAsync, AddAsync (master shape, ItemCategory port precedent) |
| EF config | `ToTable("item_groups")`, snake_case, xmin last, Code 20 / Name 200 / Description 500 |
| Item append | `long? ItemGroupId` on Item — ctor param LAST (`itemGroupId = null`), guard `if (itemGroupId.HasValue && itemGroupId <= 0) throw`, config `HasOne<ItemGroup>().WithMany().HasForeignKey(e => e.ItemGroupId).OnDelete(Restrict)`, **AddColumn nullable NO defaultValue** |
| NO ParentId | flat only — hierarchy stays in ItemCategory (R29) |

#### E2. ItemBarcode/GTIN (Item child) — GTIN design (R7, R13, R21, R30, R31)

| Aspect | Design |
|--------|--------|
| Fields | `CompanyId long`, `ItemId long`, `Barcode string(20)`, `BarcodeType BarcodeType` (enum), `UomId long?` (nullable — per-UOM barcodes), `IsPrimary bool = false`, `IsActive bool = true` |
| Ctor | `(long companyId, long itemId, string barcode, BarcodeType barcodeType, long? uomId = null, bool isPrimary = false)` — guards: companyId>0, itemId>0, barcode non-whitespace, uomId `HasValue && <= 0`, barcode length ≤ 20 |
| BarcodeType enum | `Domain/ValueObjects/BarcodeType.cs`: `GTIN8, GTIN12, GTIN13, GTIN14, Other` (UPC-A=GTIN-12, EAN-13=GTIN-13, ITF-14=GTIN-14, EAN-8=GTIN-8; **Other = internal/non-GS1 codes, NO check-digit validation** — R21). **No UPC-E** (compressed form — store as GTIN-12). Stored as string via `HasConversion<string>()` |
| Check-digit validation | **FluentValidation validator** (`CreateItemBarcodeCommandValidator`), private static method: GS1 Mod-10, right-to-left from rightmost data digit, weights 3/1 alternating (3 on first), `checkDigit = (10 - (sum % 10)) % 10`; **validate ONLY when BarcodeType ∈ {GTIN8, GTIN12, GTIN13, GTIN14}** (length-matched: 7/11/12/13 data digits + 1 check digit); compare computed vs. last digit; **skip entirely for `Other`** (R21 — generic internal barcodes must NOT be check-digit-validated). **Validator-only guard** — matches PaymentMethod G2 "validator-only enum guard" precedent (invalid input rejected at FluentValidation, no domain Enum.IsDefined-style guard). Domain ctor validates only non-whitespace + length. Test vectors (GS1 worked examples): GTIN-13 `6291041500213` (check digit 3); GTIN-13 `5012345670003` (check digit 3) |
| Uniqueness | `HasIndex((CompanyId, Barcode)).IsUnique().HasFilter("\"is_active\"")` — **partial-unique on active rows** (R7: ItemBarcode HAS Deactivate() → partial-unique, SupplierItem precedent; deactivate→re-add same barcode works). Per-company scope (R13: two companies legitimately catalog the same GTIN product; global unique would break multi-tenant) |
| Primary flag | `HasIndex((CompanyId, ItemId)).IsUnique().HasFilter("\"is_primary\" AND \"is_active\"")` — **one ACTIVE primary barcode per item per company** (auditor-corrected: was `"is_primary"` alone, which recreated the deactivate→re-add dead-end — Deactivate() does not clear IsPrimary, so a deactivated primary would hold the unique slot forever; the AND filter lets a deactivated primary be replaced; third HasFilter pattern in codebase) |
| Per-UOM | `UomId long?` nullable FK Restrict — same item can carry different barcodes per UOM (e.g., each vs. box of 12) |
| FKs | Company, Item, Uom — all Restrict (R3: never SetNull on item children) |
| Soft delete | `IsActive` + `Deactivate()` |
| Events | `ItemBarcodeCreated(ItemBarcodeId, CompanyId, OccurredOn)` |
| Port | `IItemBarcodeRepository`: GetByIdAsync, GetAllByCompanyAsync, AddAsync (child/link shape, SupplierItem port precedent — no GetByCodeAsync; DB partial-unique enforces barcode dup) |
| EF config | `ToTable("item_barcodes")`, Barcode 20, snake_case, xmin last |
| Scope | **Item only — ServiceItem (separate `service_items` table) cannot have barcodes** (R31, stated limitation). GS1 prefix/registry lookups OUT of scope (R30 — external service) |

#### E3. PriceList + ItemPriceList (master + child)

**PriceList (master):**

| Aspect | Design |
|--------|--------|
| Fields | `CompanyId long`, `Code string(20)`, `Name string(200)`, `IsActive bool = true`, `Description string?(500)` |
| Ctor | `(long companyId, string code, string name, string? description = null)` — standard master guards |
| Uniqueness | `HasIndex((CompanyId, Code)).IsUnique()` — full unique, master (R5: deactivate→re-add same code BLOCKED, accepted) |
| Port | `IPriceListRepository`: GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, AddAsync |
| Events | `PriceListCreated(PriceListId, CompanyId, OccurredOn)` |
| EF config | `ToTable("price_lists")`, snake_case, xmin last |

**ItemPriceList (child, price-bearing, effective-dated):**

| Aspect | Design |
|--------|--------|
| Fields | `CompanyId long`, `PriceListId long`, `ItemId long`, `UnitPrice decimal(18,2)`, `CurrencyCode string(3)`, `EffectiveFrom DateOnly` (required), `EffectiveTo DateOnly?` (nullable=indefinite), `IsActive bool = true` |
| Ctor | `(long companyId, long priceListId, long itemId, decimal unitPrice, string currencyCode, DateOnly effectiveFrom, DateOnly? effectiveTo = null)` — guards: all IDs >0, unitPrice >= 0, currencyCode 3 chars non-whitespace (normalize `ToUpperInvariant()`, ExchangeRate.cs:40 precedent), effectiveTo null-or-after-effectiveFrom |
| Decimal precision | **decimal(18,2)** for money — standard money precision (VND 0 decimals, foreign 2); TaxRate's (5,2) is a percentage rate, NOT the money precedent; UomConversion's (18,6) is a conversion factor, NOT money. Money VO uses `decimal Amount` (`Money.cs:5`) — **scalar decimal + string, NOT the Money VO** (R23: Money throws ArgumentNullException, no ISO validation; R24: scalar avoids OwnsOne column ambiguity) |
| Currency | `string CurrencyCode(3)` — Money VO / BankAccount.CurrencyCode precedent (string, not FK); format validation (3 uppercase) at Application layer (R23) |
| Uniqueness | `HasIndex((CompanyId, PriceListId, ItemId, CurrencyCode, EffectiveFrom)).IsUnique()` — versioning key (R7: effective-dated → full unique on effective key, TaxRate precedent; deactivate→re-add same date collides — accepted) |
| FKs | Company, PriceList, Item — all Restrict (R3, R5) |
| Soft delete | `IsActive` + `Deactivate()` |
| Events | `ItemPriceListCreated(ItemPriceListId, CompanyId, OccurredOn)` |
| Port | `IItemPriceListRepository`: GetByIdAsync, GetAllByCompanyAsync, AddAsync (child shape) |
| EF config | `ToTable("item_price_lists")`, UnitPrice `HasPrecision(18,2)`, CurrencyCode 3, snake_case, xmin last |
| Scope | Price master data only — no discount math, no price calculation, no currency conversion (R27) |

#### E4. ItemReorderLevel (config, per-item ± per-warehouse) — R9, R25

| Aspect | Design |
|--------|--------|
| Fields | `CompanyId long`, `ItemId long`, `WarehouseId long?` (nullable — company-wide default when null, per-warehouse override when set), `MinimumQuantity decimal(18,3)`, `MaximumQuantity decimal(18,3)?`, `IsActive bool = true` |
| Ctor | `(long companyId, long itemId, decimal minimumQuantity, long? warehouseId = null, decimal? maximumQuantity = null)` — guards: companyId>0, itemId>0, warehouseId `HasValue && <= 0`, minimumQuantity >= 0, maximumQuantity null-or->= minimumQuantity |
| Decimal precision | **decimal(18,3)** for quantities — inventory quantities with fractional units (0.001 kg); 18,6 is the conversion-factor precision (UomConversion), not quantity; 18,2 is money. Documented reasoned deviation |
| Uniqueness | **TWO partial indexes (R9 — nullable WarehouseId NULL-distinct trap; R10 — DB-level enforcement, no TOCTOU handler guard):** (a) `HasIndex((CompanyId, ItemId)).IsUnique().HasFilter("\"warehouse_id\" IS NULL AND \"is_active\"")` — one company-wide default per item; (b) `HasIndex((CompanyId, ItemId, WarehouseId)).IsUnique().HasFilter("\"warehouse_id\" IS NOT NULL AND \"is_active\"")` — one per-warehouse level per item. Both filters include is_active → deactivate→re-add works (R7). **Do NOT ship a single full-unique triple with nullable WarehouseId** (Postgres treats NULLs as distinct — unlimited NULL-warehouse rows) |
| Handler guard | **R25: stock-item-only** — `CreateItemReorderLevelHandler` loads Item via `IItemRepository.GetByIdAsync`; **null-guard FIRST** (auditor Issue C): `if (item is null) throw new InvalidOperationException($"Item {itemId} not found.")` — then `if (!item.IsStockItem)` → throw `DomainException("Reorder level requires a stock item.")` (Item.cs:26 invariant: stock items require UomId). No min/max computation, no PO suggestion, no stock-on-hand math (R25 — threshold storage only) |
| FKs | Company, Item, Warehouse — all Restrict (R3) |
| Soft delete | `IsActive` + `Deactivate()` |
| Events | `ItemReorderLevelCreated(ItemReorderLevelId, CompanyId, OccurredOn)` |
| Port | `IItemReorderLevelRepository`: GetByIdAsync, GetAllByCompanyAsync, AddAsync (child shape — NO GetByItemAndWarehouseAsync; DB partial indexes enforce, R10) |
| EF config | `ToTable("item_reorder_levels")`, Minimum/Maximum `HasPrecision(18,3)`, snake_case, xmin last |

#### E5. ItemSupplierPrice (new price-bearing entity) — C3

| Aspect | Design |
|--------|--------|
| Fields | `CompanyId long`, `SupplierId long`, `ItemId long`, `UnitPrice decimal(18,2)`, `CurrencyCode string(3)`, `EffectiveFrom DateOnly` (required), `EffectiveTo DateOnly?`, `IsActive bool = true` |
| Ctor | `(long companyId, long supplierId, long itemId, decimal unitPrice, string currencyCode, DateOnly effectiveFrom, DateOnly? effectiveTo = null)` — guards: all IDs >0, unitPrice >= 0, currencyCode 3 chars (ToUpperInvariant), effectiveTo null-or-after-effectiveFrom |
| Uniqueness | `HasIndex((CompanyId, SupplierId, ItemId, CurrencyCode, EffectiveFrom)).IsUnique()` — versioning key (R7: effective-dated → full unique, TaxRate precedent) |
| FKs | Company, Supplier, Item — all Restrict (R4: Supplier soft-delete; reads filter Supplier.IsActive) |
| Soft delete | `IsActive` + `Deactivate()` |
| Events | `ItemSupplierPriceCreated(ItemSupplierPriceId, CompanyId, OccurredOn)` |
| Port | `IItemSupplierPriceRepository`: GetByIdAsync, GetAllByCompanyAsync, AddAsync (child shape) |
| EF config | `ToTable("item_supplier_prices")`, UnitPrice `HasPrecision(18,2)`, CurrencyCode 3, snake_case, xmin last |
| SupplierItem | **UNTOUCHED** — pure link stays pure (C3) |
| Scope | Price master data only — no discount math, no currency conversion (R27) |

#### E6. ItemTaxClass (link entity) — C2 (R15, R16, R18)

| Aspect | Design |
|--------|--------|
| Fields | `CompanyId long`, `ItemId long`, `TaxTypeId long`, `EffectiveFrom DateOnly` (required), `EffectiveTo DateOnly?`, `IsActive bool = true` |
| Ctor | `(long companyId, long itemId, long taxTypeId, DateOnly effectiveFrom, DateOnly? effectiveTo = null)` — guards: companyId/itemId/taxTypeId >0, effectiveTo null-or-after-effectiveFrom |
| Uniqueness | `HasIndex((CompanyId, ItemId, TaxTypeId, EffectiveFrom)).IsUnique()` — versioning key (R7: effective-dated → full unique, TaxRate precedent). **No TaxRateId in key or entity** (R8/R16) |
| FKs | Company, Item, TaxType — all Restrict (R3, R18) |
| Soft delete | `IsActive` + `Deactivate()` |
| Events | `ItemTaxClassCreated(ItemTaxClassId, CompanyId, OccurredOn)` |
| Port | `IItemTaxClassRepository`: GetByIdAsync, GetAllByCompanyAsync, AddAsync (child shape) |
| EF config | `ToTable("item_tax_classes")`, snake_case, xmin last |
| Item | **UNTOUCHED** — no TaxTypeId FK on Item (C2) |
| Scope | Classification only — no tax calculation (R28; calculation lives in future transaction modules per ADR-010:135-144). Complementary to TaxAccountingMapping, not an alternative (R15) |

#### E7. UomClass (new master) + Uom append — C4 (R12, R22)

| Aspect | Design |
|--------|--------|
| Fields | `CompanyId long`, `Code string(20)`, `Name string(200)`, `IsActive bool = true`, `Description string?(500)` |
| Ctor | `(long companyId, string code, string name, string? description = null)` — standard master guards |
| Uniqueness | `HasIndex((CompanyId, Code)).IsUnique()` — company-scoped (R12) |
| Port | `IUomClassRepository`: GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, AddAsync (master shape) |
| Events | `UomClassCreated(UomClassId, CompanyId, OccurredOn)` |
| EF config | `ToTable("uom_classes")`, snake_case, xmin last |
| Uom append | **7-file surface (R22, §7b):** Uom entity ctor param LAST + `HasValue && <= 0` guard; CreateUomCommand +`long? UomClassId = null` LAST; CreateUomCommandValidator +`GreaterThan(0).When(HasValue)`; **CreateUomHandler pass-through (callsite line 15 — missing = silent null)**; UomDto +`long? UomClassId`; GetUomHandler Map +`u.UomClassId`; UomConfiguration `HasOne<UomClass>()...Restrict` + **AddColumn nullable NO defaultValue** (0 live rows — zero backfill risk) |
| UomConversion compat | **Handler-level** in `CreateUomConversionHandler`: load both Uoms via `IUomRepository.GetByIdAsync`; if both have UomClassId AND they differ → `throw new DomainException("Cannot convert between UOMs of different classes.")`. If either is unclassified (null) → allow. Entity unchanged (cannot validate — no data access); validator unchanged (sync-shape only). Same-company consistency of (Uom.UomClassId, UomClass.CompanyId) is Application-layer/document-only (R12, R14) |

#### E8. WarehouseLocation/Bin (Warehouse child) — Bank→BankBranch precedent (R26)

| Aspect | Design |
|--------|--------|
| Fields | `CompanyId long`, `WarehouseId long`, `Code string(20)`, `Name string(200)`, `IsActive bool = true`, `Description string?(500)` |
| Ctor | `(long companyId, long warehouseId, string code, string name, string? description = null)` — guards: companyId>0, warehouseId>0, Code/Name non-whitespace |
| Uniqueness | `HasIndex((CompanyId, WarehouseId, Code)).IsUnique()` — **BankBranch precedent** `(CompanyId, BankId, Code)` (`BankBranchConfiguration.cs:41-42`). Full unique, master-child classification (R7; deactivate→re-add same code BLOCKED, accepted — BankBranch same) |
| FKs | Company, Warehouse — both Restrict (BankBranch: Company + Bank both Restrict) |
| Soft delete | `IsActive` + `Deactivate()` |
| Events | `WarehouseLocationCreated(WarehouseLocationId, CompanyId, OccurredOn)` |
| Port | `IWarehouseLocationRepository`: GetByIdAsync, GetAllByCompanyAsync, AddAsync (child shape) |
| EF config | `ToTable("warehouse_locations")`, Code 20 / Name 200 / Description 500, snake_case, xmin last |
| Scope | **Master data only — NO stock quantity columns** (R26: quantities = stock ledger, out of scope). No bin-capacity math |

---

### Cross-cutting implementation notes (all 8)

- **Uniqueness classification (R7):** master entities (ItemGroup, PriceList, UomClass) = full unique `(CompanyId, Code)`; effective-dated entities (ItemPriceList, ItemSupplierPrice, ItemTaxClass) = full unique on effective key incl. EffectiveFrom; IsActive-only link/child with Deactivate (ItemBarcode, ItemReorderLevel) = partial-unique HasFilter; WarehouseLocation = full unique `(CompanyId, WarehouseId, Code)` (BankBranch precedent).
- **R1:** uom_conversions existing full-unique carried forward as document-only limitation — no index ALTER in #19.
- **R2/R3/R4/R18 query contracts:** child rows survive parent deactivation (all FKs Restrict, never SetNull — SetNull precedent is for OPTIONAL JE-line dimensions, NOT item children); reads must filter parent `IsActive` (Item, Supplier, PriceList, Warehouse, TaxType, TaxRate). Document-only today — no cross-entity query exists in this module.
- **R10:** every new entity gets BOTH xmin AND its unique index; no reliance on application-level pre-checks for uniqueness (GetByCodeAsync is UX pre-check only, TOCTOU-ineffective). Exception: C4's class-compat check and E4's stock-item check are cross-ENTITY validations (not uniqueness) — handler-level is the only place with data access.
- **R14:** cross-company FK gap acknowledged — child carries CompanyId + ItemId but FK is on ItemId only; same-company consistency of (CompanyId, ItemId) pairs is Application-layer validation, not DB-enforced (SupplierItem precedent accepts this). Do NOT invent composite FKs.
- **R17:** InventoryAccountingConfiguration stays 1:1 per company, NOT extended with item/category-scoped fields (per-item account mapping is a transaction-module concern, out of scope).
- **Wiring per entity:** DbContext DbSet (or Ignore-only + `Set<T>()` — both styles coexist; partners use Ignore-only) + one `modelBuilder.Ignore<XxxCreated>()`; one `AddScoped<IXxx, EfXxx>()` in `DependencyInjection.cs` (insert adjacent to related entity's line; re-read shared files before edit — parallel-task race, MEMORY:265).
- **Migration #19** (`AddInventoryModule03`): **9 CreateTable** (item_groups, item_barcodes, price_lists, item_price_lists, item_reorder_levels, item_supplier_prices, item_tax_classes, uom_classes, warehouse_locations) + **2 nullable AddColumn NO defaultValue** (item_group_id on items, uom_class_id on uoms) + **3 HasFilter partial uniques** (item_barcodes active-primary combined `"is_primary" AND "is_active"` + active `"is_active"`, item_reorder_levels `"warehouse_id" IS NULL AND "is_active"` + `"warehouse_id" IS NOT NULL AND "is_active"` — 4 filter indexes total across the two entities) + all FKs Restrict. Check-only — never `database update` without user approval. (R32 count corrected: 9 tables not 8 — ItemGroup is a new table per C1, not absorbed.)
- **Events minimalism:** all events `(EntityId, CompanyId, OccurredOn)` — never duplicate payload (global canon).
- **CompanyId FIRST** in all Create commands (30/32 precedent).
- **No views** for master data (app-wide precedent).
- **Tests:** BankTests Facts per entity, List-backed fakes in `Fakes.cs`, Id=5-before-deactivate convention, explicit `using SmeAccounting.Application.Handlers;`. New baseline after partners = 115/115 + new Facts. GS1 check-digit test vectors: GTIN-13 `6291041500213` (cd 3), GTIN-13 `5012345670003` (cd 3); invalid-length and `Other`-type negative Facts (R21).

## Design Decisions (G1)

**Date:** 2026-09-24. **Author:** executor. **Source:** transcribed verbatim from "## Task-Specific Research — G1 Design Deep-Dive" (RESEARCH.md:378-616), reconciled against "## Task-Specific Research — G1 Adversarial Review" (R1–R32, RESEARCH.md:314-376). All cited files re-read by executor 2026-09-24 before transcription. **Status:** CANONICAL — G2/G3 slices follow this record verbatim. **Scope:** design record only — zero src/ changes, zero migrations, zero git staging (G1 is loop-state only).

### 0. Cross-cutting canon (applies to all 8 entities)

| Rule | Canon |
|------|-------|
| Company scope | Non-nullable `long CompanyId` on every entity; FK `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`; no navigation property; per-company uniqueness at DB level |
| IDs | `long` identity, `ValueGeneratedOnAdd`, `BaseEntity.Id` has public setter (tests set Id directly); transient Id=0 at construction, EF assigns on save |
| Audit | `xmin` row version on every table (`Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")` last in config) |
| Soft delete | `IsActive bool = true` + `Deactivate()` sets false; no hard delete, no Reactivate anywhere |
| Validation | `DomainException` hierarchy in entity ctors (never ArgumentNullException/ArgumentOutOfRangeException); FluentValidation in Application (English messages); max lengths enforced in EF config only (Code=20, Name=200, Description=500) |
| Events | Minimal `{Entity}Created(EntityId, CompanyId, OccurredOn)` raised in ctor (ItemCreated.cs shape); one `modelBuilder.Ignore<XxxCreated>()` line per event in DbContext |
| CQRS | Flat Application layout (Commands/Queries/Handlers/Validators/DTOs); records implementing `IRequest<T>`; **CompanyId FIRST param** in Create commands (30/32 precedent); manual DTO mapping (no AutoMapper); `internal sealed class` handlers (InternalsVisibleTo("SmeAccounting.BankTests")) |
| Controllers | Thin MediatR dispatch only, zero `Domain.*` usings (arch rules 11–12); conventional MVC routes; shape = ItemController.cs:7-13: `[HttpGet] Index(long companyId)` → `View(await _mediator.Send(new GetXxxByCompanyQuery(companyId)))`; `[HttpPost][ValidateAntiForgeryToken] Create(...)` catches `ValidationException` → `ModelState.AddModelError` → `View()`; `[HttpPost] Deactivate(long id, long companyId)` → `RedirectToAction(nameof(Index), new { companyId })` |
| Wiring | DbContext DbSet (or Ignore-only + `Set<T>()` — both styles coexist; partners use Ignore-only) + one `modelBuilder.Ignore<XxxCreated>()`; one `AddScoped<IXxx, EfXxx>()` in `DependencyInjection.cs` (insert adjacent to related entity's line; re-read shared files before edit — parallel-task race, MEMORY:265) |
| Tests | BankTests Facts per entity (`{Entity}AggregateTests.cs`), List-backed fakes in `Fakes.cs` implementing the exact port (missing member = CS0535), Id=5-before-deactivate convention, explicit `using SmeAccounting.Application.Handlers;` (internal handlers, CS0246) |
| No views | Master-data views skipped app-wide (precedent) |
| Uniqueness classification (R7) | Master (ItemGroup, PriceList, UomClass) = full unique `(CompanyId, Code)`; effective-dated (ItemPriceList, ItemSupplierPrice, ItemTaxClass) = full unique on effective key incl. EffectiveFrom; IsActive-only link/child with Deactivate (ItemBarcode, ItemReorderLevel) = partial-unique HasFilter; WarehouseLocation = full unique `(CompanyId, WarehouseId, Code)` (BankBranch precedent) |
| FK Restrict rule (R3/R4/R6) | ALL item-child FKs Restrict — never SetNull (SetNull precedent is for OPTIONAL JE-line dimensions, NOT item children); zero hard-delete anywhere in the 8 entities; no new FK from journal_entry_lines (stock ledger out of scope) |
| R1 | uom_conversions existing full-unique carried forward as **documented limitation** — no index ALTER in migration #19 |
| R2/R18 query contracts | Child rows survive parent deactivation (Restrict); reads must filter parent `IsActive` (Item, Supplier, PriceList, Warehouse, TaxType, TaxRate). Document-only today — no cross-entity query exists in this module |
| R10 | Every new entity gets BOTH xmin AND its unique index; no reliance on application-level pre-checks for uniqueness (GetByCodeAsync is UX pre-check only, TOCTOU-ineffective) |
| R14 | Cross-company FK gap acknowledged — child carries CompanyId + ItemId but FK is on ItemId only; same-company consistency of (CompanyId, ItemId) pairs is Application-layer validation, not DB-enforced (SupplierItem precedent accepts this). Do NOT invent composite FKs |
| R17 | InventoryAccountingConfiguration stays 1:1 per company, NOT extended with item/category-scoped fields (per-item account mapping is a transaction-module concern, out of scope) |
| R23/R24 | Prices = scalar `decimal` + `string CurrencyCode(3)`, NOT the Money VO (Money.cs:13 throws ArgumentNullException, no ISO validation); scalar avoids OwnsOne column ambiguity; explicit column names + `HasPrecision` |
| Migration #19 (R32) | `AddInventoryModule03`: **9 CreateTable** (item_groups, item_barcodes, price_lists, item_price_lists, item_reorder_levels, item_supplier_prices, item_tax_classes, uom_classes, warehouse_locations) + **2 nullable AddColumn NO defaultValue** (item_group_id on items, uom_class_id on uoms) + **4 HasFilter partial-unique indexes** (item_barcodes `"is_primary" AND "is_active"` + `"is_active"`; item_reorder_levels `"warehouse_id" IS NULL AND "is_active"` + `"warehouse_id" IS NOT NULL AND "is_active"`) + all FKs Restrict + xmin. Check-only — never `database update` without user approval. Generated on top of the UNCOMMITTED partners snapshot (18 migrations / 37 .cs on disk) = migration #19 |

---

### 1. ItemGroup — table `item_groups`

**Conflict resolution:** **C1** (ItemGroup vs ItemCategory — DISTINCT ROLES, flat ItemGroup, no ParentId; hierarchy stays in ItemCategory). **Risks:** R5, R7, R11, R29 (dispositions in §10). **Built by:** G2 slice, PLAN task 3 (ItemGroup vertical slice). **References:** Company (FK); appends nullable `ItemGroupId` on Item.

**Company scope + ownership:** Company-scoped master data. Non-nullable `long CompanyId`; FK Restrict to Company; no nav prop. Every row owned by exactly one company; per-company uniqueness at DB level.

**Fields (exact):**

| # | Name | C# type | Precision/Length | Nullable | Default |
|---|------|---------|------------------|----------|---------|
| 1 | CompanyId | long | — | no | — |
| 2 | Code | string | 20 | no | — |
| 3 | Name | string | 200 | no | — |
| 4 | IsActive | bool | — | no | true |
| 5 | Description | string? | 500 | yes | null |

**Ctor:** `(long companyId, string code, string name, string? description = null)` — guards: companyId>0, Code/Name non-whitespace (DomainException). Private parameterless ctor for EF.

**Unique constraints:** `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()` — full unique, master classification (R7).

**FKs (all OnDelete=Restrict):** Company → companies.

**Effective-dating / IsActive / soft-delete:** No effective dating (master data). `IsActive = true` default; `Deactivate()` sets false. Deactivate→re-add same code BLOCKED (accepted master precedent, R5 — no Reactivate anywhere).

**Events:** `ItemGroupCreated(long ItemGroupId, long CompanyId, DateTimeOffset OccurredOn)` — minimal, raised in ctor.

**Port + repo behavior:** `IItemGroupRepository`: `GetByIdAsync(long)`, `GetByCodeAsync(string code, long companyId)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(ItemGroup)` (master shape, IItemCategoryRepository precedent). Repo: tracked for GetById/GetByCode, `AsNoTracking()` for GetAllByCompanyAsync (`.Where(e => e.CompanyId == companyId).OrderBy(e => e.Code)`), AddAsync delegates to DbSet. No UpdateAsync (change tracking).

**Command + validator:** `CreateItemGroupCommand(long CompanyId, string Code, string Name, string? Description = null) : IRequest<CreateItemGroupResult>`; `CreateItemGroupResult(long Id)` (co-located, CreateItemCommand.cs shape). `DeactivateItemGroupCommand(long Id) : IRequest<DeactivateItemGroupResult>`; `DeactivateItemGroupResult(bool Success)` (DeactivateItemCommand.cs shape). Validator (`CreateItemGroupCommandValidator`): CompanyId `GreaterThan(0)`; Code `NotEmpty().MaximumLength(20)`; Name `NotEmpty().MaximumLength(200)`; Description `MaximumLength(500).When(x => !string.IsNullOrWhiteSpace(x.Description))`.

**DTO + queries:** `ItemGroupDto(long Id, long CompanyId, string Code, string Name, bool IsActive, string? Description)` (UomDto.cs shape). `GetItemGroupQuery(long Id) : IRequest<ItemGroupDto?>`; `GetItemGroupsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ItemGroupDto>>` (co-located, GetItemQuery.cs shape). Handler: one class implements both, private static Map (GetItemHandler.cs shape).

**Controller routes:** `ItemGroupController` — `GET /ItemGroup/Index?companyId=`; `POST /ItemGroup/Create` (ValidateAntiForgeryToken); `POST /ItemGroup/Deactivate` (ItemController.cs:7-13 shape).

**Item append (nullable ItemGroupId):** `long? ItemGroupId` on Item — ctor param LAST (`long? itemGroupId = null`), guard `if (itemGroupId.HasValue && itemGroupId <= 0) throw new DomainException(...)` (Supplier.cs:31-32 precedent), property placed before IsActive (Supplier.cs:17 precedent); **CreateItemCommand gains `long? ItemGroupId` LAST + CreateItemHandler passes it through to the entity ctor (callsite Item.cs ctor — line 13; missing pass-through = silent null, transcription-drop pattern MEMORY:21)**; CreateItemCommandValidator `GreaterThan(0).When(x => x.ItemGroupId.HasValue)`; ItemDto + GetItemQuery handler Map include ItemGroupId; config `HasOne<ItemGroup>().WithMany().HasForeignKey(e => e.ItemGroupId).OnDelete(DeleteBehavior.Restrict)`; migration = **AddColumn nullable NO defaultValue** (zero backfill risk, MEMORY:264 canon). Existing Item callers compile unchanged (param LAST).

**BankTests (`ItemGroupAggregateTests`):** positive — ctor valid raises ItemGroupCreated with CompanyId; validator valid passes; handler happy path adds + saves (SaveCalledCount==1). negative — ctor CompanyId 0/-1 throws DomainException; Code whitespace throws; Name whitespace throws; validator CompanyId 0 fails; Code empty/21 fails; Name empty/201 fails; Description 501 fails; deactivate handler missing entity throws InvalidOperationException. deactivation — Deactivate sets IsActive false; deactivate handler happy path (Id=5 before AddAsync) deactivates + saves. company isolation — GetAllByCompanyAsync returns only rows of the requested company (repo-level fact).

---

### 2. ItemBarcode/GTIN — table `item_barcodes`

**Conflict resolution:** none of C1–C5 (standalone child entity). **Risks:** R3, R7, R10, R13, R14, R21, R30, R31 (dispositions in §10). **Built by:** G2 slice, PLAN task 4 (ItemBarcode/GTIN vertical slice). **References:** Company, Item, Uom (all FKs).

**Company scope + ownership:** Company-scoped child of Item. Non-nullable `long CompanyId`; FK Restrict to Company; no nav prop. Barcode uniqueness is **per-company, NOT global** (R13 — two companies legitimately catalog the same GTIN product; global unique would break multi-tenant).

**Fields (exact):**

| # | Name | C# type | Precision/Length | Nullable | Default |
|---|------|---------|------------------|----------|---------|
| 1 | CompanyId | long | — | no | — |
| 2 | ItemId | long | — | no | — |
| 3 | Barcode | string | 20 | no | — |
| 4 | BarcodeType | BarcodeType (enum) | string via HasConversion | no | — |
| 5 | UomId | long? | — | yes | null |
| 6 | IsPrimary | bool | — | no | false |
| 7 | IsActive | bool | — | no | true |

**Ctor:** `(long companyId, long itemId, string barcode, BarcodeType barcodeType, long? uomId = null, bool isPrimary = false)` — guards: companyId>0, itemId>0, barcode non-whitespace, barcode length ≤ 20, uomId `HasValue && <= 0` (DomainException). Private parameterless ctor for EF.

**GTIN design block (canonical):**

- **BarcodeType enum** — `Domain/ValueObjects/BarcodeType.cs`: `GTIN8, GTIN12, GTIN13, GTIN14, Other` (UPC-A = GTIN-12, EAN-13 = GTIN-13, ITF-14 = GTIN-14, EAN-8 = GTIN-8; **Other = internal/non-GS1 codes, NO check-digit validation** — R21). **No UPC-E** (compressed form — store as GTIN-12). Stored as string via `HasConversion<string>()` (enum-as-string canon).
- **Mod-10 check digit algorithm (GS1 §7.10):** for a GTIN of total length L ∈ {8, 12, 13, 14}, the last digit is the check digit and the first L−1 digits are data digits (7/11/12/13 respectively). Iterate data digits **right-to-left from the rightmost data digit**, weights alternate **3, 1, 3, 1, … with 3 on the first (rightmost) data digit**; `sum = Σ (digit × weight)`; `checkDigit = (10 − (sum % 10)) % 10`. Valid iff computed checkDigit equals the last digit. Verified test vectors: GTIN-13 `6291041500213` (data `629104150021`, sum=57, cd=3 ✓); GTIN-13 `5012345670003` (data `501234567000`, sum=57, cd=3 ✓).
- **Validation location:** `CreateItemBarcodeCommandValidator` — private static `HasValidCheckDigit(string barcode, BarcodeType type)` method; rule `Must(x => HasValidCheckDigit(x.Barcode, x.BarcodeType)).When(x => x.BarcodeType != BarcodeType.Other)`; length-match enforced inside (barcode length must equal the type's data digits + 1). **Skip entirely for `Other`** (R21 — generic internal barcodes must NOT be check-digit-validated). **Validator-only guard** — matches PaymentMethod G2 "validator-only enum guard" precedent (invalid input rejected at FluentValidation; no domain Enum.IsDefined-style guard). Domain ctor validates only non-whitespace + length ≤ 20.
- **Uniqueness (R7, R13):** (a) `HasIndex(e => new { e.CompanyId, e.Barcode }).IsUnique().HasFilter("\"is_active\"")` — partial-unique on ACTIVE rows, per-company scope; deactivate→re-add same barcode works (SupplierItem precedent, first HasFilter pattern). (b) `HasIndex(e => new { e.CompanyId, e.ItemId }).IsUnique().HasFilter("\"is_primary\" AND \"is_active\"")` — **one ACTIVE primary barcode per item per company** (auditor-corrected: `"is_primary"` alone recreates the deactivate→re-add dead-end since Deactivate() does not clear IsPrimary).
- **UomId? nullable:** per-UOM barcodes — same item can carry different barcodes per UOM (e.g., each vs. box of 12). FK Restrict to Uom; guard `HasValue && <= 0`.

**FKs (all OnDelete=Restrict):** Company → companies; Item → items; Uom → uoms (R3 — never SetNull on item children).

**Effective-dating / IsActive / soft-delete:** No effective dating. `IsActive = true` default; `Deactivate()` sets false. Partial-unique HasFilter on is_active → deactivate→re-add works.

**Events:** `ItemBarcodeCreated(long ItemBarcodeId, long CompanyId, DateTimeOffset OccurredOn)` — minimal.

**Port + repo behavior:** `IItemBarcodeRepository`: `GetByIdAsync(long)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(ItemBarcode)` (child/link shape, ISupplierItemRepository precedent — **no GetByCodeAsync**; DB partial-unique enforces barcode dup, R10). Repo: tracked for GetById, `AsNoTracking()` for GetAllByCompanyAsync, AddAsync delegates to DbSet.

**Command + validator:** `CreateItemBarcodeCommand(long CompanyId, long ItemId, string Barcode, BarcodeType BarcodeType, long? UomId = null, bool IsPrimary = false) : IRequest<CreateItemBarcodeResult>`; `CreateItemBarcodeResult(long Id)`. `DeactivateItemBarcodeCommand(long Id) : IRequest<DeactivateItemBarcodeResult>`; `DeactivateItemBarcodeResult(bool Success)`. Validator (`CreateItemBarcodeCommandValidator`): CompanyId `GreaterThan(0)`; ItemId `GreaterThan(0)`; Barcode `NotEmpty().MaximumLength(20)`; UomId `GreaterThan(0).When(x => x.UomId.HasValue)`; BarcodeType `IsInEnum()`; check-digit `Must(...)` per GTIN design block above.

**DTO + queries:** `ItemBarcodeDto(long Id, long CompanyId, long ItemId, string Barcode, string BarcodeType, long? UomId, bool IsPrimary, bool IsActive)` (enum as string via `.ToString()`, DTO canon). `GetItemBarcodeQuery(long Id) : IRequest<ItemBarcodeDto?>`; `GetItemBarcodesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ItemBarcodeDto>>`.

**Controller routes:** `ItemBarcodeController` — `GET /ItemBarcode/Index?companyId=`; `POST /ItemBarcode/Create`; `POST /ItemBarcode/Deactivate`.

**BankTests (`ItemBarcodeAggregateTests`):** positive — ctor valid raises ItemBarcodeCreated with CompanyId; validator valid GTIN-13 `6291041500213` passes; validator valid GTIN-13 `5012345670003` passes; validator `Other` type with arbitrary internal code passes (check digit skipped); handler happy path adds + saves. negative — ctor CompanyId/ItemId 0/-1 throws DomainException; barcode whitespace throws; barcode length 21 throws; UomId 0/-1 throws; validator invalid check digit fails; validator wrong-length GTIN fails; validator BarcodeType (Enum)999 fails IsInEnum; deactivate handler missing entity throws InvalidOperationException. deactivation — Deactivate sets IsActive false; deactivate handler happy path (Id=5) deactivates + saves. company isolation — GetAllByCompanyAsync filters by company.

**Scope statements:** Item only — **ServiceItem (separate `service_items` table) cannot have barcodes** (R31, stated limitation). GS1 company-prefix/registry lookups OUT of scope (R30 — external service; check-digit validation only).

---

### 3. PriceList + ItemPriceList — tables `price_lists`, `item_price_lists`

**Conflict resolution:** none of C1–C5 (master + child pair). **Risks:** R3, R5, R7, R10, R14, R23, R24, R27 (dispositions in §10). **Built by:** G2 slice, PLAN task 5 (PriceList + ItemPriceList vertical slice). **References:** Company, PriceList, Item (FKs).

#### 3a. PriceList (master)

**Company scope + ownership:** Company-scoped master data. Non-nullable `long CompanyId`; FK Restrict to Company; no nav prop.

**Fields (exact):**

| # | Name | C# type | Precision/Length | Nullable | Default |
|---|------|---------|------------------|----------|---------|
| 1 | CompanyId | long | — | no | — |
| 2 | Code | string | 20 | no | — |
| 3 | Name | string | 200 | no | — |
| 4 | IsActive | bool | — | no | true |
| 5 | Description | string? | 500 | yes | null |

**Ctor:** `(long companyId, string code, string name, string? description = null)` — standard master guards (companyId>0, Code/Name non-whitespace).

**Unique constraints:** `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()` — full unique, master (R5: deactivate→re-add same code BLOCKED, accepted).

**FKs (all OnDelete=Restrict):** Company → companies.

**Effective-dating / IsActive / soft-delete:** No effective dating (master). `IsActive = true`; `Deactivate()` sets false.

**Events:** `PriceListCreated(long PriceListId, long CompanyId, DateTimeOffset OccurredOn)`.

**Port + repo behavior:** `IPriceListRepository`: `GetByIdAsync(long)`, `GetByCodeAsync(string code, long companyId)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(PriceList)` (master shape).

**Command + validator:** `CreatePriceListCommand(long CompanyId, string Code, string Name, string? Description = null) : IRequest<CreatePriceListResult>`; `CreatePriceListResult(long Id)`. `DeactivatePriceListCommand(long Id) : IRequest<DeactivatePriceListResult>`. Validator: CompanyId `GreaterThan(0)`; Code `NotEmpty().MaximumLength(20)`; Name `NotEmpty().MaximumLength(200)`; Description `MaximumLength(500).When(...)`.

**DTO + queries:** `PriceListDto(long Id, long CompanyId, string Code, string Name, bool IsActive, string? Description)`. `GetPriceListQuery(long Id)`; `GetPriceListsByCompanyQuery(long CompanyId)`.

**Controller routes:** `PriceListController` — `GET /PriceList/Index?companyId=`; `POST /PriceList/Create`; `POST /PriceList/Deactivate`.

**BankTests (`PriceListAggregateTests`):** positive — ctor valid raises PriceListCreated with CompanyId; validator valid passes; handler happy path. negative — ctor CompanyId 0/-1 throws; Code/Name whitespace throws; validator CompanyId 0, Code empty/21, Name empty/201, Description 501 fail; deactivate handler missing entity throws InvalidOperationException. deactivation — Deactivate sets IsActive false; deactivate handler happy path (Id=5). company isolation — GetAllByCompanyAsync filters.

#### 3b. ItemPriceList (child, price-bearing, effective-dated)

**Company scope + ownership:** Company-scoped child of PriceList + Item. Non-nullable `long CompanyId`; FK Restrict to Company; no nav prop.

**Fields (exact):**

| # | Name | C# type | Precision/Length | Nullable | Default |
|---|------|---------|------------------|----------|---------|
| 1 | CompanyId | long | — | no | — |
| 2 | PriceListId | long | — | no | — |
| 3 | ItemId | long | — | no | — |
| 4 | UnitPrice | decimal | decimal(18,2) | no | — |
| 5 | CurrencyCode | string | 3 | no | — |
| 6 | EffectiveFrom | DateOnly | — | no | — |
| 7 | EffectiveTo | DateOnly? | — | yes | null (indefinite) |
| 8 | IsActive | bool | — | no | true |

**Ctor:** `(long companyId, long priceListId, long itemId, decimal unitPrice, string currencyCode, DateOnly effectiveFrom, DateOnly? effectiveTo = null)` — guards: all IDs >0, unitPrice >= 0, currencyCode 3 chars non-whitespace (normalize `ToUpperInvariant()`, ExchangeRate.cs:40 precedent), effectiveTo null-or-on/after-effectiveFrom (DomainException).

**Decimal precision:** **decimal(18,2)** for money — standard money precision (VND 0 decimals, foreign 2). TaxRate's (5,2) is a percentage rate, NOT the money precedent; UomConversion's (18,6) is a conversion factor, NOT money. Money VO uses `decimal Amount` (Money.cs:5) — **scalar decimal + string, NOT the Money VO** (R23: Money throws ArgumentNullException, no ISO validation; R24: scalar avoids OwnsOne column ambiguity).

**Currency:** `string CurrencyCode(3)` — Money VO / BankAccount.CurrencyCode precedent (string, not FK to Currency). Format validation (3 uppercase, ISO 4217 shape) at Application layer (R23): validator `NotEmpty().Length(3).Matches("^[A-Z]{3}$")`.

**Unique constraints:** `HasIndex(e => new { e.CompanyId, e.PriceListId, e.ItemId, e.CurrencyCode, e.EffectiveFrom }).IsUnique()` — versioning key (R7: effective-dated → full unique on effective key, TaxRate precedent; deactivate→re-add same date collides — accepted).

**FKs (all OnDelete=Restrict):** Company → companies; PriceList → price_lists; Item → items (R3, R5).

**Effective-dating / IsActive / soft-delete:** EffectiveFrom required + EffectiveTo? nullable = indefinite (TaxRate.cs:12-13 pattern). `IsActive = true`; `Deactivate()` sets false. Effective-date query contract (future): `EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive` (TaxRate canon, MEMORY:93).

**Events:** `ItemPriceListCreated(long ItemPriceListId, long CompanyId, DateTimeOffset OccurredOn)`.

**Port + repo behavior:** `IItemPriceListRepository`: `GetByIdAsync(long)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(ItemPriceList)` (child shape).

**Command + validator:** `CreateItemPriceListCommand(long CompanyId, long PriceListId, long ItemId, decimal UnitPrice, string CurrencyCode, DateOnly EffectiveFrom, DateOnly? EffectiveTo = null) : IRequest<CreateItemPriceListResult>`; `CreateItemPriceListResult(long Id)`. `DeactivateItemPriceListCommand(long Id)`. Validator (`CreateItemPriceListCommandValidator`): CompanyId/PriceListId/ItemId `GreaterThan(0)`; UnitPrice `GreaterThanOrEqualTo(0)`; CurrencyCode `NotEmpty().Length(3).Matches("^[A-Z]{3}$")`; EffectiveFrom `NotEmpty()`; `RuleFor(x => x).Must(x => !x.EffectiveTo.HasValue || x.EffectiveTo >= x.EffectiveFrom).WithMessage("EffectiveTo must be null or on/after EffectiveFrom.")`.

**DTO + queries:** `ItemPriceListDto(long Id, long CompanyId, long PriceListId, long ItemId, decimal UnitPrice, string CurrencyCode, DateOnly EffectiveFrom, DateOnly? EffectiveTo, bool IsActive)`. `GetItemPriceListQuery(long Id)`; `GetItemPriceListsByCompanyQuery(long CompanyId)`.

**Controller routes:** `ItemPriceListController` — `GET /ItemPriceList/Index?companyId=`; `POST /ItemPriceList/Create`; `POST /ItemPriceList/Deactivate`.

**BankTests (`ItemPriceListAggregateTests`):** positive — ctor valid raises ItemPriceListCreated with CompanyId; currencyCode normalized to uppercase; validator valid passes; handler happy path. negative — ctor CompanyId/PriceListId/ItemId 0/-1 throws; unitPrice negative throws; currencyCode empty/2-char/4-char throws (lowercase 3-char is NORMALIZED to uppercase in ctor — "lowercase throws" is a transcription outlier, see Task-Specific Research — PriceList Slice §3; validator `Matches("^[A-Z]{3}$")` rejects lowercase); effectiveTo before effectiveFrom throws; validator each rule fails; deactivate handler missing entity throws InvalidOperationException. deactivation — Deactivate sets IsActive false; deactivate handler happy path (Id=5). company isolation — GetAllByCompanyAsync filters.

**Scope:** Price master data only — no discount math, no price calculation, no currency conversion (R27).

---

### 4. ItemReorderLevel — table `item_reorder_levels`

**Conflict resolution:** none of C1–C5 (config entity). **Risks:** R3, R7, R9, R10, R14, R25 (dispositions in §10). **Built by:** G3 slice, PLAN task 6 (ItemReorderLevel vertical slice). **References:** Company, Item, Warehouse (FKs).

**Company scope + ownership:** Company-scoped config child of Item (optionally per-Warehouse). Non-nullable `long CompanyId`; FK Restrict to Company; no nav prop.

**Fields (exact):**

| # | Name | C# type | Precision/Length | Nullable | Default |
|---|------|---------|------------------|----------|---------|
| 1 | CompanyId | long | — | no | — |
| 2 | ItemId | long | — | no | — |
| 3 | WarehouseId | long? | — | yes | null (company-wide default when null; per-warehouse override when set) |
| 4 | MinimumQuantity | decimal | decimal(18,3) | no | — |
| 5 | MaximumQuantity | decimal? | decimal(18,3) | yes | null |
| 6 | IsActive | bool | — | no | true |

**Ctor:** `(long companyId, long itemId, decimal minimumQuantity, long? warehouseId = null, decimal? maximumQuantity = null)` — guards: companyId>0, itemId>0, warehouseId `HasValue && <= 0`, minimumQuantity >= 0, maximumQuantity null-or->= minimumQuantity (DomainException).

**Decimal precision:** **decimal(18,3)** for quantities — inventory quantities with fractional units (0.001 kg); 18,6 is the conversion-factor precision (UomConversion), 18,2 is money. Documented reasoned deviation.

**Unique constraints — TWO partial indexes (R9 — nullable WarehouseId NULL-distinct trap; R10 — DB-level enforcement, no TOCTOU handler guard):**
- (a) `HasIndex(e => new { e.CompanyId, e.ItemId }).IsUnique().HasFilter("\"warehouse_id\" IS NULL AND \"is_active\"")` — one company-wide default per item;
- (b) `HasIndex(e => new { e.CompanyId, e.ItemId, e.WarehouseId }).IsUnique().HasFilter("\"warehouse_id\" IS NOT NULL AND \"is_active\"")` — one per-warehouse level per item.
Both filters include is_active → deactivate→re-add works (R7). **Do NOT ship a single full-unique triple with nullable WarehouseId** (Postgres treats NULLs as distinct — unlimited NULL-warehouse rows).

**FKs (all OnDelete=Restrict):** Company → companies; Item → items; Warehouse → warehouses (R3).

**Effective-dating / IsActive / soft-delete:** No effective dating (threshold config). `IsActive = true`; `Deactivate()` sets false.

**Handler guard (R25 — stock-item-only):** `CreateItemReorderLevelHandler` gains `IItemRepository` dependency; loads Item via `GetByIdAsync`; **null-guard FIRST** (auditor Issue C): `if (item is null) throw new InvalidOperationException($"Item {itemId} not found.")`; then `if (!item.IsStockItem)` → `throw new DomainException("Reorder level requires a stock item.")` (Item.cs:26 invariant: stock items require UomId). No min/max computation, no PO suggestion, no stock-on-hand math (R25 — threshold storage only).

**Events:** `ItemReorderLevelCreated(long ItemReorderLevelId, long CompanyId, DateTimeOffset OccurredOn)`.

**Port + repo behavior:** `IItemReorderLevelRepository`: `GetByIdAsync(long)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(ItemReorderLevel)` (child shape — **NO GetByItemAndWarehouseAsync**; DB partial indexes enforce, R10).

**Command + validator:** `CreateItemReorderLevelCommand(long CompanyId, long ItemId, decimal MinimumQuantity, long? WarehouseId = null, decimal? MaximumQuantity = null) : IRequest<CreateItemReorderLevelResult>`; `CreateItemReorderLevelResult(long Id)`. `DeactivateItemReorderLevelCommand(long Id)`. Validator (`CreateItemReorderLevelCommandValidator`): CompanyId/ItemId `GreaterThan(0)`; WarehouseId `GreaterThan(0).When(x => x.WarehouseId.HasValue)`; MinimumQuantity `GreaterThanOrEqualTo(0)`; `RuleFor(x => x).Must(x => !x.MaximumQuantity.HasValue || x.MaximumQuantity >= x.MinimumQuantity).WithMessage("MaximumQuantity must be null or >= MinimumQuantity.")`.

**DTO + queries:** `ItemReorderLevelDto(long Id, long CompanyId, long ItemId, long? WarehouseId, decimal MinimumQuantity, decimal? MaximumQuantity, bool IsActive)`. `GetItemReorderLevelQuery(long Id)`; `GetItemReorderLevelsByCompanyQuery(long CompanyId)`.

**Controller routes:** `ItemReorderLevelController` — `GET /ItemReorderLevel/Index?companyId=`; `POST /ItemReorderLevel/Create`; `POST /ItemReorderLevel/Deactivate`.

**BankTests (`ItemReorderLevelAggregateTests`):** positive — ctor valid raises ItemReorderLevelCreated with CompanyId; handler happy path adds + saves; handler stock-item guard passes for IsStockItem item. negative — ctor CompanyId/ItemId 0/-1 throws; WarehouseId 0/-1 throws; MinimumQuantity negative throws; MaximumQuantity < MinimumQuantity throws; validator each rule fails; handler non-stock item throws DomainException; handler item-not-found throws InvalidOperationException (null-guard, not NRE); deactivate handler missing entity throws InvalidOperationException. deactivation — Deactivate sets IsActive false; deactivate handler happy path (Id=5). company isolation — GetAllByCompanyAsync filters.

**Scope:** Threshold storage only (R25) — no min/max computation, no PO suggestion, no stock-on-hand math.

---

### 5. ItemSupplierPrice — table `item_supplier_prices`

**Conflict resolution:** **C3** (NEW price-bearing entity; SupplierItem untouched). **Risks:** R3, R4, R7, R10, R14, R23, R24, R27 (dispositions in §10). **Built by:** G3 slice, PLAN task 7 (ItemSupplierPrice vertical slice). **References:** Company, Supplier, Item (FKs).

**Company scope + ownership:** Company-scoped price child of Supplier + Item. Non-nullable `long CompanyId`; FK Restrict to Company; no nav prop.

**Fields (exact):**

| # | Name | C# type | Precision/Length | Nullable | Default |
|---|------|---------|------------------|----------|---------|
| 1 | CompanyId | long | — | no | — |
| 2 | SupplierId | long | — | no | — |
| 3 | ItemId | long | — | no | — |
| 4 | UnitPrice | decimal | decimal(18,2) | no | — |
| 5 | CurrencyCode | string | 3 | no | — |
| 6 | EffectiveFrom | DateOnly | — | no | — |
| 7 | EffectiveTo | DateOnly? | — | yes | null (indefinite) |
| 8 | IsActive | bool | — | no | true |

**Ctor:** `(long companyId, long supplierId, long itemId, decimal unitPrice, string currencyCode, DateOnly effectiveFrom, DateOnly? effectiveTo = null)` — guards: all IDs >0, unitPrice >= 0, currencyCode 3 chars (normalize `ToUpperInvariant()`), effectiveTo null-or-on/after-effectiveFrom (DomainException).

**Decimal precision / Currency:** decimal(18,2) money precision; `string CurrencyCode(3)` scalar (R23/R24 — same as ItemPriceList §3b).

**Unique constraints:** `HasIndex(e => new { e.CompanyId, e.SupplierId, e.ItemId, e.CurrencyCode, e.EffectiveFrom }).IsUnique()` — versioning key (R7: effective-dated → full unique, TaxRate precedent).

**FKs (all OnDelete=Restrict):** Company → companies; Supplier → suppliers; Item → items (R4: Supplier deactivation is soft-only; child rows survive; reads filter `Supplier.IsActive`).

**Effective-dating / IsActive / soft-delete:** EffectiveFrom required + EffectiveTo? nullable = indefinite. `IsActive = true`; `Deactivate()` sets false. Effective-date query contract (future): `EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive`.

**Events:** `ItemSupplierPriceCreated(long ItemSupplierPriceId, long CompanyId, DateTimeOffset OccurredOn)`.

**Port + repo behavior:** `IItemSupplierPriceRepository`: `GetByIdAsync(long)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(ItemSupplierPrice)` (child shape).

**Command + validator:** `CreateItemSupplierPriceCommand(long CompanyId, long SupplierId, long ItemId, decimal UnitPrice, string CurrencyCode, DateOnly EffectiveFrom, DateOnly? EffectiveTo = null) : IRequest<CreateItemSupplierPriceResult>`; `CreateItemSupplierPriceResult(long Id)`. `DeactivateItemSupplierPriceCommand(long Id)`. Validator (`CreateItemSupplierPriceCommandValidator`): CompanyId/SupplierId/ItemId `GreaterThan(0)`; UnitPrice `GreaterThanOrEqualTo(0)`; CurrencyCode `NotEmpty().Length(3).Matches("^[A-Z]{3}$")`; EffectiveFrom `NotEmpty()`; EffectiveTo null-or-on/after-EffectiveFrom Must.

**DTO + queries:** `ItemSupplierPriceDto(long Id, long CompanyId, long SupplierId, long ItemId, decimal UnitPrice, string CurrencyCode, DateOnly EffectiveFrom, DateOnly? EffectiveTo, bool IsActive)`. `GetItemSupplierPriceQuery(long Id)`; `GetItemSupplierPricesByCompanyQuery(long CompanyId)`.

**Controller routes:** `ItemSupplierPriceController` — `GET /ItemSupplierPrice/Index?companyId=`; `POST /ItemSupplierPrice/Create`; `POST /ItemSupplierPrice/Deactivate`.

**BankTests (`ItemSupplierPriceAggregateTests`):** positive — ctor valid raises ItemSupplierPriceCreated with CompanyId; currencyCode normalized to uppercase; validator valid passes; handler happy path. negative — ctor CompanyId/SupplierId/ItemId 0/-1 throws; unitPrice negative throws; currencyCode invalid throws; effectiveTo before effectiveFrom throws; validator each rule fails; deactivate handler missing entity throws InvalidOperationException. deactivation — Deactivate sets IsActive false; deactivate handler happy path (Id=5). company isolation — GetAllByCompanyAsync filters.

**SupplierItem:** **UNTOUCHED** — pure link stays pure (C3). **Scope:** Price master data only — no discount math, no currency conversion (R27).

---

### 6. ItemTaxClass — table `item_tax_classes`

**Conflict resolution:** **C2** (LINK ENTITY, TaxTypeId-only, effective-dated; R16 option a; R8 moot). **Risks:** R3, R7, R8, R10, R14, R15, R16, R18, R28 (dispositions in §10). **Built by:** G3 slice, PLAN task 8 (ItemTaxClass vertical slice). **References:** Company, Item, TaxType (FKs).

**Company scope + ownership:** Company-scoped link between Item and TaxType. Non-nullable `long CompanyId`; FK Restrict to Company; no nav prop.

**Fields (exact):**

| # | Name | C# type | Precision/Length | Nullable | Default |
|---|------|---------|------------------|----------|---------|
| 1 | CompanyId | long | — | no | — |
| 2 | ItemId | long | — | no | — |
| 3 | TaxTypeId | long | — | no | — |
| 4 | EffectiveFrom | DateOnly | — | no | — |
| 5 | EffectiveTo | DateOnly? | — | yes | null (indefinite) |
| 6 | IsActive | bool | — | no | true |

**Ctor:** `(long companyId, long itemId, long taxTypeId, DateOnly effectiveFrom, DateOnly? effectiveTo = null)` — guards: companyId/itemId/taxTypeId >0, effectiveTo null-or-on/after-effectiveFrom (DomainException).

**Unique constraints:** `HasIndex(e => new { e.CompanyId, e.ItemId, e.TaxTypeId, e.EffectiveFrom }).IsUnique()` — versioning key (R7: effective-dated → full unique, TaxRate precedent). **No TaxRateId in key or entity** (R8/R16 — PostgreSQL NULL-distinct trap avoided by having no nullable key member at all).

**FKs (all OnDelete=Restrict):** Company → companies; Item → items; TaxType → tax_types (R3, R18).

**Effective-dating / IsActive / soft-delete:** EffectiveFrom required + EffectiveTo? nullable = indefinite. `IsActive = true`; `Deactivate()` sets false. **Query contract (R18):** item tax resolution = ItemTaxClass active AND TaxType active AND TaxRate (resolved by type+date) active + effective window (`EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive` — TaxRate canon).

**Events:** `ItemTaxClassCreated(long ItemTaxClassId, long CompanyId, DateTimeOffset OccurredOn)`.

**Port + repo behavior:** `IItemTaxClassRepository`: `GetByIdAsync(long)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(ItemTaxClass)` (child shape).

**Command + validator:** `CreateItemTaxClassCommand(long CompanyId, long ItemId, long TaxTypeId, DateOnly EffectiveFrom, DateOnly? EffectiveTo = null) : IRequest<CreateItemTaxClassResult>`; `CreateItemTaxClassResult(long Id)`. `DeactivateItemTaxClassCommand(long Id)`. Validator (`CreateItemTaxClassCommandValidator`): CompanyId/ItemId/TaxTypeId `GreaterThan(0)`; EffectiveFrom `NotEmpty()`; EffectiveTo null-or-on/after-EffectiveFrom Must.

**DTO + queries:** `ItemTaxClassDto(long Id, long CompanyId, long ItemId, long TaxTypeId, DateOnly EffectiveFrom, DateOnly? EffectiveTo, bool IsActive)`. `GetItemTaxClassQuery(long Id)`; `GetItemTaxClassesByCompanyQuery(long CompanyId)`.

**Controller routes:** `ItemTaxClassController` — `GET /ItemTaxClass/Index?companyId=`; `POST /ItemTaxClass/Create`; `POST /ItemTaxClass/Deactivate`.

**BankTests (`ItemTaxClassAggregateTests`):** positive — ctor valid raises ItemTaxClassCreated with CompanyId; validator valid passes; handler happy path. negative — ctor CompanyId/ItemId/TaxTypeId 0/-1 throws; effectiveTo before effectiveFrom throws; validator each rule fails; deactivate handler missing entity throws InvalidOperationException. deactivation — Deactivate sets IsActive false; deactivate handler happy path (Id=5). company isolation — GetAllByCompanyAsync filters.

**Item:** **UNTOUCHED** — no TaxTypeId FK on Item (C2). **Scope:** Classification only — no tax calculation (R28; calculation lives in future transaction modules per ADR-010:135-144). Complementary to TaxAccountingMapping, not an alternative (R15 — no Account FK here).

---

### 7. UomClass — table `uom_classes` (+ Uom append)

**Conflict resolution:** **C4** (nullable UomClassId append on Uom + handler-level class-compat check; R12, R20, R22). **Risks:** R1, R2, R7, R10, R11, R12, R14, R20, R22 (dispositions in §10). **Built by:** G2 slice, PLAN task 2 (UomClass vertical slice). **References:** Company (FK); appends nullable `UomClassId` on Uom; adds class-compat check to CreateUomConversionHandler.

**Company scope + ownership:** Company-scoped master data (R12 — consistency with Uom/ItemCategory wins; global breaks FK-to-Company canon + GetAllByCompanyAsync pattern). Non-nullable `long CompanyId`; FK Restrict to Company; no nav prop.

**Fields (exact):**

| # | Name | C# type | Precision/Length | Nullable | Default |
|---|------|---------|------------------|----------|---------|
| 1 | CompanyId | long | — | no | — |
| 2 | Code | string | 20 | no | — |
| 3 | Name | string | 200 | no | — |
| 4 | IsActive | bool | — | no | true |
| 5 | Description | string? | 500 | yes | null |

**Ctor:** `(long companyId, string code, string name, string? description = null)` — standard master guards.

**Unique constraints:** `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()` — company-scoped (R12).

**FKs (all OnDelete=Restrict):** Company → companies.

**Effective-dating / IsActive / soft-delete:** No effective dating (master). `IsActive = true`; `Deactivate()` sets false. Deactivate→re-add same code BLOCKED (accepted master precedent, R5).

**Events:** `UomClassCreated(long UomClassId, long CompanyId, DateTimeOffset OccurredOn)`.

**Port + repo behavior:** `IUomClassRepository`: `GetByIdAsync(long)`, `GetByCodeAsync(string code, long companyId)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(UomClass)` (master shape).

**Command + validator:** `CreateUomClassCommand(long CompanyId, string Code, string Name, string? Description = null) : IRequest<CreateUomClassResult>`; `CreateUomClassResult(long Id)`. `DeactivateUomClassCommand(long Id)`. Validator (`CreateUomClassCommandValidator`): CompanyId `GreaterThan(0)`; Code `NotEmpty().MaximumLength(20)`; Name `NotEmpty().MaximumLength(200)`; Description `MaximumLength(500).When(...)`.

**DTO + queries:** `UomClassDto(long Id, long CompanyId, string Code, string Name, bool IsActive, string? Description)`. `GetUomClassQuery(long Id)`; `GetUomClassesByCompanyQuery(long CompanyId)`.

**Controller routes:** `UomClassController` — `GET /UomClass/Index?companyId=`; `POST /UomClass/Create`; `POST /UomClass/Deactivate`.

**BankTests (`UomClassAggregateTests`):** positive — ctor valid raises UomClassCreated with CompanyId; validator valid passes; handler happy path. negative — ctor CompanyId 0/-1 throws; Code/Name whitespace throws; validator CompanyId 0, Code empty/21, Name empty/201, Description 501 fail; deactivate handler missing entity throws InvalidOperationException. deactivation — Deactivate sets IsActive false; deactivate handler happy path (Id=5). company isolation — GetAllByCompanyAsync filters. **Uom-append Facts** (see §7b): Uom ctor with UomClassId=0 throws; Uom ctor with UomClassId=5 sets property; CreateUomCommandValidator UomClassId 0 fails when present; GetUomHandler Map includes UomClassId; CreateUomConversionHandler class-compat: both classes present and differ → DomainException; either Uom unclassified → allowed.

#### 7b. UomClassId append on Uom — canonical 7-file change spec (R22; missing any = compile break or silent null DTO field)

Verified current state (read 2026-09-24): `uoms` table has 0 live rows (psql-verified) — **zero backfill risk**; no test constructs Uom (grep over tests = 0 hits); only callsite `CreateUomHandler.cs:15` passes 5 positional args — ctor param LAST keeps it compiling.

1. **`Domain/Entities/Uom.cs`** — ctor currently `(long companyId, string code, string name, string? symbol = null, string? description = null)` (Uom.cs:17). Gains `long? uomClassId = null` **LAST** → `(long companyId, string code, string name, string? symbol = null, string? description = null, long? uomClassId = null)`. Guard: `if (uomClassId.HasValue && uomClassId <= 0) throw new DomainException("UomClassId must be greater than zero when specified.");` (Supplier.cs:31-32 precedent). Property `public long? UomClassId { get; private set; }` placed **before IsActive** (Supplier.cs:17 precedent — SupplierGroupId sits before IsActive). Assignment `UomClassId = uomClassId;` in ctor body. Existing callers (CreateUomHandler.cs:15, 5 positional args) compile unchanged.
2. **`Application/Commands/CreateUomCommand.cs`** — gains `long? UomClassId = null` LAST (after Description): `public record CreateUomCommand(long CompanyId, string Code, string Name, string? Symbol = null, string? Description = null, long? UomClassId = null) : IRequest<CreateUomResult>;`
3. **`Application/Validators/CreateUomCommandValidator.cs`** — gains `RuleFor(x => x.UomClassId).GreaterThan(0).When(x => x.UomClassId.HasValue);` (after the Description rule, CreateUomCommandValidator.cs:14).
3b. **`Application/Handlers/CreateUomHandler.cs`** — pass-through (line 15 currently constructs Uom with 5 positional args): `new Uom(command.CompanyId, command.Code, command.Name, command.Symbol, command.Description, command.UomClassId)`. Missing pass-through = silent null UomClassId (transcription-drop pattern, MEMORY:21 — same gap as G1's dropped null-guard).
4. **`Application/DTOs/UomDto.cs`** — gains `long? UomClassId` before IsActive: `public record UomDto(long Id, long CompanyId, string Code, string Name, string? Symbol, long? UomClassId, bool IsActive, string? Description);`
5. **`Application/Handlers/GetUomHandler.cs`** — Map (line 26) passes `u.UomClassId`: `=> new UomDto(u.Id, u.CompanyId, u.Code, u.Name, u.Symbol, u.UomClassId, u.IsActive, u.Description);`
6. **`Infrastructure/Persistence/Configurations/UomConfiguration.cs`** — add `builder.Property(e => e.UomClassId).HasColumnName("uom_class_id");` (before IsActive block, UomConfiguration.cs:35) + `builder.HasOne<UomClass>().WithMany().HasForeignKey(e => e.UomClassId).OnDelete(DeleteBehavior.Restrict);` (after the Company FK block, UomConfiguration.cs:45-48). Migration = **AddColumn nullable NO defaultValue** (0 live rows — zero backfill risk, R22 verified).

**CreateUomConversionHandler class-compat check (C4):** handler currently `(IUomConversionRepository repository, IUnitOfWork unitOfWork)` (CreateUomConversionHandler.cs:8-10). Gains `IUomRepository uomRepository` dependency. Logic: load both Uoms via `GetByIdAsync`; if **both** have UomClassId AND they differ → `throw new DomainException("Cannot convert between UOMs of different classes.")`. If either Uom is unclassified (null) → allow (existing UOMs have no class; blocking would break existing conversions). Rule: reject only when both classes are present and unequal. Entity unchanged (cannot validate — no data access, no nav props); validator unchanged (sync-shape only). Same-company consistency of (Uom.UomClassId, UomClass.CompanyId) is Application-layer/document-only (R12, R14).

**R1 (uom_conversions full-unique vs soft-delete — EXISTING table):** `UomConversionConfiguration.cs:24` full unique `(CompanyId, FromUomId, ToUomId)` + `Deactivate()` = deactivate→re-add same pair = DbUpdateException (the exact SupplierItem dead-end, MEMORY:263). **Decision: document-only limitation — do NOT alter the existing index in migration #19.** Why: (a) uom_conversions is an EXISTING committed table; altering its index in #19 expands migration surface and touches a parity-verify entity (DoD #23 — no modification without stated reason); (b) no Reactivate anywhere — dead-end only triggers on deactivate-then-create-new-same-pair, a rare admin flow; (c) all 8 NEW entities get partial-unique where IsActive-only, so the codebase moves forward consistently. Remediation (partial-unique HasFilter on uom_conversions) = one-line config change + migration, deferred to a future loop with user approval. **R20:** store BOTH conversion directions as explicit rows (A→B and B→A are distinct rows under the unique key) — no inverse computation, no rounding drift; document-only (no stock math in scope).

---

### 8. WarehouseLocation/Bin — table `warehouse_locations`

**Conflict resolution:** none of C1–C5 (Warehouse child). **Risks:** R3, R7, R10, R14, R26 (dispositions in §10). **Built by:** G3 slice, PLAN task 9 (WarehouseLocation/Bin vertical slice). **References:** Company, Warehouse (FKs).

**Company scope + ownership:** Company-scoped child of Warehouse. Non-nullable `long CompanyId`; FK Restrict to Company; no nav prop.

**Fields (exact):**

| # | Name | C# type | Precision/Length | Nullable | Default |
|---|------|---------|------------------|----------|---------|
| 1 | CompanyId | long | — | no | — |
| 2 | WarehouseId | long | — | no | — |
| 3 | Code | string | 20 | no | — |
| 4 | Name | string | 200 | no | — |
| 5 | IsActive | bool | — | no | true |
| 6 | Description | string? | 500 | yes | null |

**Ctor:** `(long companyId, long warehouseId, string code, string name, string? description = null)` — guards: companyId>0, warehouseId>0, Code/Name non-whitespace (DomainException). Private parameterless ctor for EF.

**Unique constraints:** `HasIndex(e => new { e.CompanyId, e.WarehouseId, e.Code }).IsUnique()` — **BankBranch precedent** `(CompanyId, BankId, Code)` (BankBranchConfiguration.cs:41-42). Full unique, master-child classification (R7; deactivate→re-add same code BLOCKED, accepted — BankBranch same).

**FKs (all OnDelete=Restrict):** Company → companies; Warehouse → warehouses (BankBranch: Company + Bank both Restrict).

**Effective-dating / IsActive / soft-delete:** No effective dating. `IsActive = true`; `Deactivate()` sets false.

**Events:** `WarehouseLocationCreated(long WarehouseLocationId, long CompanyId, DateTimeOffset OccurredOn)`.

**Port + repo behavior:** `IWarehouseLocationRepository`: `GetByIdAsync(long)`, `GetAllByCompanyAsync(long companyId)`, `AddAsync(WarehouseLocation)` (child shape).

**Command + validator:** `CreateWarehouseLocationCommand(long CompanyId, long WarehouseId, string Code, string Name, string? Description = null) : IRequest<CreateWarehouseLocationResult>`; `CreateWarehouseLocationResult(long Id)`. `DeactivateWarehouseLocationCommand(long Id)`. Validator (`CreateWarehouseLocationCommandValidator`): CompanyId/WarehouseId `GreaterThan(0)`; Code `NotEmpty().MaximumLength(20)`; Name `NotEmpty().MaximumLength(200)`; Description `MaximumLength(500).When(...)`.

**DTO + queries:** `WarehouseLocationDto(long Id, long CompanyId, long WarehouseId, string Code, string Name, bool IsActive, string? Description)`. `GetWarehouseLocationQuery(long Id)`; `GetWarehouseLocationsByCompanyQuery(long CompanyId)`.

**Controller routes:** `WarehouseLocationController` — `GET /WarehouseLocation/Index?companyId=`; `POST /WarehouseLocation/Create`; `POST /WarehouseLocation/Deactivate`.

**BankTests (`WarehouseLocationAggregateTests`):** positive — ctor valid raises WarehouseLocationCreated with CompanyId; validator valid passes; handler happy path. negative — ctor CompanyId/WarehouseId 0/-1 throws; Code/Name whitespace throws; validator CompanyId 0, WarehouseId 0, Code empty/21, Name empty/201, Description 501 fail; deactivate handler missing entity throws InvalidOperationException. deactivation — Deactivate sets IsActive false; deactivate handler happy path (Id=5). company isolation — GetAllByCompanyAsync filters.

**Scope:** **Master data only — NO stock quantity columns** (R26: quantities = stock ledger, out of scope). No bin-capacity math.

---

### 9. Open conflicts resolved — canonical citations (C1–C5)

| # | Conflict | Decision (canonical) | Rationale anchor | Consequence |
|---|----------|----------------------|------------------|-------------|
| C1 | ItemGroup vs ItemCategory | **DISTINCT ROLES** — ItemCategory keeps the self-ref classification hierarchy (exists, untouched); ItemGroup = NEW flat master (CompanyId, Code, Name, IsActive, Description) for pricing/tax/accounting/reporting grouping, **NO ParentId**; nullable `ItemGroupId` appended on Item (ctor param LAST, `HasValue && <= 0` guard, AddColumn nullable NO defaultValue) | ItemCategory.cs:11 ParentId + self-FK Restrict; Item.ItemCategoryId FK exists; Supplier.SupplierGroupId nullable-FK-append canon (Supplier.cs:23,31-32); R29 option 2 | 1 new table `item_groups` + 1 nullable AddColumn `item_group_id` on `items`; Item ctor gains `long? itemGroupId = null` LAST — existing callers compile unchanged; ItemGroup is a full master slice (GetByCodeAsync in port) |
| C2 | ItemTaxClass shape | **LINK ENTITY, TaxTypeId-only, effective-dated** — CompanyId, ItemId, TaxTypeId, EffectiveFrom (required), EffectiveTo? (nullable=indefinite), IsActive; unique `(CompanyId, ItemId, TaxTypeId, EffectiveFrom)`; 3 FKs Restrict; **NO TaxRateId, NO AccountId** | R16 option (a): TaxRate already effective-dated (TaxRate.cs:12-13) — referencing it duplicates the date axis; rate resolved at transaction time via TaxRate's own effective-date query; R8 moot (no TaxRateId column); R15: account mapping stays in TaxAccountingMapping | 1 new table `item_tax_classes`; Item unchanged; query contract (R18): ItemTaxClass active AND TaxType active AND TaxRate (by type+date) active |
| C3 | ItemSupplierPrice vs extending SupplierItem | **NEW price-bearing entity** — CompanyId, SupplierId, ItemId, UnitPrice decimal(18,2), CurrencyCode string(3), EffectiveFrom (required), EffectiveTo?, IsActive; unique `(CompanyId, SupplierId, ItemId, CurrencyCode, EffectiveFrom)`; 3 FKs Restrict; **SupplierItem untouched** | SupplierItem is a pure link (SupplierItem.cs:8-11) with partial-unique HasFilter — one row per pair vs N price versions; price is versioned data → own rows with effective dating (TaxRate precedent); PLAN.md G3 explicitly "do NOT modify SupplierItem"; R4 | 1 new table `item_supplier_prices`; SupplierItem/Supplier/Item untouched; CurrencyCode string(3) per Money VO / BankAccount.CurrencyCode precedent (R23 — scalar, not Money VO) |
| C4 | UomClass | **New master + nullable UomClassId append on Uom** — company-scoped (R12); 6-file surface (R22, §7b); class-compat check in `CreateUomConversionHandler` (Application layer), NOT entity, NOT validator | Uom has no class (Uom.cs); UomConversion stores only FromUomId/ToUomId longs (UomConversion.cs:9-10) with no nav props and Domain has no repo access — entity physically cannot validate class compatibility at construction (R12 consequence); handler already has repo access (CreateItemHandler pattern); rule: reject only when both classes present and unequal | 1 new table `uom_classes` + 1 nullable AddColumn `uom_class_id` on `uoms` (NO defaultValue); UomConversion entity/config unchanged; CreateUomConversionHandler gains compat check + 2 repo lookups |
| C5 | ValuationMethod LIFO/SpecificIdentification | **DOCUMENT-ONLY known limitation, no enum mutation** — enum stays `{ FIFO, LIFO, WeightedAverage }` exactly as committed | R19 — document BOTH facts: (a) LIFO present-but-NON-OPERATIVE (VAS 02 para 13 lists it; operative VN regime = weighted avg / specific id / FIFO per Circular 200/2014, 133/2016, 99/2025); (b) SpecificIdentification operative-but-ABSENT. Mutating breaks existing committed code/data/tests; compliance-relevant change requires user approval; master-data module only (DoD #12); PLAN.md G1 "no enum mutation without user approval". Enum stored as string — adding SpecificIdentification later is additive/migration-free; removing LIFO is breaking | Zero code change; G5 report lists both facts + remediation path (add SpecificIdentification, remove LIFO, remap rows) requiring user approval + migration |

---

### 10. Adversarial risk disposition matrix (R1–R32)

| R# | Affects | Disposition |
|----|---------|-------------|
| R1 | UomClass slice (uom_conversions) | **Documented limitation.** Existing full unique `(CompanyId, FromUomId, ToUomId)` on uom_conversions kept — no index ALTER in #19. Why: existing committed table; altering expands migration surface + touches parity-verify entity (DoD #23); no Reactivate anywhere so dead-end only on deactivate→re-add same pair (rare admin flow); all 8 NEW entities use partial-unique where IsActive-only. Remediation (HasFilter on uom_conversions) deferred to future loop with user approval |
| R2 | UomClass slice (UomConversion) | Query contract documented: conversion effective = `conversion.IsActive AND fromUom.IsActive AND toUom.IsActive`. Document-only — no conversion query exists in this module |
| R3 | ItemBarcode, ItemPriceList, ItemSupplierPrice, ItemTaxClass, ItemReorderLevel | All item-child FKs Restrict (never SetNull — SetNull precedent is for OPTIONAL JE-line dimensions, NOT item children). Child rows survive item deactivation; reads filter `Item.IsActive` |
| R4 | ItemSupplierPrice | Supplier FK Restrict; child rows survive supplier deactivation; reads filter `Supplier.IsActive` |
| R5 | PriceList + ItemPriceList | PriceList = master (full unique (CompanyId,Code), no Reactivate) — deactivate→re-add same code BLOCKED, accepted. ItemPriceList FK Restrict; reads filter `PriceList.IsActive` |
| R6 | all 8 | Zero hard-delete anywhere; no new FK from journal_entry_lines (stock ledger out of scope) |
| R7 | all 8 | Per-entity classification (§0): master full unique (CompanyId,Code) / effective-dated full unique on effective key incl. EffectiveFrom / IsActive-only partial-unique HasFilter / WarehouseLocation full unique (CompanyId, WarehouseId, Code) |
| R8 | ItemTaxClass | **Moot** — no TaxRateId column at all (C2). Unique key `(CompanyId, ItemId, TaxTypeId, EffectiveFrom)` has no nullable member |
| R9 | ItemReorderLevel | TWO partial indexes (NULL-distinct trap avoided): `(CompanyId, ItemId)` WHERE `warehouse_id IS NULL AND is_active`; `(CompanyId, ItemId, WarehouseId)` WHERE `warehouse_id IS NOT NULL AND is_active`. No full-unique triple with nullable WarehouseId |
| R10 | all 8 | Every entity gets BOTH xmin AND its unique index; no TOCTOU handler pre-checks for uniqueness |
| R11 | ItemGroup, PriceList, UomClass (masters) | GetByCodeAsync on master ports = UX pre-check only; DB unique index is the real protection |
| R12 | UomClass | Company-scoped (CompanyId + unique (CompanyId,Code) + FK Restrict). Consequence: same-company consistency of (Uom.UomClassId, UomClass.CompanyId) is Application-layer/document-only (domain ctor has only IDs) |
| R13 | ItemBarcode | Unique `(CompanyId, Barcode)` — per-company, NOT global. Cross-company GTIN duplication legal and expected |
| R14 | all child entities | Acknowledged: same-company consistency of (CompanyId, ItemId) pairs is Application-layer validation, not DB-enforced (SupplierItem precedent accepts this). No composite FKs invented |
| R15 | ItemTaxClass | No Account FK; ItemTaxClass (classification) ↔ TaxAccountingMapping (account mapping) complementary, not alternatives |
| R16 | ItemTaxClass | TaxTypeId-only (option a). Rate resolved at transaction time via TaxRate's own effective-date query. No duplicated date axis |
| R17 | (none of the 8 — InventoryAccountingConfiguration) | Stays 1:1 per company, NOT extended with item/category-scoped fields (per-item account mapping is a transaction-module concern, out of scope) |
| R18 | ItemTaxClass | Query contract: item tax resolution = ItemTaxClass active AND TaxType active AND TaxRate (resolved by type+date) active + effective window |
| R19 | (none of the 8 — InventoryValuationPolicy) | **Documented limitation (C5).** No enum mutation. Both facts documented: LIFO present-but-non-operative; SpecificIdentification operative-but-absent. Adding later = additive/migration-free (string storage); removing LIFO = breaking. Requires user approval |
| R20 | UomClass slice (UomConversion) | Store BOTH directions as explicit rows (A→B and B→A distinct under unique key) — no inverse computation, no rounding drift. Document-only (no stock math in scope) |
| R21 | ItemBarcode | Check-digit validated ONLY for BarcodeType ∈ {GTIN8, GTIN12, GTIN13, GTIN14} (length-matched); skipped entirely for Other |
| R22 | UomClass slice (Uom append) | Full 7-file surface transcribed in §7b (incl. CreateUomHandler pass-through — missing any = compile break or silent null DTO field). Live uoms table 0 rows — zero backfill risk |
| R23 | ItemPriceList, ItemSupplierPrice | Scalar decimal + string CurrencyCode(3), NOT Money VO (Money.cs:13 throws ArgumentNullException, no ISO validation). Currency format (3 uppercase) validated at Application layer |
| R24 | ItemPriceList, ItemSupplierPrice | Scalar columns, explicit names + precision: `unit_price` decimal(18,2), `currency_code` varchar(3). No OwnsOne |
| R25 | ItemReorderLevel | Threshold storage only — no min/max computation, PO suggestion, stock-on-hand math. Stock-item-only handler guard (loads Item; null-guard FIRST → `InvalidOperationException` when item not found; then `!item.IsStockItem` → DomainException) |
| R26 | WarehouseLocation | Master data only — NO stock quantity columns (quantities = stock ledger, out of scope). No bin-capacity math |
| R27 | ItemPriceList, ItemSupplierPrice | Price master data only — no discount math, no price calculation, no currency conversion |
| R28 | ItemTaxClass | Classification only — no tax calculation (calculation lives in future transaction modules per ADR-010:135-144) |
| R29 | ItemGroup | Distinct roles: ItemCategory keeps self-ref hierarchy (exists, untouched); ItemGroup = NEW flat master (no ParentId) for pricing/tax/accounting/reporting grouping. No duplicate hierarchy |
| R30 | ItemBarcode | GS1 company-prefix/registry lookups OUT of scope (external service). Check-digit validation only |
| R31 | ItemBarcode | **Documented limitation:** ServiceItem (separate `service_items` table) cannot have barcodes — Item is the only barcode target |
| R32 | all 8 (migration) | Migration #19 shape in §0: 9 CreateTable + 2 nullable AddColumn NO defaultValue + 4 HasFilter partial uniques + all FKs Restrict + xmin; check-only, never `database update` without user approval |

---

### 11. Dependency map (slice → builds → references)

| Slice (PLAN task) | Builds | References (existing entities) | Appends / touches |
|-------------------|--------|--------------------------------|-------------------|
| G2 task 2 | UomClass | Company | UomClassId on Uom (6-file surface §7b); CreateUomConversionHandler class-compat check |
| G2 task 3 | ItemGroup | Company | ItemGroupId on Item (nullable append) |
| G2 task 4 | ItemBarcode | Company, Item, Uom | — |
| G2 task 5 | PriceList + ItemPriceList | Company, PriceList, Item | — |
| G3 task 6 | ItemReorderLevel | Company, Item, Warehouse | CreateItemReorderLevelHandler gains IItemRepository |
| G3 task 7 | ItemSupplierPrice | Company, Supplier, Item | — |
| G3 task 8 | ItemTaxClass | Company, Item, TaxType | — |
| G3 task 9 | WarehouseLocation | Company, Warehouse | — |

**Existing entities referenced but NOT modified:** Item (except the two nullable-FK appends above), ItemCategory, Uom (except UomClassId append), UomConversion (entity/config unchanged; handler gains compat check), Warehouse, Supplier, SupplierItem, TaxType, TaxRate, InventoryValuationPolicy, InventoryAccountingConfiguration, InventoryAdjustmentReason.

---

## Task-Specific Research — UomClass Slice

**Date:** 2026-09-24. **Agent:** researcher (G2 executor prep). **Scope:** verify §7/§7b canonical against real files; produce executor-ready spec. All files re-read this research. READ-ONLY — zero src/ changes.

### 1. Template slice paths — ALL CONFIRMED EXIST (glob-verified 2026-09-24)

**Uom slice (append surface + UomClass master template):**

| Layer | File |
|-------|------|
| Entity | `src/SmeAccounting.Domain/Entities/Uom.cs` |
| Event | `src/SmeAccounting.Domain/Events/UomCreated.cs` |
| Port | `src/SmeAccounting.Domain/Ports/IUomRepository.cs` |
| EF config | `src/SmeAccounting.Infrastructure/Persistence/Configurations/UomConfiguration.cs` |
| Repo | `src/SmeAccounting.Infrastructure/Repositories/EfUomRepository.cs` |
| Command | `src/SmeAccounting.Application/Commands/CreateUomCommand.cs` (+ `CreateUomResult`) |
| Handler | `src/SmeAccounting.Application/Handlers/CreateUomHandler.cs` |
| Validator | `src/SmeAccounting.Application/Validators/CreateUomCommandValidator.cs` |
| Query | `src/SmeAccounting.Application/Queries/GetUomQuery.cs` (`GetUomQuery` + `GetUomsByCompanyQuery` co-located) |
| Query handler | `src/SmeAccounting.Application/Handlers/GetUomHandler.cs` |
| DTO | `src/SmeAccounting.Application/DTOs/UomDto.cs` |
| Controller | `src/SmeAccounting.Api/Controllers/UomController.cs` |
| Deactivate | `src/SmeAccounting.Application/Commands/DeactivateUomCommand.cs` + `Handlers/DeactivateUomHandler.cs` |

**Item slice (5-layer master template, RESEARCH.md Environment §2):** `Item.cs`, `ItemCreated.cs`, `IItemRepository.cs`, `ItemConfiguration.cs`, `EfItemRepository.cs`, `CreateItemCommand.cs`, `CreateItemHandler.cs`, `CreateItemCommandValidator.cs`, `GetItemQuery.cs`, `GetItemHandler.cs`, `ItemDto.cs`, `ItemController.cs` — all 12 exist.

**Test templates:** `tests/SmeAccounting.BankTests/SupplierItemAggregateTests.cs` (child/link shape) + `tests/SmeAccounting.BankTests/CustomerGroupAggregateTests.cs` (**master-entity shape — closest to UomClass**: ctor/validator/handler/deactivate/company-isolation Facts, 144 lines) + `tests/SmeAccounting.BankTests/Fakes.cs`.

### 2. Fakes.cs — current state + what must be added

Location: `tests/SmeAccounting.BankTests/Fakes.cs` (235 lines). **Current fake classes (12):** FakeBankRepository, FakePaymentMethodRepository, FakePostingReferenceRepository, FakeJournalEntryRepository, FakeOpeningBalancePeriodRepository, FakeVoucherTypeRepository, FakeDocumentNumberingSeriesRepository, FakeCustomerGroupRepository, FakeSupplierGroupRepository, FakeSupplierItemRepository, FakeUnitOfWork, FakeClock.

**ZERO Uom fakes exist** (grep `Uom|UomConversion` over BankTests = no files found — also means **no existing Uom/UomConversion tests anywhere**). Executor MUST add 3 new fakes to Fakes.cs:

| Fake | Port (verified members) | Members |
|------|------------------------|---------|
| `FakeUomClassRepository : IUomClassRepository` | §7 spec (master shape) | GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, AddAsync + `Stored` |
| `FakeUomRepository : IUomRepository` | IUomRepository.cs:5-11 | GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, AddAsync + `Stored` |
| `FakeUomConversionRepository : IUomConversionRepository` | IUomConversionRepository.cs:5-10 | GetByIdAsync, **GetByCompanyAsync** (NOT GetAllByCompanyAsync — CS0535 trap), AddAsync + `Stored` |

Missing member = CS0535 (MEMORY:269). Plain List-backed Add (NO `_nextId` counter) is correct — Uom/UomClass ctors have no own-Id>0 guard (MEMORY:269); Deactivate-happy facts set `entity.Id = 5` BEFORE AddAsync (BaseEntity.Id public setter).

### 3. §7b 6-file append — verified against real files, ZERO discrepancies

| # | File | §7b claim | Verified actual | Verdict |
|---|------|-----------|-----------------|---------|
| 1 | Uom.cs | ctor `(companyId, code, name, symbol=null, description=null)` at :17; guard `HasValue && <= 0` (Supplier.cs:31-32); property before IsActive (Supplier.cs:17) | ctor exactly at :17 ✓; property order Symbol:11, **IsActive:12**, Description:13 → UomClassId property inserts between :11 and :12 ✓; Supplier.cs:31-32 guard verbatim `if (supplierGroupId.HasValue && supplierGroupId <= 0) throw new DomainException("SupplierGroupId must be greater than zero when specified.");` ✓ | MATCH |
| 2 | CreateUomCommand.cs | gains `long? UomClassId = null` LAST after Description | record :5-10 `(CompanyId, Code, Name, Symbol=null, Description=null)` ✓ | MATCH |
| 3 | CreateUomCommandValidator.cs | add `RuleFor(x => x.UomClassId).GreaterThan(0).When(x => x.UomClassId.HasValue);` after Description rule :14 | Description rule at :14 ✓; existing nullable rules use `.When(x => !string.IsNullOrWhiteSpace(x.Symbol))` style — for nullable long use `When(x => x.UomClassId.HasValue)` per §7b | MATCH |
| 4 | UomDto.cs | gains `long? UomClassId` before IsActive | record :3-10 `(Id, CompanyId, Code, Name, Symbol, IsActive, Description)` ✓ | MATCH |
| 5 | GetUomHandler.cs | Map :26 passes `u.UomClassId` before `u.IsActive` | Map at :25-26 `new UomDto(u.Id, u.CompanyId, u.Code, u.Name, u.Symbol, u.IsActive, u.Description)` ✓ | MATCH |
| 6 | UomConfiguration.cs | `Property(e => e.UomClassId).HasColumnName("uom_class_id")` before IsActive block :35; `HasOne<UomClass>().WithMany().HasForeignKey(e => e.UomClassId).OnDelete(Restrict)` after Company FK block :45-48 | IsActive block :35-36 ✓; Company FK block :45-48 ✓; Symbol block ends :33 → UomClassId Property inserts after :33 | MATCH |

**Callsite check:** CreateUomHandler.cs:15 `new Uom(request.CompanyId, request.Code, request.Name, request.Symbol, request.Description)` — 5 positional args, compiles unchanged with 6th defaulted ✓. No other Uom ctor callsites (grep tests = 0; only CreateUomHandler constructs Uom).

**Flags (not discrepancies, executor notes):**
- **UomController NOT in §7b surface** — controller binds form params individually (`Create(long companyId, string code, string name, string? symbol, string? description, ...)` :30) and constructs the command with 5 args (:34) — compiles unchanged. If UI must SET UomClassId on Uom creation, controller needs `long? uomClassId` param + pass-through — **out of §7b scope, optional**.
- **Deactivate handler pattern split:** DeactivateUomHandler.cs:15 returns `new DeactivateUomResult(false)` for missing entity (OLD pattern); DeactivateCustomerGroupHandler.cs:17-18 THROWS `InvalidOperationException` (NEW pattern). §7 UomClass test list says "deactivate handler missing entity throws InvalidOperationException" → **follow CustomerGroup throw pattern**, NOT Uom's false-return. DeactivateUomClassCommand shape per §7 = `(long Id)` (Uom-style param name, CustomerGroup-style throw).
- **Deactivate result shape:** DeactivateCustomerGroupCommand returns empty `DeactivateCustomerGroupResult` record (no bool) — use same for UomClass (matches throw-on-missing; bool Success is meaningless when missing throws).

### 4. UomConversion class-compat check — handler-only confirmed

- **Entity cannot validate** — confirmed: UomConversion.cs has only scalar longs (CompanyId/FromUomId/ToUomId/Factor/IsActive), no nav props, no repo access. Class-compat check lands in **CreateUomConversionHandler only** (Application layer). Validator unchanged (sync-shape only).
- **Handler shape:** CreateUomConversionHandler.cs:8-10 `(IUomConversionRepository repository, IUnitOfWork unitOfWork)` → gains `IUomRepository uomRepository`. Check inserts BEFORE `var conv = new UomConversion(...)` at :15. **IUomRepository already DI-registered** (DependencyInjection.cs:59) — NO DI change for the handler.
- **Existing UomConversion tests: NONE** (grep over BankTests = zero Uom matches) — nothing to break. New class-compat Facts are the FIRST conversion-handler tests.
- **Null-Uom edge case NOT specified in §7b:** canonical rule = "reject only when both classes present and unequal". If `GetByIdAsync` returns null for either Uom, `uom.UomClassId` would NRE. **Recommendation: null-safe allow** — `if (fromUom?.UomClassId is not null && toUom?.UomClassId is not null && fromUom.UomClassId != toUom.UomClassId) throw new DomainException("Cannot convert between UOMs of different classes.");` — treats not-found as unclassified → allowed (behavior-preserving: today a dangling FK fails at SaveChanges via Restrict; same outcome, no NRE). Alternative (throw InvalidOperationException on null) deviates from canonical rule. **Executor: pick null-safe allow; verifier: check no NRE path.**

### 5. DbContext + DI insertion points (verified line numbers)

**SmeAccountingDbContext.cs:**
- Uom DbSet at **:36** `public DbSet<Uom> Uoms => Set<Uom>();` — UomClass DbSet inserts adjacent (:36-37 area) OR Ignore-only.
- UomCreated Ignore at **:92** — `modelBuilder.Ignore<UomClassCreated>();` inserts adjacent (:92-93 area).
- **Style:** BOTH coexist. Uom/Item/Warehouse = DbSet style (`_context.Uoms` in repo); partners (CustomerGroup etc.) = Ignore-only + `_context.Set<T>()` in repo (EfCustomerGroupRepository.cs:16,22,28,37). **Recommendation: DbSet style** (UomClass is a master entity like Uom/Item; consistent with parent Uom). Either passes arch/build; migration output identical. If DbSet style: repo uses `_context.UomClasses`; if Ignore-only: `_context.Set<UomClass>()`.
- `using SmeAccounting.Domain.Events;` already present (:3) — no using change for Ignore<UomClassCreated>.

**DependencyInjection.cs:**
- `IUomRepository` AddScoped at **:59** — `services.AddScoped<IUomClassRepository, EfUomClassRepository>();` inserts adjacent (:59-60 area). Re-read file before edit (parallel-task race, MEMORY:265).

### 6. Edge cases for BankTests (from §7 + §7b lists — all confirmed implementable)

| Fact | Construction | Assert |
|------|-------------|--------|
| Uom ctor UomClassId=0 throws | `new Uom(1, "KG", "Kilogram", uomClassId: 0)` | `Assert.Throws<DomainException>` |
| Uom ctor UomClassId=5 sets property | `new Uom(1, "KG", "Kilogram", uomClassId: 5)` | `Assert.Equal(5, uom.UomClassId)` |
| Validator UomClassId 0 fails when present | `new CreateUomCommand(1, "KG", "Kilogram", UomClassId: 0)` | `Assert.False(result.IsValid)` |
| Validator UomClassId null passes | `new CreateUomCommand(1, "KG", "Kilogram")` | `Assert.True(result.IsValid)` |
| GetUomHandler Map includes UomClassId | FakeUomRepository with Uom (UomClassId=5, `uom.Id = 5`), `handler.Handle(new GetUomQuery(5))` | `Assert.Equal(5, dto!.UomClassId)` |
| Class-compat both-classes-differ → DomainException | FakeUomRepository: Uom A (Id=5, class 1), Uom B (Id=6, class 2); `CreateUomConversionHandler(repo, uomRepo, uow).Handle(new CreateUomConversionCommand(1, 5, 6, 2m))` | `Assert.ThrowsAsync<DomainException>`; SaveCalledCount == 0 |
| Class-compat both-same-class → allowed | Uom A (Id=5, class 1), Uom B (Id=6, class 1) | no throw; SaveCalledCount == 1 |
| Class-compat either-unclassified → allowed | Uom A (Id=5, class null), Uom B (Id=6, class 1) — and both-null | no throw; SaveCalledCount == 1 |
| UomClass master Facts (§7) | CustomerGroupAggregateTests shape | ctor valid/0/-1/empty-code/empty-name; Deactivate; validator valid/0/empty/overlength; Create handler happy path; Deactivate missing throws InvalidOperationException; Deactivate happy path (Id=5); GetAllByCompanyAsync filters |

Note: conversion Facts need distinct Uom Ids (5/6) — UomConversion ctor guards `fromUomId == toUomId` throws (:21). Uom Ids set via public setter (`uom.Id = 5`) before AddAsync to FakeUomRepository.

### 7. New-file list for the slice (executor scope)

**New (14 files):** Domain — `UomClass.cs`, `UomClassCreated.cs` (UomCreated.cs:3-17 shape: `(long UomClassId, long CompanyId, DateTimeOffset OccurredOn)`), `IUomClassRepository.cs` (4 members, master shape); Infrastructure — `UomClassConfiguration.cs` (ToTable("uom_classes"), unique (CompanyId, Code), Company FK Restrict, xmin, Code 20/Name 200/Description 500), `EfUomClassRepository.cs`; Application — `CreateUomClassCommand.cs` (+`CreateUomClassResult(long Id)`), `DeactivateUomClassCommand.cs` (+empty result), `CreateUomClassCommandValidator.cs`, `GetUomClassQuery.cs` (+`GetUomClassesByCompanyQuery`), `CreateUomClassHandler.cs`, `DeactivateUomClassHandler.cs` (throw-on-missing), `GetUomClassHandler.cs`, `UomClassDto.cs`; Api — `UomClassController.cs` (UomController.cs:9-53 shape); Tests — `UomClassAggregateTests.cs`.

**Modified (7 files):** Uom.cs, CreateUomCommand.cs, CreateUomCommandValidator.cs, UomDto.cs, GetUomHandler.cs, UomConfiguration.cs (§7b 6-file surface) + CreateUomConversionHandler.cs (class-compat check). **Modified (2 wiring):** SmeAccountingDbContext.cs, DependencyInjection.cs.

**NO migration in G2** (PLAN: G2/G3 code+tests only; uom_classes table + uom_class_id AddColumn land in G4 migration #19). Build must stay 0/0 with UomConfiguration referencing UomClass — entity exists, compiles.

**Commit hygiene:** stage ONLY the 23 files above; business-partners WIP (~69 files, confirmed still uncommitted via git status) must stay unstaged. Never `git add -A`.

---

## Task-Specific Research — ItemGroup Slice

**Date:** 2026-09-24. **Author:** researcher (G2 batch). **Task:** PLAN task 3 — ItemGroup vertical slice + nullable ItemGroupId append on Item. **Source:** canonical §0/§1 (RESEARCH.md:622-687) verified against actual source files (all re-read this research). **Status:** executor-ready spec.

### 1. Template slice paths — confirmed present

| Template | Files (all exist) | Role for ItemGroup |
|----------|-------------------|--------------------|
| **Uom slice (flat-master template — COPY THIS)** | `Domain/Entities/Uom.cs`, `Events/UomCreated.cs`, `Ports/IUomRepository.cs`, `Infrastructure/Persistence/Configurations/UomConfiguration.cs`, `Infrastructure/Repositories/EfUomRepository.cs`, `Application/Commands/CreateUomCommand.cs`, `Handlers/CreateUomHandler.cs`, `Handlers/GetUomHandler.cs`, `Handlers/DeactivateUomHandler.cs`, `Queries/GetUomQuery.cs`, `Validators/CreateUomCommandValidator.cs`, `DTOs/UomDto.cs`, `Api/Controllers/UomController.cs` | Flat master: CompanyId+Code+Name+IsActive+Description, unique (CompanyId,Code), Company FK Restrict, xmin. ItemGroup = Uom minus Symbol |
| **Item slice (5-layer pattern)** | `Domain/Entities/Item.cs`, `Events/ItemCreated.cs`, `Ports/IItemRepository.cs`, `Configurations/ItemConfiguration.cs`, `Repositories/EfItemRepository.cs`, `Commands/CreateItemCommand.cs`, `Commands/DeactivateItemCommand.cs`, `Handlers/CreateItemHandler.cs`, `Handlers/GetItemHandler.cs`, `Handlers/DeactivateItemHandler.cs`, `Queries/GetItemQuery.cs`, `Validators/CreateItemCommandValidator.cs`, `DTOs/ItemDto.cs`, `Api/Controllers/ItemController.cs` | CQRS shape, command/result records, controller routes, repo behavior |
| **ItemCategory slice (self-ref — DO NOT copy ParentId)** | `Domain/Entities/ItemCategory.cs`, `Configurations/ItemCategoryConfiguration.cs`, `Ports/IItemCategoryRepository.cs`, `Handlers/GetItemCategoryHandler.cs`, `Api/Controllers/ItemCategoryController.cs` | Port shape (GetByCodeAsync present — master shape), query-handler shape. **ParentId + self-HasOne at ItemCategoryConfiguration.cs:24 are the C1 exclusion** |
| **SupplierGroup slice (test template — COPY THIS)** | `tests/SmeAccounting.BankTests/SupplierGroupAggregateTests.cs`, `CustomerGroupAggregateTests.cs`, `Fakes.cs` | 14-Fact flat-master test file: ctor/validator/handler/deactivate, Id=5-before-AddAsync, SaveCalledCount==1, throw-on-missing |

**⚠️ STALE REFERENCE:** AGENTS.md says "Template to copy: ... `tests/SmeAccounting.BankTests/ItemAggregateTests.cs`" — **that file does NOT exist** (grep over tests/ = 0 hits for ItemAggregateTests/UomAggregateTests). Use `SupplierGroupAggregateTests.cs` as the test template.

### 2. ItemGroupId append on Item — verified per file (7-file surface)

**Item ctor param count NOW: 8** — `Item.cs:20` `(long companyId, string code, string name, bool isStockItem, bool isServiceItem, long? itemCategoryId = null, long? uomId = null, string? description = null)`. Append → 9 params, `long? itemGroupId = null` LAST.

| # | File | Verified current state | Change (canon §1 + this verification) |
|---|------|------------------------|----------------------------------------|
| 1 | `Domain/Entities/Item.cs` | Property: IsServiceItem :14, IsActive :15, Description :16. Ctor :20-38, guards single-line style :22-26, assignments :28-35, event :37 | Property `public long? ItemGroupId { get; private set; }` inserted **between :14 (IsServiceItem) and :15 (IsActive)** — "before IsActive" per Supplier.cs:17 precedent (SupplierGroupId sits directly before IsActive). Ctor param LAST `long? itemGroupId = null`. Guard after :26: `if (itemGroupId.HasValue && itemGroupId <= 0) throw new DomainException("ItemGroupId must be greater than zero when specified.");` (Supplier.cs:31-32 message style; Item.cs uses single-line guard style — either compiles). Assignment `ItemGroupId = itemGroupId;` after :35 (`Description = description;`) |
| 2 | `Application/Commands/CreateItemCommand.cs` | :5-13, 8 params, Description LAST :13 | Append `long? ItemGroupId = null` after Description |
| 3 | `Application/Validators/CreateItemCommandValidator.cs` | :10-16, no ItemGroupId rule | Add `RuleFor(x => x.ItemGroupId).GreaterThan(0).When(x => x.ItemGroupId.HasValue);` — §7b UomClassId rule shape (RESEARCH.md:990-1006), matches ItemBarcode UomId rule precedent |
| 4 | `Application/Handlers/CreateItemHandler.cs` | :13 `new Item(request.CompanyId, ..., request.Description)` — 8 positional args | **MUST append `request.ItemGroupId` as 9th arg — canon §1 does NOT list this file; without it the value silently drops (compiles unchanged, null always). DISCREPANCY #1** |
| 5 | `Application/DTOs/ItemDto.cs` | :3-13: Id, CompanyId, Code, Name, ItemCategoryId, UomId, IsStockItem, IsServiceItem :11, IsActive :12, Description :13 | Insert `long? ItemGroupId` **between :11 (IsServiceItem) and :12 (IsActive)** — before IsActive, matching entity order |
| 6 | `Application/Handlers/GetItemHandler.cs` | :25 Map: `new ItemDto(i.Id, i.CompanyId, i.Code, i.Name, i.ItemCategoryId, i.UomId, i.IsStockItem, i.IsServiceItem, i.IsActive, i.Description)` | Insert `i.ItemGroupId` between `i.IsServiceItem` and `i.IsActive` |
| 7 | `Infrastructure/Persistence/Configurations/ItemConfiguration.cs` | Column props :14-22; HasOne Company :24, ItemCategory :25, Uom :26; unique :28; xmin :30 | Column `builder.Property(e => e.ItemGroupId).HasColumnName("item_group_id");` between :20 (IsServiceItem) and :21 (IsActive); `builder.HasOne<ItemGroup>().WithMany().HasForeignKey(e => e.ItemGroupId).OnDelete(DeleteBehavior.Restrict);` after :26 (Uom HasOne) |

**DISCREPANCY #1 (canon gap):** §1 Item append lists only entity + config + migration — the full surface is **7 files** (above). Same gap exists in §7b (6-file UomClassId list misses `CreateUomHandler.cs:15` pass-through — silent null risk). Executor: update CreateItemHandler.cs:13. Verifier: check ItemGroupId reaches the entity (handler fact).

**DISCREPANCY #2 (controller, beyond canon):** `ItemController.cs:8` Create takes `(companyId, code, name, isStockItem, isServiceItem, itemCategoryId, uomId, description, ct)` and builds the command with 8 positional args — compiles unchanged after append, but ItemGroupId is then unreachable from the Item create form. Canon §1 is silent on the controller. **Recommendation:** add `long? itemGroupId` param to ItemController.Create + pass to command (matches existing itemCategoryId/uomId flow, 2-token change). Flag to auditor — beyond-canon addition, or leave as documented limitation (append usable via direct command only). §7b has the same question for UomController.

**DISCREPANCY #3 (deactivate behavior — do NOT copy Item):** `DeactivateItemHandler.cs:13` returns `DeactivateItemResult(false)` on missing entity. Canon §1 says ItemGroup deactivate handler **throws InvalidOperationException** on missing (SupplierGroup precedent, `DeactivateSupplierGroupHandler.cs:17-18`). Command shape stays Item-style: `DeactivateItemGroupCommand(long Id)` + `DeactivateItemGroupResult(bool Success)` (DeactivateItemCommand.cs shape — NOT SupplierGroup's `long SupplierGroupId` + bare result). Executor: throw on missing; test asserts `Assert.ThrowsAsync<InvalidOperationException>`.

### 3. C1 reconciliation — ItemGroup vs ItemCategory (no overlap, no hierarchy validation)

Verified `ItemCategory.cs`: ParentId :11 (nullable self-ref), ctor `(companyId, code, name, parentId = null, description = null)` :17, self-HasOne at `ItemCategoryConfiguration.cs:24`. **ItemGroup design has NO ParentId** (fields: CompanyId, Code, Name, IsActive, Description — §1 :655-663). Distinct roles: ItemCategory = classification hierarchy (self-ref); ItemGroup = flat grouping master. Item carries both nullable FKs independently (ItemCategoryId :11, new ItemGroupId) — no conflict, no shared index. **No hierarchy/cycle validation needed for ItemGroup** — no ParentId, no self-ref in ctor or validator. C1 confirmed against source.

### 4. DbContext + DI insertion points (exact lines, re-read this research)

**`Infrastructure/Persistence/SmeAccountingDbContext.cs`:**
- DbSet: `public DbSet<Item> Items => Set<Item>();` at **:40**, `ServiceItem` :41. Insert `public DbSet<ItemGroup> ItemGroups => Set<ItemGroup>();` **after :40** (adjacent to Items — DbSet style, matches Item/Uom; partners' Ignore-only style not used here).
- Ignore: `modelBuilder.Ignore<ItemCreated>();` at **:96**, `ServiceItemCreated` :97. Insert `modelBuilder.Ignore<ItemGroupCreated>();` **after :96**.

**`Infrastructure/DependencyInjection.cs`:**
- `services.AddScoped<IItemRepository, EfItemRepository>();` at **:63**, `IServiceItemRepository` :64. Insert `services.AddScoped<IItemGroupRepository, EfItemGroupRepository>();` **after :63**.

Re-read both files before editing (parallel-task race, MEMORY:265). No migration for this task (G4 consolidated `AddInventoryModule03` carries the `item_group_id` AddColumn + item_groups CreateTable — PLAN task 3 says NO migration; build stays green because EF model drift is not a build-time check).

### 5. New-file list (13 files + 2 Fakes additions + 7 edits + 2 wiring)

**Domain:** `Entities/ItemGroup.cs` (ctor `(long companyId, string code, string name, string? description = null)` — Uom shape minus Symbol; guards companyId>0, Code/Name non-whitespace, DomainException; private parameterless ctor; Deactivate()); `Events/ItemGroupCreated.cs` (ItemCreated.cs shape: class : DomainEvent, `ItemGroupCreated(long itemGroupId, long companyId, DateTimeOffset occurredOn)`); `Ports/IItemGroupRepository.cs` (4 members: GetByIdAsync, GetByCodeAsync(code, companyId), GetAllByCompanyAsync, AddAsync — IItemCategoryRepository shape).
**Infrastructure:** `Configurations/ItemGroupConfiguration.cs` (UomConfiguration shape: table `item_groups`, snake_case columns, unique `(CompanyId, Code)` :42-43, Company HasOne Restrict :45-48, xmin :50-52); `Repositories/EfItemGroupRepository.cs` (EfItemRepository shape: tracked GetById/GetByCode, `AsNoTracking().Where(CompanyId).OrderBy(Code)` GetAllByCompany, AddAsync delegates).
**Application:** `Commands/CreateItemGroupCommand.cs` (+`CreateItemGroupResult(long Id)` co-located); `Commands/DeactivateItemGroupCommand.cs` (+`DeactivateItemGroupResult(bool Success)`); `Handlers/CreateItemGroupHandler.cs` (CreateItemHandler shape); `Handlers/DeactivateItemGroupHandler.cs` (**SupplierGroup throw-on-missing shape**, returns `new DeactivateItemGroupResult(true)`); `Handlers/GetItemGroupHandler.cs` (GetItemCategoryHandler shape — one class implements both queries, private static Map); `Queries/GetItemGroupQuery.cs` (`GetItemGroupQuery(long Id) : IRequest<ItemGroupDto?>` + `GetItemGroupsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ItemGroupDto>>` co-located); `Validators/CreateItemGroupCommandValidator.cs` (CompanyId GreaterThan(0); Code NotEmpty().MaximumLength(20); Name NotEmpty().MaximumLength(200); Description MaximumLength(500).When(!IsNullOrWhiteSpace)); `DTOs/ItemGroupDto.cs` (`(long Id, long CompanyId, string Code, string Name, bool IsActive, string? Description)` — UomDto shape).
**Api:** `Controllers/ItemGroupController.cs` (ItemController.cs:7-13 shape: Index/Create/Deactivate, ValidationException → ModelState).
**Tests:** `tests/SmeAccounting.BankTests/ItemGroupAggregateTests.cs` (new); `Fakes.cs` += `FakeItemGroupRepository` (4 members, FakeSupplierGroupRepository shape) + `FakeItemRepository` (4 members, IItemRepository shape — needed for the GetItemQuery Map fact).

### 6. BankTests edge cases (canon §1 list → SupplierGroupAggregateTests template, 14 + 4 append Facts)

ItemGroup facts (SupplierGroupAggregateTests.cs 1:1 — 14 Facts):
1. Ctor valid raises ItemGroupCreated with CompanyId (assert `Assert.Single(group.DomainEvents.OfType<ItemGroupCreated>())`, evt.CompanyId == 1)
2. Ctor CompanyId 0 throws DomainException
3. Ctor CompanyId -1 throws DomainException
4. Ctor Code whitespace throws (string.Empty)
5. Ctor Name whitespace throws ("  ")
6. Deactivate sets IsActive false
7. Validator valid passes
8. Validator CompanyId 0 fails
9. Validator Code empty fails
10. Validator Name empty fails
11. Validator over-length fails (Code 21 / Name 201 / Description 501 — one Fact, three asserts, SupplierGroup :94-102 shape)
12. CreateItemGroupHandler happy path adds + saves (SaveCalledCount==1, `Assert.Equal(repository.Stored[0].Id, result.Id)`)
13. DeactivateItemGroupHandler missing entity throws InvalidOperationException (Id 999)
14. DeactivateItemGroupHandler happy path deactivates + saves (**`group.Id = 5` BEFORE AddAsync** — BaseEntity.Id public setter; SaveCalledCount==1)
15. Company isolation: GetAllByCompanyAsync returns only requested-company rows (repo-level fact — seed two groups CompanyId 1 and 2, assert filter)

Item-append Facts (same file, 4 Facts — **trap: `isStockItem=true` requires `uomId` (Item.cs:26 guard); use `new Item(1, "ITM1", "Item One", false, true, itemGroupId: 5)` or pass `uomId: 1`**):
16. Item ctor ItemGroupId=0 throws DomainException (`itemGroupId: 0`)
17. Item ctor ItemGroupId=5 sets ItemGroupId (assert `item.ItemGroupId == 5`)
18. CreateItemCommandValidator ItemGroupId 0 fails when present (`ItemGroupId: 0`); null passes (covered by existing valid fact)
19. GetItemQuery Map includes ItemGroupId — needs **FakeItemRepository** in Fakes.cs: seed `new Item(1, "ITM1", "Item One", false, true, itemGroupId: 5)` with `item.Id = 5`, AddAsync, `new GetItemHandler(repo).Handle(new GetItemQuery(5), ...)` → `result!.ItemGroupId == 5`

Explicit `using SmeAccounting.Application.Handlers;` required (internal handlers, CS0246). Fakes must implement the exact port members or CS0535.

### 7. Verification criteria (verifier)

- Build 0 warnings / 0 errors (`dotnet build SmeAccounting.sln`); arch 22/22; BankTests ≥ 115 + 18 new Facts (115 baseline, MEMORY:271).
- ItemGroupId reaches entity end-to-end: CreateItemHandler.cs:13 passes `request.ItemGroupId` (Fact 17/19 prove it).
- Item ctor still 9 params, ItemGroupId LAST — existing Item callers compile unchanged (CreateItemHandler was the only callsite; controller compiles unchanged).
- DbContext: DbSet after :40 + Ignore after :96; DI: AddScoped after :63 — adjacent placement, no other lines touched.
- ItemConfiguration: column + `HasOne<ItemGroup>()...OnDelete(Restrict)` — never Cascade/SetNull.
- Deactivate handler THROWS on missing (Fact 13) — not Item's return-false.
- No migration scaffolded (G4 owns it); no `git add -A`; only ItemGroup-slice + Item-append files staged (business-partners WIP untouched).
- ItemGroup entity has NO ParentId (C1); no hierarchy validation anywhere.

---

## Task-Specific Research — PriceList Slice

**Date:** 2026-09-24. **Author:** researcher (G2 batch). **Task:** PLAN task 5 — PriceList + ItemPriceList vertical slice. **Source of truth:** "## Design Decisions (G1)" §3 (RESEARCH.md:737-818) + §0 canon (:622-645). All cited files re-read this research. **READ-ONLY** — zero src/ changes.

### 1. Two entities, ONE slice — CONFIRMED

PriceList (master) + ItemPriceList (child) = ONE executor task, adjacent files, one commit. PLAN.md:19 task 5. Design §3a + §3b both under "Built by: G2 slice, PLAN task 5".

**Template paths (verified on disk):**

| Role | Template | Files |
|------|----------|-------|
| PriceList (flat master) | Uom slice | `Domain/Entities/Uom.cs`, `Infrastructure/Persistence/Configurations/UomConfiguration.cs`, `Infrastructure/Repositories/EfUomRepository.cs`, `Application/Commands/CreateUomCommand.cs`, `Application/Validators/CreateUomCommandValidator.cs`, `Application/DTOs/UomDto.cs`, `Application/Queries/GetUomQuery.cs`, `Application/Handlers/GetUomHandler.cs`, `Api/Controllers/UomController.cs` |
| PriceList port (4-member master) | ICustomerGroupRepository shape | `Domain/Ports/ICustomerGroupRepository.cs`; fake = `Fakes.cs:158-178` (FakeCustomerGroupRepository) |
| ItemPriceList (child, effective-dated) | SupplierItem (port/child shape) + TaxRate (effective-dating/unique) + SupplierItemConfiguration (3-FK config) | `Domain/Entities/SupplierItem.cs` + `Domain/Entities/TaxRate.cs`; `Infrastructure/Persistence/Configurations/SupplierItemConfiguration.cs` + `TaxRateConfiguration.cs`; `Domain/Ports/ISupplierItemRepository.cs` (3 members); `Application/Commands/CreateSupplierItemCommand.cs` + `DeactivateSupplierItemCommand.cs`; `Application/Handlers/CreateSupplierItemHandler.cs` + `DeactivateSupplierItemHandler.cs`; `Application/DTOs/SupplierItemDto.cs`; `Application/Queries/GetSupplierItemQuery.cs`; `Api/Controllers/SupplierItemController.cs`; `tests/SmeAccounting.BankTests/SupplierItemAggregateTests.cs` (child test template, 15 Facts) |
| ItemPriceList unique (versioning key) | TaxRateConfiguration.cs:46-47 | `HasIndex(e => new { e.CompanyId, e.TaxTypeId, e.RateValue, e.EffectiveFrom }).IsUnique()` — full unique incl EffectiveFrom |
| ItemPriceList effective dating | TaxRate.cs:12-13 | `DateOnly EffectiveFrom` + `DateOnly? EffectiveTo` (nullable = indefinite) |
| BankBranch (CompanyId, BankId, Code) | NOT the ItemPriceList template | BankBranch is the WarehouseLocation template (G3 task 8), not this slice |

**Best child template verdict:** ItemPriceList = **SupplierItem port shape (3 members, no GetByCodeAsync) + TaxRate effective-dating/unique shape + SupplierItemConfiguration 3-FK Restrict config shape**. BankBranch is parent/child master (Code-bearing) — wrong shape for a price row.

### 2. Currency handling — string codes CONFIRMED (design §3b correct)

- **ExchangeRate.cs:9-11** — `string FromCurrencyCode` / `string ToCurrencyCode` (NOT FK to Currency entity). **ExchangeRate.cs:40-41** — `ToUpperInvariant()` normalization in domain ctor. This is the exact precedent the design cites.
- **Money.cs:13** — `?? throw new ArgumentNullException` + no ISO validation → R23/R24 confirmed: scalar `decimal` + `string CurrencyCode(3)`, NOT the Money VO.
- **Currency.cs** — entity exists (standalone master, `ArgumentException` legacy guard at :22-23) but NO entity in the codebase FKs to it for codes. `Company.FunctionalCurrencyCode` is string (global MEMORY:67). `BankAccount.CurrencyCode` is `string?` (deep-dive :400). **Design §3b string CurrencyCode(3) = codebase-consistent.**
- **No FK to currencies table** anywhere for price/rate codes. Do NOT invent one.

### 3. ⚠️ CurrencyCode guard contradiction in canonical §3b — RESOLVED (Option A)

Canonical §3b BankTests (:814) lists "currencyCode ... lowercase throws" among **ctor** negatives, but the same block's ctor guard (:792) says "currencyCode 3 chars non-whitespace (normalize `ToUpperInvariant()`, ExchangeRate.cs:40 precedent)" and the positive list says "currencyCode normalized to uppercase". Lowercase 3-char input cannot both normalize AND throw.

**Resolution — Option A (follow deep-dive + precedent + sibling block):**
- Deep-dive source (:518): "currencyCode 3 chars non-whitespace (normalize ToUpperInvariant())" — lowercase accepted, normalized.
- G3 sibling block §5 ItemSupplierPrice (:907) already corrected the same list to "currencyCode **invalid** throws" — NOT "lowercase". The §3b "lowercase" is the transcription outlier (MEMORY:21 transcription-drop pattern).
- R23 (:1086): "Currency format (3 uppercase) validated at **Application layer**" — lowercase rejection belongs to the validator, not the ctor.
- ExchangeRate.cs:40-41: normalize, never reject lowercase.

**Executor must implement:** ctor guard = `string.IsNullOrWhiteSpace(currencyCode)` → DomainException + `currencyCode.Length != 3` → DomainException; then `CurrencyCode = currencyCode.ToUpperInvariant()`. Ctor-negative tests = empty / 2-char / 4-char. Validator-negative test = lowercase (`Matches("^[A-Z]{3}$")` rejects). Positive test "currencyCode normalized to uppercase" = pass `"usd"` → assert `"USD"`. Document the deviation from the literal "lowercase throws" line in the commit/STATUS (auditor-caught transcription inconsistency — same failure mode as G1's dropped null-guard, MEMORY:21).

### 4. Validator patterns

- **Cross-field Must precedent:** `CreateUomConversionCommandValidator.cs:14` — `RuleFor(x => x).Must(x => x.FromUomId != x.ToUomId).WithMessage(...)`; also `CreateInventoryAccountingConfigurationCommandValidator.cs:10`. Design's `RuleFor(x => x).Must(x => !x.EffectiveTo.HasValue || x.EffectiveTo >= x.EffectiveFrom).WithMessage("EffectiveTo must be null or on/after EffectiveFrom.")` follows this exact shape.
- **Currency string rule:** `NotEmpty().Length(3).Matches("^[A-Z]{3}$")` — NO existing validator precedent in codebase (ExchangeRate has no CQRS slice — entity + repo only). Rule is new but locked by design §3b :808 + global MEMORY:15.
- **Domain guard effectiveTo:** TaxRate ctor (:19-46) does NOT validate effectiveTo — the ItemPriceList ctor guard "effectiveTo null-or-on/after-effectiveFrom (DomainException)" is design-mandated NEW (both domain + validator, per :792/:808).
- **UnitPrice >= 0:** TaxRate.cs:32-33 `rateValue < 0` guard precedent.
- **Validator style:** English messages, `GreaterThan(0).WithMessage("...")` (CreateSupplierItemCommandValidator.cs:10-17 shape).

### 5. DbContext + DI insertion points (exact, verified)

**SmeAccountingDbContext.cs** (140 lines):
- DbSets :10-54 — insert after **line 40** (`public DbSet<Item> Items => Set<Item>();`): `public DbSet<PriceList> PriceLists => Set<PriceList>();` + `public DbSet<ItemPriceList> ItemPriceLists => Set<ItemPriceList>();` (item-adjacent; DbSet style is `=> Set<T>()` everywhere).
- Ignore :61-113 — insert after **line 96** (`modelBuilder.Ignore<ItemCreated>();`): `modelBuilder.Ignore<PriceListCreated>();` + `modelBuilder.Ignore<ItemPriceListCreated>();`. **Both DbSet AND Ignore mandatory** (MEMORY:110).

**DependencyInjection.cs** — insert after **line 63** (`services.AddScoped<IItemRepository, EfItemRepository>();`): `services.AddScoped<IPriceListRepository, EfPriceListRepository>();` + `services.AddScoped<IItemPriceListRepository, EfItemPriceListRepository>();`. Re-read shared files before edit (parallel-task race, MEMORY:265).

### 6. Fakes.cs — what's needed

- **FakePriceListRepository** — 4 members (master shape): `GetByIdAsync(long)`, `GetByCodeAsync(string, long)`, `GetAllByCompanyAsync(long)`, `AddAsync(PriceList)` + `Stored` — copy FakeCustomerGroupRepository (Fakes.cs:158-178) verbatim shape.
- **FakeItemPriceListRepository** — 3 members (child shape): `GetByIdAsync(long)`, `GetAllByCompanyAsync(long)`, `AddAsync(ItemPriceList)` + `Stored` — copy FakeSupplierItemRepository (Fakes.cs:202-219) verbatim shape. **NO GetByCodeAsync** (ISupplierItemRepository.cs:5-10 exact — missing member = CS0535, MEMORY:269).
- Existing item/supplier fakes: FakeSupplierItemRepository (child template) + FakeCustomerGroupRepository/FakeSupplierGroupRepository (master template) already in Fakes.cs. **No FakeItemRepository/FakeUomRepository exist and none are needed** — handlers inject only the slice's own repo + IUnitOfWork (CreateSupplierItemHandler.cs:8-10 shape).
- FakeUnitOfWork (Fakes.cs:221-230) reused — `SaveCalledCount` assertion pattern.
- InternalsVisibleTo("SmeAccounting.BankTests") confirmed at Application.csproj:14 — internal handlers testable, zero csproj edits.

### 7. BankTests edge cases (from §3 lists, verified against templates)

**PriceListAggregateTests** (master — CustomerGroupAggregateTests shape): positive — ctor valid raises PriceListCreated with CompanyId; validator valid passes; handler happy path adds + saves (SaveCalledCount==1). negative — ctor CompanyId 0/-1 throws DomainException; Code/Name whitespace throws; validator CompanyId 0, Code empty/21, Name empty/201, Description 501 fail; deactivate handler missing entity throws **InvalidOperationException** (DeactivateSupplierItemHandler.cs:17-18 pattern — design chose throw, NOT DeactivateItemHandler's return-false). deactivation — Deactivate sets IsActive false; deactivate handler happy path (**Id=5 before AddAsync**, MEMORY:269). company isolation — GetAllByCompanyAsync filters.

**ItemPriceListAggregateTests** (child — SupplierItemAggregateTests shape): positive — ctor valid raises ItemPriceListCreated with CompanyId; **currencyCode "usd" normalized to "USD"**; validator valid passes; handler happy path. negative — ctor CompanyId/PriceListId/ItemId 0/-1 throws; unitPrice negative throws; currencyCode empty/2-char/4-char throws (NOT lowercase — see §3); effectiveTo before effectiveFrom throws; validator each rule fails (incl. lowercase currency, EffectiveTo < EffectiveFrom); deactivate handler missing entity throws InvalidOperationException. deactivation — Deactivate sets IsActive false; deactivate handler happy path (Id=5). company isolation — GetAllByCompanyAsync filters.

**Command shapes (design-locked):** `DeactivatePriceListCommand(long Id)` + `DeactivatePriceListResult(bool Success)` (DeactivateItemCommand.cs:5-7 shape); `DeactivateItemPriceListCommand(long Id)` (design says Id — note DeactivateSupplierItemCommand uses `SupplierItemId` param name; design chose Id, follow design). `GetItemPriceListQuery(long Id)` (GetItemQuery.cs:6 shape).

### 8. Pricing-integrity rules (goal §8 → design encoding)

- **Effective dates explicit:** EffectiveFrom required (DateOnly, non-nullable) + EffectiveTo? nullable = indefinite (TaxRate.cs:12-13). Effective-date query contract (future): `EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive` (:802).
- **No silent overwrite = versioning not editing:** port has NO update path — `GetByIdAsync`/`GetAllByCompanyAsync`/`AddAsync` only (ISupplierItemRepository shape). Only write = AddAsync of a NEW version row. No UpdateAsync, no edit command. Anchored at RESEARCH.md:174/:198 (historical-integrity axis: "no silent overwrite of prices/tax/valuation — new versions/effective-dates instead").
- **Duplicate active price prevention = DB uniqueness:** full unique `(CompanyId, PriceListId, ItemId, CurrencyCode, EffectiveFrom)` (:798) — versioning key, TaxRate precedent. R10: no reliance on app-level pre-checks (GetByCodeAsync is UX pre-check only, TOCTOU-ineffective). Deactivate→re-add same date collides — accepted (R5-style, no Reactivate).
- **Scope guard:** price master data only — no discount math, no price calculation, no currency conversion (R27, :816).

### 9. Slice file inventory (executor checklist)

**CREATE (~26):** Domain — `PriceList.cs`, `ItemPriceList.cs` (Entities), `PriceListCreated.cs`, `ItemPriceListCreated.cs` (Events), `IPriceListRepository.cs`, `IItemPriceListRepository.cs` (Ports). Infrastructure — `PriceListConfiguration.cs`, `ItemPriceListConfiguration.cs` (Configurations), `EfPriceListRepository.cs`, `EfItemPriceListRepository.cs` (Repositories). Application — `CreatePriceListCommand.cs`, `CreateItemPriceListCommand.cs`, `DeactivatePriceListCommand.cs`, `DeactivateItemPriceListCommand.cs` (Commands), `CreatePriceListCommandValidator.cs`, `CreateItemPriceListCommandValidator.cs` (Validators), `CreatePriceListHandler.cs`, `CreateItemPriceListHandler.cs`, `DeactivatePriceListHandler.cs`, `DeactivateItemPriceListHandler.cs`, `GetPriceListHandler.cs`, `GetItemPriceListHandler.cs` (Handlers), `PriceListDto.cs`, `ItemPriceListDto.cs` (DTOs), `GetPriceListQuery.cs`, `GetItemPriceListQuery.cs` (Queries). Api — `PriceListController.cs`, `ItemPriceListController.cs`. Tests — `PriceListAggregateTests.cs`, `ItemPriceListAggregateTests.cs`.

**EDIT (3):** `SmeAccountingDbContext.cs` (2 DbSet + 2 Ignore), `DependencyInjection.cs` (2 AddScoped), `tests/SmeAccounting.BankTests/Fakes.cs` (2 fakes).

**NO migration** (PLAN: G2/G3 code+tests only; price_lists + item_price_lists tables land in G4 migration #19). **NO new enums** (no BarcodeType here — that's ItemBarcode). **NO csproj/sln edits** (InternalsVisibleTo confirmed).

**Commit hygiene:** stage ONLY the ~29 files above; business-partners WIP (~69 files, still uncommitted) must stay unstaged. Never `git add -A`.

---

## Task-Specific Research — ItemBarcode Slice

**Date:** 2026-09-24. **Author:** researcher (G2 batch). **Task:** PLAN task 4 — ItemBarcode/GTIN vertical slice. **Source of truth:** RESEARCH.md "## Design Decisions (G1)" §2 (lines 689–735) + §0 canon (lines 622–645) — follow verbatim. **Status:** executor-ready spec. **READ-ONLY research — zero src/ changes.**

### 1. Template slice paths (confirmed on disk)

**Primary template — Item slice (master with nullable FKs, DbSet style):**
- `src/SmeAccounting.Domain/Entities/Item.cs` (41 lines) — ctor guards, Deactivate()
- `src/SmeAccounting.Domain/Events/ItemCreated.cs` — minimal event shape
- `src/SmeAccounting.Domain/Ports/IItemRepository.cs` — 4-member master port
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/ItemConfiguration.cs` — snake_case, nullable FK HasOne<Uom> Restrict (:26), xmin (:30)
- `src/SmeAccounting.Infrastructure/Repositories/EfItemRepository.cs` — tracked GetById, AsNoTracking GetAllByCompany, AddAsync
- `src/SmeAccounting.Application/Commands/CreateItemCommand.cs` — CompanyId FIRST, result co-located
- `src/SmeAccounting.Application/Handlers/CreateItemHandler.cs` — construct → AddAsync → SaveChangesAsync → result
- `src/SmeAccounting.Application/Validators/CreateItemCommandValidator.cs` — FluentValidation
- `src/SmeAccounting.Application/Queries/GetItemQuery.cs` — GetXQuery + GetXsByCompanyQuery co-located
- `src/SmeAccounting.Application/Handlers/GetItemHandler.cs` — ONE class implements both queries + private static Map (:24)
- `src/SmeAccounting.Application/DTOs/ItemDto.cs`
- `src/SmeAccounting.Application/Commands/DeactivateItemCommand.cs` — `DeactivateXxxCommand(long Id)` + `Result(bool Success)`
- `src/SmeAccounting.Application/Handlers/DeactivateItemHandler.cs` — ⚠️ returns `Result(false)` on missing (Item style) — **NOT the ItemBarcode style** (see below)
- `src/SmeAccounting.Api/Controllers/ItemController.cs` — thin, raw-params Create (:8)

**Best child/link template — SupplierItem slice (partial-unique HasFilter, 3-member port, Ignore-only DbContext):**
- `src/SmeAccounting.Domain/Entities/SupplierItem.cs` — child ctor guards (companyId/supplierId/itemId > 0), Deactivate()
- `src/SmeAccounting.Domain/Events/SupplierItemCreated.cs`
- `src/SmeAccounting.Domain/Ports/ISupplierItemRepository.cs` — **3 members: GetByIdAsync, GetAllByCompanyAsync, AddAsync — NO GetByCodeAsync** (canonical §2 port shape for ItemBarcode)
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/SupplierItemConfiguration.cs` — **partial unique `HasIndex(...).IsUnique().HasFilter("\"is_active\"")` (:30–32)** — first HasFilter in codebase; ItemBarcode adds a SECOND HasFilter `"is_primary" AND "is_active"` (:714 canonical)
- `src/SmeAccounting.Infrastructure/Repositories/EfSupplierItemRepository.cs` — `_context.Set<SupplierItem>()` style, OrderBy(SupplierId).ThenBy(ItemId)
- `src/SmeAccounting.Application/Commands/CreateSupplierItemCommand.cs` — CompanyId FIRST
- `src/SmeAccounting.Application/Handlers/CreateSupplierItemHandler.cs`
- `src/SmeAccounting.Application/Validators/CreateSupplierItemCommandValidator.cs` — GreaterThan(0) with English messages
- `src/SmeAccounting.Application/Handlers/DeactivateSupplierItemHandler.cs` — **throws `InvalidOperationException` on missing (:17–18)** — THIS is the ItemBarcode deactivate-handler template (canonical §2: "deactivate handler missing entity throws InvalidOperationException")
- `src/SmeAccounting.Application/Queries/GetSupplierItemQuery.cs` + `GetSupplierItemsByCompanyQuery.cs` + `GetSupplierItemHandler.cs` + `GetSupplierItemsByCompanyHandler.cs` — NOTE: SupplierItem uses `long SupplierItemId` param names; **canonical §2 says `GetItemBarcodeQuery(long Id)`** — follow canonical
- `src/SmeAccounting.Api/Controllers/SupplierItemController.cs` — ViewModel-based Create
- `src/SmeAccounting.Api/ViewModels/CreateSupplierItemViewModel.cs`
- `tests/SmeAccounting.BankTests/SupplierItemAggregateTests.cs` (146 lines) — **the test template** (see §5)

**Enum-in-controller precedent — PaymentMethod slice (arch-legal ValueObjects usage):**
- `src/SmeAccounting.Domain/ValueObjects/PaymentMethodCategory.cs` — enum in ValueObjects/
- `src/SmeAccounting.Infrastructure/Persistence/Configurations/PaymentMethodConfiguration.cs` — `HasConversion<string>()` (:31–33)
- `src/SmeAccounting.Application/Commands/CreatePaymentMethodCommand.cs` — command carries enum type (ValueObjects using)
- `src/SmeAccounting.Application/Handlers/GetPaymentMethodHandler.cs` — DTO maps `entity.Category.ToString()` (:22)
- `src/SmeAccounting.Api/Controllers/PaymentMethodController.cs` — `using SmeAccounting.Domain.ValueObjects;` (:7) + `Enum.Parse<PaymentMethodCategory>(model.Category)` (:38) — **arch-legal** (LayerCouplingTests bans only Domain.Entities :12 and Domain.Ports :27)
- `src/SmeAccounting.Api/ViewModels/CreatePaymentMethodViewModel.cs` — enum as `string Category` (:19)
- `tests/SmeAccounting.BankTests/PaymentMethodAggregateTests.cs:108` — `(PaymentMethodCategory)999` IsInEnum-fail test pattern

**Other child precedents checked:** BankBranch (full unique `(CompanyId, BankId, Code)` — NOT partial; master-child, not IsActive-link) and ItemCategory (self-ref ParentId, full unique `(CompanyId, Code)`) — neither matches ItemBarcode's IsActive-only link semantics; SupplierItem is the correct template. ItemCategoryConfiguration.cs:24 shows self-ref HasOne<ItemCategory> Restrict (not needed for ItemBarcode).

### 2. Codebase facts nailed down

**Enum placement:** `src/SmeAccounting.Domain/ValueObjects/` EXISTS — 18 files (AccountCode, AccountType, Currency, ExchangeRateType, FilingFrequency, FiscalYearStatus, Money, NormalBalance, PaymentMethodCategory, PaymentTermType, PeriodStatus, PeriodType, TaxAccountingMappingType, TaxAuthorityLevel, TaxCategory, TaxPeriodStatus, TaxTreatmentType, VoucherCategory). **No BarcodeType.cs yet** — create `Domain/ValueObjects/BarcodeType.cs` with `GTIN8, GTIN12, GTIN13, GTIN14, Other` (canonical :711). No `Domain/Enums/` dir (T1 lesson, MEMORY:112).

**Enum EF conversion:** `HasConversion<string>()` confirmed — PaymentMethodConfiguration.cs:31–33 (`Category` → `category`). ItemBarcode config: `builder.Property(e => e.BarcodeType).HasColumnName("barcode_type").HasConversion<string>();`.

**Validator custom-check precedent:** NO `private static` helper exists in any validator (grep = 0 hits). Closest patterns: (a) `RuleFor(x => x).Must(x => ...)` inline lambda — CreateUomConversionCommandValidator.cs:14 (`FromUomId != ToUomId`), CreateItemCommandValidator.cs:15, CreateInventoryAccountingConfigurationCommandValidator.cs:10; (b) `.IsInEnum()` — PaymentMethod:22, TaxType:19, VoucherType:19, etc.; (c) `.Matches(@"^[A-Z]{3}$")` — CreateBankAccountCommandValidator.cs:32. **The GS1 `HasValidCheckDigit` private static helper will be the FIRST such helper in the codebase** — pattern: `RuleFor(x => x).Must(x => HasValidCheckDigit(x.Barcode, x.BarcodeType)).When(x => x.BarcodeType != BarcodeType.Other)` (canonical :713). The `.When` on a whole-command `RuleFor(x => x)` is proven (UomConversion :14).

**Cross-entity/lookup validation:** validators are pure (no repo injection anywhere — grep confirms zero validators take repositories). Cross-entity checks live in HANDLERS (CreateUomConversionHandler.cs:15 constructs directly; class-compat check is a G2 UomClass task concern). ItemBarcode needs NO lookup — FK Restrict + ItemId>0 validator guard suffice (canonical §2 has no handler null-guard for ItemBarcode, unlike ItemReorderLevel R25).

**GS1 Mod-10 algorithm — VERIFIED by execution (python3, this research):**
- Algorithm: data = barcode minus last digit; iterate data digits right-to-left from rightmost, weights 3,1,3,1,… with 3 on rightmost data digit; `sum = Σ(digit × weight)`; `checkDigit = (10 − (sum % 10)) % 10`; valid iff checkDigit == last digit. Length-match enforced inside (barcode length must equal type's data digits + 1: GTIN8→8, GTIN12→12, GTIN13→13, GTIN14→14).
- `6291041500213` → data `629104150021`, sum=57, cd=3 == last 3 ✓ (matches canonical :712)
- `5012345670003` → data `501234567000`, sum=57, cd=3 == last 3 ✓ (matches canonical :712)
- Negative vector: `6291041500214` → computed cd=3, last=4 → INVALID (use in "invalid check digit fails" test)
- Well-known GS1 vectors also verified: GTIN-8 `12345670` (cd=0), GTIN-12 `012345678905` (cd=5), GTIN-14 `00012345678905` (cd=5) — available if executor wants per-type vectors
- **Recommended implementation detail (not in canonical, safe addition):** reject non-digit barcodes inside HasValidCheckDigit (`!barcode.All(char.IsDigit)` → false) — avoids garbage char arithmetic on letters; only makes validation stricter for malformed GTINs, consistent with GTIN semantics. Length-match is the canonical mandate; digit-check is a compatible strengthening. Also: HasValidCheckDigit must return false (never throw) for unknown enum values — the `(Enum)999` case hits both IsInEnum AND the Must rule (999 != Other), so the helper must handle unknown types gracefully (default → length 0 → false).

### 3. DbContext + DI insertion points (exact, verified by read)

**`src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs`** (140 lines, 45 DbSets, 52 Ignore lines):
- **DbSet:** insert `public DbSet<ItemBarcode> ItemBarcodes => Set<ItemBarcode>();` AFTER line 40 (`public DbSet<Item> Items => Set<Item>();`), BEFORE line 41 (ServiceItems). Style decision: DbSet (inventory-module norm — Item/ItemCategory/Warehouse/UomConversion/ServiceItem all have DbSets; only business-partners entities are Ignore-only). Repo then uses `_context.ItemBarcodes` (EfItemRepository style). Alternative (Ignore-only + `Set<ItemBarcode>()`, SupplierItem style) also works — but DbSet keeps inventory-module consistency and gives typed repo access.
- **Ignore:** insert `modelBuilder.Ignore<ItemBarcodeCreated>();` AFTER line 96 (`modelBuilder.Ignore<ItemCreated>();`), BEFORE line 97 (ServiceItemCreated). Both DbSet AND Ignore are mandatory (MEMORY:110).
- Config auto-discovery: `ApplyConfigurationsFromAssembly` at :115 — no config registration needed.

**`src/SmeAccounting.Infrastructure/DependencyInjection.cs`** (81 lines):
- Insert `services.AddScoped<IItemBarcodeRepository, EfItemBarcodeRepository>();` AFTER line 63 (`services.AddScoped<IItemRepository, EfItemRepository>();`), BEFORE line 64 (IServiceItemRepository). Adjacent-to-Item placement (MEMORY:265 race rule — re-read shared files before edit).

### 4. Fakes.cs — what's needed

**`tests/SmeAccounting.BankTests/Fakes.cs`** (235 lines) — current fakes: FakeBankRepository, FakePaymentMethodRepository, FakePostingReferenceRepository, FakeJournalEntryRepository (has `_nextId` counter), FakeOpeningBalancePeriodRepository, FakeVoucherTypeRepository (counter), FakeDocumentNumberingSeriesRepository, FakeCustomerGroupRepository, FakeSupplierGroupRepository, FakeSupplierItemRepository, FakeUnitOfWork, FakeClock.
- **NO IItemRepository fake exists** (no ItemAggregateTests.cs in BankTests — AGENTS.md's "ItemAggregateTests.cs" reference is STALE; confirmed by ls: 12 test files, none for Item). ItemBarcode tests need NO IItemRepository fake — CreateItemBarcodeHandler takes only IItemBarcodeRepository + IUnitOfWork (SupplierItem handler shape, no Item lookup).
- **ADD `FakeItemBarcodeRepository : IItemBarcodeRepository`** — 3 members (GetByIdAsync, GetAllByCompanyAsync, AddAsync) + `Stored` property, SupplierItem fake shape (Fakes.cs:202–219). Plain Add (NO `_nextId` counter) — ItemBarcode ctor has no own-Id>0 guard, transient Id=0 OK (MEMORY:269). Deactivate-happy fact sets `entity.Id = 5` BEFORE AddAsync.
- FakeUnitOfWork (SaveCalledCount) + FakeClock already exist — reuse.

### 5. Edge cases for BankTests (`ItemBarcodeAggregateTests.cs`, SupplierItemAggregateTests.cs template)

Test file usings: `SmeAccounting.Application.Commands`, `SmeAccounting.Application.Handlers` (internal — CS0246 without), `SmeAccounting.Application.Validators`, `SmeAccounting.Domain.Entities`, `SmeAccounting.Domain.Events`, `SmeAccounting.Domain.Exceptions`, `SmeAccounting.Domain.ValueObjects` (BarcodeType).

Facts (canonical §2 :731 + task-prompt additions):

| # | Fact | Vector / setup |
|---|------|----------------|
| 1 | Ctor valid raises ItemBarcodeCreated with CompanyId | `new ItemBarcode(1, 2, "6291041500213", BarcodeType.GTIN13)` — assert CompanyId=1, ItemId=2, Barcode, IsActive=true, IsPrimary=false, single event, evt.CompanyId=1 |
| 2 | Validator valid GTIN-13 passes | `6291041500213`, GTIN13 |
| 3 | Validator valid GTIN-13 passes (2nd vector) | `5012345670003`, GTIN13 |
| 4 | Validator Other skips check digit | `new CreateItemBarcodeCommand(1, 2, "INTERNAL-CODE-1", BarcodeType.Other)` passes |
| 5 | Handler happy path adds + saves | FakeItemBarcodeRepository + FakeUnitOfWork; Assert.Single(Stored), result.Id == stored[0].Id, SaveCalledCount==1 |
| 6 | Ctor CompanyId 0/-1 throws DomainException | |
| 7 | Ctor ItemId 0/-1 throws DomainException | |
| 8 | Ctor barcode whitespace throws | `" "` |
| 9 | Ctor barcode length 21 throws | `new string('0', 21)` |
| 10 | Ctor UomId 0/-1 throws DomainException | `uomId: 0` / `uomId: -1` |
| 11 | Validator invalid check digit fails | `6291041500214` (computed cd=3, last=4), GTIN13 |
| 12 | Validator wrong-length GTIN fails | e.g. `629104150021` (12 chars) with GTIN13 — length-match inside helper |
| 13 | Validator BarcodeType (Enum)999 fails IsInEnum | `(BarcodeType)999` — PaymentMethodAggregateTests.cs:108 pattern |
| 14 | Deactivate handler missing entity throws InvalidOperationException | `DeactivateItemBarcodeCommand(999)` — SupplierItem handler template (:17–18) |
| 15 | Deactivate sets IsActive false | |
| 16 | Deactivate handler happy path deactivates + saves | `entity.Id = 5` BEFORE AddAsync; assert IsActive false + SaveCalledCount==1 |
| 17 | Company isolation — GetAllByCompanyAsync filters by company | repo-level fact: add rows for company 1 + 2, assert only company-1 rows returned |
| 18 | **Deactivate leaves IsPrimary=true** (task-prompt "R2 re-add" proxy) | ctor `isPrimary: true` → Deactivate() → assert IsActive=false AND IsPrimary=true — documents WHY the primary-unique filter must be `"is_primary" AND "is_active"` (auditor correction, MEMORY:296) |

**"Deactivate primary → re-add new primary works" is a DB-level property, NOT a BankTests fact:** List-backed fakes enforce no unique indexes; the re-add behavior is delivered by the two HasFilter partial-unique indexes in ItemBarcodeConfiguration (canonical :714) and verified at G4 migration review (filter expressions rendered in CreateIndex) + SupplierItem precedent (MEMORY:263/275). Fact #18 is the testable proxy that locks the two-flag filter rationale.

Optional extras (not in canonical list, safe): validator UomId 0 fails (`GreaterThan(0).When(HasValue)`); ctor isPrimary=true sets IsPrimary; ctor UomId set persists.

### 6. Executor checklist (files to create — 17 new + 2 wiring)

Domain (4): `Entities/ItemBarcode.cs`, `Events/ItemBarcodeCreated.cs`, `Ports/IItemBarcodeRepository.cs`, `ValueObjects/BarcodeType.cs`
Infrastructure (2): `Persistence/Configurations/ItemBarcodeConfiguration.cs`, `Repositories/EfItemBarcodeRepository.cs`
Application (8): `Commands/CreateItemBarcodeCommand.cs` (+CreateItemBarcodeResult), `Commands/DeactivateItemBarcodeCommand.cs` (+DeactivateItemBarcodeResult), `Handlers/CreateItemBarcodeHandler.cs`, `Handlers/DeactivateItemBarcodeHandler.cs`, `Handlers/GetItemBarcodeHandler.cs` (one class, both queries, private static Map — GetItemHandler shape), `Validators/CreateItemBarcodeCommandValidator.cs` (GS1 helper), `Queries/GetItemBarcodeQuery.cs` (+GetItemBarcodesByCompanyQuery co-located), `DTOs/ItemBarcodeDto.cs`
Api (1): `Controllers/ItemBarcodeController.cs` (+ optional `ViewModels/CreateItemBarcodeViewModel.cs`)
Wiring (2): `SmeAccountingDbContext.cs` (DbSet after :40 + Ignore after :96), `DependencyInjection.cs` (AddScoped after :63)
Tests (1): `tests/SmeAccounting.BankTests/ItemBarcodeAggregateTests.cs` (+ FakeItemBarcodeRepository in Fakes.cs)

**Controller shape decision:** canonical §0 gives ItemController.cs:7–13 shape (raw-params Create); the enum forces either raw `string barcodeType` + `Enum.Parse<BarcodeType>` (ItemController-faithful) or ViewModel + Enum.Parse (PaymentMethod/SupplierItem precedent). Either is arch-legal (ValueObjects using OK — LayerCouplingTests bans only Domain.Entities/Domain.Ports). Recommend the PaymentMethodController pattern (ViewModel `string BarcodeType` + `Enum.Parse<BarcodeType>(model.BarcodeType)` + `using SmeAccounting.Domain.ValueObjects;`) — it is the only existing enum-in-controller precedent and handles the 7-field command cleanly. If raw-params chosen, `Enum.Parse<BarcodeType>(barcodeType)` still required (MVC model binder cannot bind enum from string without a TypeConverter — PaymentMethod G2 lesson, MEMORY:243).

**Entity ctor (canonical :707):** `(long companyId, long itemId, string barcode, BarcodeType barcodeType, long? uomId = null, bool isPrimary = false)` — guards: companyId>0, itemId>0, barcode non-whitespace, barcode.Length ≤ 20, `uomId.HasValue && uomId <= 0` (Supplier.cs:31–32 guard shape). NO Enum.IsDefined guard (validator-only enum guard, PaymentMethod precedent). Deactivate() sets IsActive=false only — does NOT touch IsPrimary (fact #18).

**EF config (canonical :713–715):** table `item_barcodes`; columns id/company_id/item_id/barcode(20)/barcode_type(string)/uom_id/is_primary/is_active/xmin; TWO partial uniques — `HasIndex(e => new { e.CompanyId, e.Barcode }).IsUnique().HasFilter("\"is_active\"")` + `HasIndex(e => new { e.CompanyId, e.ItemId }).IsUnique().HasFilter("\"is_primary\" AND \"is_active\"")` (auditor-corrected, MEMORY:296); 3 FKs Restrict (Company, Item, Uom — Uom FK nullable, ItemConfiguration.cs:26 pattern); xmin last.

**NO migration in G2** (PLAN: G2/G3 code+tests only; item_barcodes table lands in G4 migration #19 — 9 CreateTable + 4 HasFilter partial uniques, RESEARCH.md:645). Build must stay 0/0 with ItemBarcodeConfiguration referencing ItemBarcode — entity exists, compiles.

**Commit hygiene:** stage ONLY the ~20 files above; business-partners WIP (~69 files, uncommitted) must stay unstaged. Never `git add -A`.
