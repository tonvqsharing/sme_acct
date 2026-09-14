using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata;
using System.Linq.Expressions;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;
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

        modelBuilder.HasPostgresExtension("uuid-ossp");
        ApplySnakeCaseNamingConvention(modelBuilder);

        // modelBuilder.UseSnakeCaseNamingConvention(); // requires Npgsql EF Core 9 convention extension

        // Configure default identity for long keys
        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            var clrType = entityType.ClrType;
            if (typeof(BaseEntity).IsAssignableFrom(clrType) && entityType.FindProperty("Id")?.ClrType == typeof(long))
            {
                entityType.FindProperty("Id")!.SetAnnotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn);
            }

            // Add xmin shadow property as concurrency token for PostgreSQL
            if (typeof(BaseEntity).IsAssignableFrom(clrType))
            {
                var xminShadow = entityType.AddProperty("Xmin", typeof(uint));
                xminShadow.SetColumnName("xmin");
                xminShadow.SetColumnType("xid");
                xminShadow.IsConcurrencyToken = true;
                // xmin is a PostgreSQL system column - exclude from INSERT/UPDATE, only read for concurrency
                xminShadow.SetBeforeSaveBehavior(PropertySaveBehavior.Ignore);
                xminShadow.SetAfterSaveBehavior(PropertySaveBehavior.Ignore);
            }
        }

        // Conventions
        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            // Decimal precision default
            foreach (var property in entityType.GetProperties())
            {
                if (property.ClrType == typeof(decimal) || property.ClrType == typeof(decimal?))
                {
                    property.SetColumnType("numeric(18,2)");
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

        // Use anonymous types to include shadow property Xmin
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
                DeletedBy = (Guid?)null,
                Xmin = 0u
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
                DeletedBy = (Guid?)null,
                Xmin = 0u
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
