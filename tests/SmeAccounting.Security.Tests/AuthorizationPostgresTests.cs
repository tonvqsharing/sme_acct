using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Modules.Authorization.Infrastructure.Services;
using SmeAccounting.Modules.Identity.Infrastructure;
using Testcontainers.PostgreSql;

namespace SmeAccounting.Security.Tests;

/// <summary>
/// Postgres-backed RoleService smoke. Skips gracefully when Docker is
/// unavailable (CI without Docker, local dev) — SQLite suite covers the
/// same round-trips without a container.
/// </summary>
public sealed class AuthorizationPostgresTests : IAsyncLifetime
{
    private PostgreSqlContainer _postgres = null!;
    private ServiceProvider _provider = null!;
    private RoleService _roles = null!;
    private bool _skipped;

    public async ValueTask InitializeAsync()
    {
        if (!File.Exists("/var/run/docker.sock")
            && string.IsNullOrEmpty(Environment.GetEnvironmentVariable("DOCKER_HOST")))
        {
            _skipped = true;
            return;
        }

        try
        {
            _postgres = new PostgreSqlBuilder("postgres:16.14-alpine")
                .WithDatabase("sme_accounting_auth_test")
                .WithUsername("postgres")
                .WithPassword("postgres")
                .WithCleanUp(true)
                .Build();
            await _postgres.StartAsync(TestContext.Current.CancellationToken);
        }
        catch
        {
            _skipped = true;
            return;
        }

        var services = new ServiceCollection();
        services.AddLogging();
        services.AddDbContext<IdentityDbContext>(options => options.UseNpgsql(_postgres.GetConnectionString()));
        services.AddIdentity<ApplicationUser, ApplicationRole>()
            .AddEntityFrameworkStores<IdentityDbContext>()
            .AddDefaultTokenProviders();

        _provider = services.BuildServiceProvider();
        var scope = _provider.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<IdentityDbContext>();
        await db.Database.EnsureCreatedAsync(TestContext.Current.CancellationToken);

        var roleManager = scope.ServiceProvider.GetRequiredService<RoleManager<ApplicationRole>>();
        var userManager = scope.ServiceProvider.GetRequiredService<UserManager<ApplicationUser>>();
        _roles = new RoleService(roleManager, userManager);
    }

    public async ValueTask DisposeAsync()
    {
        _provider?.Dispose();
        if (_postgres is not null && !_skipped)
        {
            await _postgres.DisposeAsync();
        }
    }

    private void SkipIfNoDocker()
    {
        if (_skipped)
            Assert.Skip("Docker unavailable — skipping Postgres integration.");
    }

    [Fact]
    public async Task Postgres_CreateAssignDelete_RoundTrip()
    {
        SkipIfNoDocker();
        var ct = TestContext.Current.CancellationToken;

        Assert.True((await _roles.CreateAsync("PgRole", null, ct)).IsSuccess);
        Assert.True((await _roles.AssignPermissionAsync("PgRole", "reports.view", ct)).IsSuccess);

        var stored = await _roles.GetRolePermissionsAsync("PgRole", ct);
        Assert.True(stored.IsSuccess);
        Assert.Equal(["reports.view"], stored.Value!.ToArray());

        Assert.True((await _roles.DeleteAsync("PgRole", ct)).IsSuccess);
    }

    [Fact]
    public async Task Postgres_SnakeCase_IdentityTablesExist()
    {
        SkipIfNoDocker();
        var ct = TestContext.Current.CancellationToken;
        var scope = _provider.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<IdentityDbContext>();

        var tables = await db.Database
            .SqlQueryRaw<string>("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'asp_net%'")
            .ToListAsync(ct);

        Assert.Contains("asp_net_roles", tables);
        Assert.Contains("asp_net_users", tables);
    }
}
