using Microsoft.Extensions.Configuration;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Security.Tests;

/// <summary>
/// Provider selection without a database: parsing, defaults, and
/// connection-string priority. Covers the "dual stack" config surface
/// (PostgreSql default, per-provider fallbacks).
/// </summary>
public class DbProviderSelectorTests
{
    private static IConfiguration Config(params (string Key, string? Value)[] pairs)
    {
        var data = pairs.ToDictionary(p => p.Key, p => p.Value);
        return new ConfigurationBuilder().AddInMemoryCollection(data).Build();
    }

    [Fact]
    public void Resolve_DefaultsToPostgreSql()
    {
        Assert.Equal(DatabaseProvider.PostgreSql, DbProviderSelector.Resolve(Config()));
    }

    [Fact]
    public void Resolve_ParsesProviderCaseInsensitively()
    {
        Assert.Equal(DatabaseProvider.Sqlite, DbProviderSelector.Resolve(Config(("Database:Provider", "sqlite"))));
        Assert.Equal(DatabaseProvider.MariaDb, DbProviderSelector.Resolve(Config(("Database:Provider", "MariaDb"))));
        Assert.Equal(DatabaseProvider.SqlServer, DbProviderSelector.Resolve(Config(("Database:Provider", "SQLSERVER"))));
    }

    [Fact]
    public void Resolve_UnknownValue_FallsBackToPostgreSql()
    {
        Assert.Equal(DatabaseProvider.PostgreSql, DbProviderSelector.Resolve(Config(("Database:Provider", "oracle"))));
    }

    [Fact]
    public void ResolveConnectionString_ExplicitValue_Wins()
    {
        var config = Config(("Database:ConnectionString", "Host=custom;Database=x"));

        var result = DbProviderSelector.ResolveConnectionString(config, DatabaseProvider.Sqlite);

        Assert.Equal("Host=custom;Database=x", result);
    }

    [Fact]
    public void ResolveConnectionString_SqliteDefault_PointsAtLocalFile()
    {
        var result = DbProviderSelector.ResolveConnectionString(Config(), DatabaseProvider.Sqlite);

        Assert.Equal("Data Source=smeaccounting.db", result);
    }

    [Fact]
    public void ResolveConnectionString_PostgresDefault_IsLocalhost()
    {
        var result = DbProviderSelector.ResolveConnectionString(Config(), DatabaseProvider.PostgreSql);

        Assert.Contains("Host=localhost", result);
    }

    [Fact]
    public void ResolveConnectionString_UnsupportedProvider_Throws()
    {
        Assert.Throws<InvalidOperationException>(() =>
            DbProviderSelector.ResolveConnectionString(Config(), (DatabaseProvider)999));
    }
}
