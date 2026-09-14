using Microsoft.EntityFrameworkCore;
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
