using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata;
using System.Linq.Expressions;
using SmeAccounting.Infrastructure.Persistence.Entities;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Infrastructure.Persistence;

public class SmeAccountingDbContext : DbContext
{
    public SmeAccountingDbContext(DbContextOptions<SmeAccountingDbContext> options)
        : base(options)
    {
    }

    public DbSet<Company> Companies => Set<Company>();
    public DbSet<Branch> Branches => Set<Branch>();
    public DbSet<Account> Accounts => Set<Account>();
    public DbSet<AuditLogEntry> AuditLogEntries => Set<AuditLogEntry>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        var providerName = modelBuilder.Model.FindAnnotation("Relational:ProviderName")?.Value as string ?? "";

        ApplySnakeCaseNamingConvention(modelBuilder);

        // modelBuilder.UseSnakeCaseNamingConvention(); // requires Npgsql EF Core 9 convention extension

        // Configure default identity for long keys per provider
        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            var clrType = entityType.ClrType;
            if (typeof(BaseEntity).IsAssignableFrom(clrType) && entityType.FindProperty("Id")?.ClrType == typeof(long))
            {
                var idProp = entityType.FindProperty("Id");
                if (idProp != null)
                {
                    if (providerName.Contains("Npgsql") || providerName.Contains("PostgreSQL"))
                    {
                        // PostgreSQL uses identity by default
                    }
                    else if (providerName.Contains("MySql") || providerName.Contains("MariaDb"))
                    {
                        idProp.ValueGenerated = ValueGenerated.OnAdd;
                    }
                    else if (providerName.Contains("Sqlite"))
                    {
                        idProp.ValueGenerated = ValueGenerated.OnAdd;
                    }
                    else if (providerName.Contains("SqlServer"))
                    {
                        idProp.ValueGenerated = ValueGenerated.OnAdd;
                    }
                }
            }
        }

        // Conventions
        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            // Decimal precision default per provider
            foreach (var property in entityType.GetProperties())
            {
                if (property.ClrType == typeof(decimal) || property.ClrType == typeof(decimal?))
                {
                    if (providerName.Contains("Npgsql") || providerName.Contains("PostgreSQL") || providerName.Contains("MySql") || providerName.Contains("Sqlite") || providerName.Contains("SqlServer"))
                    {
                        property.SetColumnType("numeric(18,2)");
                    }
                }
            }
        }

        // Soft delete filter
        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            var isSoftDeletable = entityType.ClrType.GetInterfaces()
                .Any(i => i.Name == "ISoftDeletable");
            if (isSoftDeletable)
            {
                var parameter = Expression.Parameter(entityType.ClrType, "e");
                var property = Expression.Property(parameter, "IsDeleted");
                var condition = Expression.Equal(property, Expression.Constant(false));
                var lambda = Expression.Lambda(condition, parameter);
                modelBuilder.Entity(entityType.ClrType).HasQueryFilter(lambda);
            }
        }

        modelBuilder.ApplyConfigurationsFromAssembly(typeof(SmeAccountingDbContext).Assembly);

        SeedData(modelBuilder);
    }

    private static void SeedData(ModelBuilder modelBuilder)
    {
        var now = new DateTime(2026, 1, 1, 0, 0, 0, DateTimeKind.Utc);

        modelBuilder.Entity<Company>().HasData(
            new
            {
                Id = 1L,
                Name = "Demo Company",
                Code = "DEMO",
                IsActive = true,
                CreatedAtUtc = now,
                CreatedBy = (Guid?)null,
                UpdatedAtUtc = (DateTime?)null,
                UpdatedBy = (Guid?)null,
                IsDeleted = false,
                DeletedAtUtc = (DateTime?)null,
                DeletedBy = (Guid?)null
            }
        );

        modelBuilder.Entity<Branch>().HasData(
            new
            {
                Id = 1L,
                CompanyId = 1L,
                Name = "Head Office",
                Code = "HO",
                IsActive = true,
                CreatedAtUtc = now,
                CreatedBy = (Guid?)null,
                UpdatedAtUtc = (DateTime?)null,
                UpdatedBy = (Guid?)null,
                IsDeleted = false,
                DeletedAtUtc = (DateTime?)null,
                DeletedBy = (Guid?)null
            }
        );
    }

    private static void ApplySnakeCaseNamingConvention(ModelBuilder modelBuilder)
    {
        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            var tableName = ToSnakeCase(entityType.GetTableName() ?? entityType.ClrType.Name);
            entityType.SetTableName(tableName);

            foreach (var property in entityType.GetProperties())
            {
                var columnName = ToSnakeCase(property.GetColumnName() ?? property.Name);
                property.SetColumnName(columnName);
            }

            foreach (var foreignKey in entityType.GetForeignKeys())
            {
                var fkName = ToSnakeCase(foreignKey.GetConstraintName() ?? $"FK_{entityType.GetTableName()}_{foreignKey.PrincipalEntityType.GetTableName()}");
                foreignKey.SetConstraintName(fkName);
            }
        }
    }

    private static string ToSnakeCase(string name)
    {
        if (string.IsNullOrEmpty(name)) return name;
        var sb = new System.Text.StringBuilder();
        for (int i = 0; i < name.Length; i++)
        {
            var c = name[i];
            if (char.IsUpper(c))
            {
                if (i > 0) sb.Append('_');
                sb.Append(char.ToLowerInvariant(c));
            }
            else
            {
                sb.Append(c);
            }
        }
        return sb.ToString();
    }
}
