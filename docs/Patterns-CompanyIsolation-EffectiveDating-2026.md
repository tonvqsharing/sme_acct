# Patterns — Company Isolation, Effective Dating, Soft Delete, Enum Storage
**Extracted:** 2026-09-22
**Scope:** SME Accounting codebase patterns for implementation reference

## 1. Company Isolation

### FK to Company with DeleteBehavior.Restrict
Universal pattern for all company-scoped entities.

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs`
```csharp
builder.HasOne<Company>()
    .WithMany()
    .HasForeignKey(e => e.CompanyId)
    .OnDelete(DeleteBehavior.Restrict);
```

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountConfiguration.cs` lines 64-67
```csharp
builder.HasOne<Company>()
    .WithMany()
    .HasForeignKey(e => e.CompanyId)
    .OnDelete(DeleteBehavior.Restrict);
```

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/ExchangeRateConfiguration.cs` lines 49-52
```csharp
builder.HasOne<Company>()
    .WithMany()
    .HasForeignKey(e => e.CompanyId)
    .OnDelete(DeleteBehavior.Restrict);
```

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxRateConfiguration.cs` lines 49-52
```csharp
builder.HasOne<Company>()
    .WithMany()
    .HasForeignKey(e => e.CompanyId)
    .OnDelete(DeleteBehavior.Restrict);
```

Domain validation:
```csharp
if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");
```

### Composite Unique Indexes per Company
Enforces per-company uniqueness at DB level.

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs` lines 34-35
```csharp
builder.HasIndex(e => new { e.CompanyId, e.Code })
    .IsUnique();
```

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/CostCenterConfiguration.cs`
Same pattern `(CompanyId, Code)` IsUnique.

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/ProjectConfiguration.cs`
Same pattern `(CompanyId, Code)` IsUnique.

**Composite with additional columns:**
**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxRateConfiguration.cs` lines 46-47
```csharp
builder.HasIndex(e => new { e.CompanyId, e.TaxTypeId, e.RateValue, e.EffectiveFrom })
    .IsUnique();
```

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/ExchangeRateConfiguration.cs` lines 46-47
```csharp
builder.HasIndex(e => new { e.CompanyId, e.FromCurrencyCode, e.ToCurrencyCode, e.RateType, e.EffectiveDate })
    .IsUnique();
```

## 2. Effective Dating

### EffectiveFrom / EffectiveTo pattern
Used for rates, rules, exchange rates.

**Domain entity:** `src/SmeAccounting.Domain/Entities/TaxRate.cs`
```csharp
public DateOnly EffectiveFrom { get; private set; }
public DateOnly? EffectiveTo { get; private set; }
```

**Domain entity:** `src/SmeAccounting.Domain/Entities/TaxRule.cs` lines 16-17
```csharp
public DateOnly EffectiveFrom { get; private set; }
public DateOnly? EffectiveTo { get; private set; }
```

**EF config:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxRateConfiguration.cs` lines 33-37
```csharp
builder.Property(e => e.EffectiveFrom).HasColumnName("effective_from");
builder.Property(e => e.EffectiveTo).HasColumnName("effective_to");
```

**Query pattern:**
```
EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive
```
Nullable `EffectiveTo` means indefinite validity.

**Additional examples:**
- `Project.StartDate` / `Project.EndDate` optional effective dating
- `ExchangeRate.EffectiveDate` with composite unique index

## 3. Soft Delete

### IsActive flag pattern
Never hard delete for audit trail.

**Domain entity:** `src/SmeAccounting.Domain/Entities/Department.cs` lines 11, 15-29
```csharp
public bool IsActive { get; private set; } = true;
```

**Domain entity:** `src/SmeAccounting.Domain/Entities/TaxRate.cs` line 14
```csharp
public bool IsActive { get; private set; } = true;
public void Deactivate() { IsActive = false; }
```

**EF config:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs` lines 31-32
```csharp
builder.Property(e => e.IsActive).HasColumnName("is_active");
```

**Domain behavior:**
- `Account.Deprecate()` sets `IsActive = false`
- Domain events raised on deactivation where applicable
- Queries filter by `IsActive = true` by convention

## 4. Enum Storage

### HasConversion<string>()
All enums stored as string in PostgreSQL.

**Value object:** `src/SmeAccounting.Domain/ValueObjects/NormalBalance.cs`
```csharp
public enum NormalBalance { Debit, Credit }
```

**EF config:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountConfiguration.cs` lines 29-30, 45-47
```csharp
builder.Property(e => e.AccountType).HasColumnName("account_type").HasConversion<string>();
builder.Property(e => e.NormalBalance).HasColumnName("normal_balance").HasConversion<string>();
```

**EF config:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/ExchangeRateConfiguration.cs` lines 35-37
```csharp
builder.Property(e => e.RateType).HasColumnName("rate_type").HasConversion<string>();
```

Enums covered: `AccountType`, `NormalBalance`, `PeriodType`, `PeriodStatus`, `FiscalYearStatus`, `ExchangeRateType`, `TaxCategory`, `PaymentTermType`, etc.

## 5. Supporting Cross-Cutting Patterns

### xmin concurrency token
**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs` lines 42-44
```csharp
builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
```

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountConfiguration.cs` lines 69-71
```csharp
builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
```
Present on all entities extending `BaseEntity`. PostgreSQL `xid` row version for optimistic concurrency.

### Snake_case naming
**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs` lines 11, 18-19
```csharp
builder.ToTable("departments");
builder.Property(e => e.CompanyId).HasColumnName("company_id");
```

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountConfiguration.cs` lines 12, 38-39
```csharp
builder.ToTable("accounts");
builder.Property(e => e.CompanyId).HasColumnName("company_id");
```
`EFCore.NamingConventions` enforces snake_case.

### SetNull for optional dimensions
**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/JournalEntryLineConfiguration.cs` lines 57-70
```csharp
builder.HasOne<Department>()
    .WithMany()
    .HasForeignKey(e => e.DepartmentId)
    .OnDelete(DeleteBehavior.SetNull);
builder.HasOne<CostCenter>()
    .WithMany()
    .HasForeignKey(e => e.CostCenterId)
    .OnDelete(DeleteBehavior.SetNull);
builder.HasOne<Project>()
    .WithMany()
    .HasForeignKey(e => e.ProjectId)
    .OnDelete(DeleteBehavior.SetNull);
```
Dimensions optional on `JournalEntryLine`. Deleting dimension nulls FK, retains line data.

### Domain validation pattern
**File:** `src/SmeAccounting.Domain/Entities/Department.cs` lines 15-29
```csharp
public Department(long companyId, string code, string name)
{
    if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");
    if (string.IsNullOrWhiteSpace(code)) throw new DomainException("Code is required.");
    if (string.IsNullOrWhiteSpace(name)) throw new DomainException("Name is required.");
    CompanyId = companyId;
    Code = code;
    Name = name;
    AddDomainEvent(new DepartmentCreated(Id, companyId, DateTimeOffset.UtcNow));
}
```

Private parameterless ctor for EF, public ctor with `DomainException` validation, domain events added on construction.

## Summary
- Company isolation: `CompanyId` FK Restrict + composite unique `(CompanyId, Code)`
- Effective dating: `DateOnly EffectiveFrom` + nullable `DateOnly? EffectiveTo`
- Soft delete: `IsActive` bool, `Deactivate()` method
- Enum storage: `HasConversion<string>()`
- Concurrency: `xmin` row version
- Naming: snake_case tables/columns
- Dimensions: `SetNull` delete behavior
