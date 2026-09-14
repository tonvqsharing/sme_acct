# Provider Code Map

## xmin concurrency token
- File: src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:40-50
- Current: shadow property `Xmin` type `xid`, IsConcurrencyToken, BeforeSaveBehavior.Ignore, AfterSaveBehavior.Ignore
- Abstraction: replace with provider-agnostic concurrency token or conditional per provider

## uuid-ossp extension
- File: src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:26
- Current: modelBuilder.HasPostgresExtension("uuid-ossp")
- Abstraction: remove, use EF Core default GUID generation

## IdentityByDefaultColumn
- File: src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:37
- Current: SetAnnotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn)
- Abstraction: use provider-neutral HasDefaultValueSql or ValueGeneratedOnAdd

## snake_case naming
- File: src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:129-148
- Current: ApplySnakeCaseNamingConvention
- Abstraction: provider-agnostic, keep

## Hard-coded UseNpgsql DI
- DependencyInjection.cs:32-39
- IdentityServiceExtensions.cs:15-16
- DesignTimeDbContextFactory.cs:11-14
- IdentityDbContextFactory.cs:11
- Abstraction: DbProviderSelector

## Duplicate ToSnakeCase
- SmeAccountingDbContext.cs:150-168
- IdentityDbContext.cs:37-55
- Abstraction: consolidate
