using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Infrastructure.Persistence;
using SmeAccounting.Infrastructure.Persistence.Entities;
using Testcontainers.PostgreSql;
using Xunit;

namespace SmeAccounting.Infrastructure.Tests;

public sealed class DatabaseIntegrationTests : IAsyncLifetime
{
    private readonly PostgreSqlContainer _postgres;
    private SmeAccountingDbContext _dbContext = null!;

    public DatabaseIntegrationTests()
    {
        _postgres = new PostgreSqlBuilder("postgres:16.14-alpine")
            .WithDatabase("sme_accounting_test")
            .WithUsername("postgres")
            .WithPassword("postgres")
            .WithCleanUp(true)
            .Build();
    }

    public async ValueTask InitializeAsync()
    {
        await _postgres.StartAsync(TestContext.Current.CancellationToken);

        var services = new ServiceCollection();
        services.AddDbContext<SmeAccountingDbContext>(options =>
            options.UseNpgsql(_postgres.GetConnectionString()));

        var provider = services.BuildServiceProvider();
        _dbContext = provider.GetRequiredService<SmeAccountingDbContext>();

        await _dbContext.Database.MigrateAsync(TestContext.Current.CancellationToken);
    }

    public async ValueTask DisposeAsync()
    {
        await _dbContext.DisposeAsync();
        await _postgres.DisposeAsync();
    }

    [Fact]
    public async Task SchemaCreatedWithSnakeCaseNaming()
    {
        var tables = await _dbContext.Database.SqlQueryRaw<string>(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('accounts', 'companies', 'branches', 'audit_log_entries')"
        ).ToListAsync(TestContext.Current.CancellationToken);

        Assert.Contains("accounts", tables);
        Assert.Contains("companies", tables);
        Assert.Contains("branches", tables);
        Assert.Contains("audit_log_entries", tables);
    }

    [Fact]
    public async Task PrimaryKeysAreBigintIdentity()
    {
        var pkInfo = await _dbContext.Database.SqlQueryRaw<PkInfo>(
            @"SELECT kcu.column_name, c.data_type
              FROM information_schema.table_constraints tc
              JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
              JOIN information_schema.columns c ON c.table_name = kcu.table_name AND c.column_name = kcu.column_name
              WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_name IN ('accounts', 'companies', 'branches', 'audit_log_entries')"
        ).ToListAsync(TestContext.Current.CancellationToken);

        foreach (var pk in pkInfo)
        {
            Assert.Equal("bigint", pk.DataType);
        }
    }

    [Fact]
    public async Task ColumnsUseSnakeCase()
    {
        var columns = await _dbContext.Database.SqlQueryRaw<string>(
            @"SELECT column_name FROM information_schema.columns
              WHERE table_name = 'accounts'
              AND column_name IN ('company_id', 'account_type', 'normal_balance', 'created_at_utc', 'updated_at_utc', 'is_active', 'is_deleted', 'deleted_at_utc')"
        ).ToListAsync(TestContext.Current.CancellationToken);

        Assert.Contains("company_id", columns);
        Assert.Contains("account_type", columns);
        Assert.Contains("normal_balance", columns);
        Assert.Contains("created_at_utc", columns);
        Assert.Contains("updated_at_utc", columns);
        Assert.Contains("is_active", columns);
        Assert.Contains("is_deleted", columns);
        Assert.Contains("deleted_at_utc", columns);
    }

    [Fact]
    public async Task SeedDataPresent()
    {
        var company = await _dbContext.Companies.SingleOrDefaultAsync(c => c.Id == 1, TestContext.Current.CancellationToken);
        Assert.NotNull(company);
        Assert.Equal("DEMO", company.Code);
        Assert.Equal("Demo Company", company.Name);
        Assert.True(company.IsActive);
        Assert.False(company.IsDeleted);

        var branch = await _dbContext.Branches.SingleOrDefaultAsync(b => b.Id == 1, TestContext.Current.CancellationToken);
        Assert.NotNull(branch);
        Assert.Equal(1, branch.CompanyId);
        Assert.Equal("HO", branch.Code);
        Assert.Equal("Head Office", branch.Name);
        Assert.True(branch.IsActive);
        Assert.False(branch.IsDeleted);
    }

    [Fact]
    public async Task SoftDeleteFilterApplied()
    {
        var deletedCompany = new Company
        {
            Name = "Deleted Co",
            Code = "DEL",
            IsActive = false,
            CreatedAtUtc = DateTime.UtcNow,
            IsDeleted = true,
            DeletedAtUtc = DateTime.UtcNow
        };
        _dbContext.Companies.Add(deletedCompany);
        await _dbContext.SaveChangesAsync(TestContext.Current.CancellationToken);

        var activeCompanies = await _dbContext.Companies.ToListAsync(TestContext.Current.CancellationToken);
        Assert.All(activeCompanies, c => Assert.False(c.IsDeleted));
    }

    [Fact]
    public async Task ForeignKeyConstraintsExist()
    {
        var fks = await _dbContext.Database.SqlQueryRaw<string>(
            @"SELECT constraint_name FROM information_schema.table_constraints
              WHERE constraint_type = 'FOREIGN KEY'
              AND table_name IN ('accounts', 'branches')"
        ).ToListAsync(TestContext.Current.CancellationToken);

        Assert.NotEmpty(fks);
        Assert.Contains(fks, fk => fk.Contains("branches") && fk.Contains("companies"));
    }

    private sealed record PkInfo(string ColumnName, string DataType);
}