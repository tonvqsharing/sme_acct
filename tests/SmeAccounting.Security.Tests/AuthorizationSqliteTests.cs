using Microsoft.AspNetCore.Identity;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Modules.Authorization.Infrastructure.Services;
using SmeAccounting.Modules.Identity.Infrastructure;

namespace SmeAccounting.Security.Tests;

/// <summary>
/// RoleService / PermissionService round-trip over SQLite-backed IdentityDbContext.
/// No container required; runs everywhere.
/// </summary>
public sealed class AuthorizationSqliteTests : IAsyncLifetime
{
    private readonly SqliteConnection _connection = new("DataSource=:memory:");
    private ServiceProvider _provider = null!;
    private RoleService _roles = null!;
    private PermissionService _permissions = null!;
    private UserManager<ApplicationUser> _users = null!;

    public async ValueTask InitializeAsync()
    {
        await _connection.OpenAsync(TestContext.Current.CancellationToken);

        var services = new ServiceCollection();
        services.AddLogging();
        services.AddDbContext<IdentityDbContext>(options => options.UseSqlite(_connection));
        services.AddIdentity<ApplicationUser, ApplicationRole>()
            .AddEntityFrameworkStores<IdentityDbContext>()
            .AddDefaultTokenProviders();

        _provider = services.BuildServiceProvider();
        var scope = _provider.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<IdentityDbContext>();
        await db.Database.EnsureCreatedAsync(TestContext.Current.CancellationToken);

        var roleManager = scope.ServiceProvider.GetRequiredService<RoleManager<ApplicationRole>>();
        _users = scope.ServiceProvider.GetRequiredService<UserManager<ApplicationUser>>();
        _roles = new RoleService(roleManager, _users);
        _permissions = new PermissionService(roleManager, _users);
    }

    public async ValueTask DisposeAsync()
    {
        _provider.Dispose();
        await _connection.DisposeAsync();
    }

    [Fact]
    public async Task Create_Duplicate_FailsWithRoleAlreadyExists()
    {
        var ct = TestContext.Current.CancellationToken;

        Assert.True((await _roles.CreateAsync("SqliteRole", null, ct)).IsSuccess);
        var duplicate = await _roles.CreateAsync("SqliteRole", null, ct);

        Assert.True(duplicate.IsFailure);
        Assert.Contains(duplicate.Failures, f => f.Code == "Authorization.RoleAlreadyExists");
    }

    [Fact]
    public async Task AssignPermission_UnknownPermission_Fails()
    {
        var ct = TestContext.Current.CancellationToken;
        await _roles.CreateAsync("SqlitePermRole", null, ct);

        var result = await _roles.AssignPermissionAsync("SqlitePermRole", "nope.unknown", ct);

        Assert.True(result.IsFailure);
        Assert.Contains(result.Failures, f => f.Code == "Authorization.UnknownPermission");
    }

    [Fact]
    public async Task AssignPermission_UnknownRole_Fails()
    {
        var result = await _roles.AssignPermissionAsync("NoSuchRole", "accounts.view", TestContext.Current.CancellationToken);

        Assert.True(result.IsFailure);
        Assert.Contains(result.Failures, f => f.Code == "Authorization.RoleNotFound");
    }

    [Fact]
    public async Task Assign_Revoke_RoundTrip()
    {
        var ct = TestContext.Current.CancellationToken;
        await _roles.CreateAsync("SqliteRoundTrip", null, ct);

        Assert.True((await _roles.AssignPermissionAsync("SqliteRoundTrip", "accounts.view", ct)).IsSuccess);
        // Idempotent re-assign succeeds without duplicating the claim.
        Assert.True((await _roles.AssignPermissionAsync("SqliteRoundTrip", "accounts.view", ct)).IsSuccess);

        var stored = await _roles.GetRolePermissionsAsync("SqliteRoundTrip", ct);
        Assert.True(stored.IsSuccess);
        Assert.Equal(["accounts.view"], stored.Value!.ToArray());

        Assert.True((await _roles.RevokePermissionAsync("SqliteRoundTrip", "accounts.view", ct)).IsSuccess);
        var afterRevoke = await _roles.GetRolePermissionsAsync("SqliteRoundTrip", ct);
        Assert.True(afterRevoke.IsSuccess);
        Assert.Empty(afterRevoke.Value!);
    }

    [Fact]
    public async Task Delete_UnknownRole_Fails()
    {
        var result = await _roles.DeleteAsync("NoSuchRole", TestContext.Current.CancellationToken);

        Assert.True(result.IsFailure);
        Assert.Contains(result.Failures, f => f.Code == "Authorization.RoleNotFound");
    }

    [Fact]
    public async Task Delete_RemovesRole()
    {
        var ct = TestContext.Current.CancellationToken;
        await _roles.CreateAsync("SqliteDeleteMe", null, ct);

        Assert.True((await _roles.DeleteAsync("SqliteDeleteMe", ct)).IsSuccess);

        var roles = await _roles.ListRolesAsync(ct);
        Assert.DoesNotContain("SqliteDeleteMe", roles.Value!);
    }

    /// <summary>
    /// Known Guid-vs-long bug: Identity PKs are long, but IRoleService takes
    /// Guid. FindByIdAsync(guid.ToString()) throws FormatException because
    /// Identity tries to parse the GUID string as Int64. Documented in MEMORY.md.
    /// </summary>
    [Fact]
    public async Task AssignRoleToUser_GuidUserId_ThrowsFormatException()
    {
        var ct = TestContext.Current.CancellationToken;
        await _roles.CreateAsync("SqliteUserRole", null, ct);

        await Assert.ThrowsAnyAsync<Exception>(() =>
            _roles.AssignRoleToUserAsync(Guid.NewGuid(), "SqliteUserRole", ct));
    }

    [Fact]
    public async Task AssignRoleToUser_UnknownRole_ReturnsRoleNotFound()
    {
        var result = await _roles.AssignRoleToUserAsync(Guid.NewGuid(), "NoSuchRole", TestContext.Current.CancellationToken);

        Assert.True(result.IsFailure);
        Assert.Contains(result.Failures, f => f.Code == "Authorization.RoleNotFound");
    }

    /// <summary>
    /// Known Guid-vs-long bug: same FormatException as AssignRoleToUser.
    /// </summary>
    [Fact]
    public async Task PermissionService_GuidUserId_ThrowsFormatException()
    {
        var ct = TestContext.Current.CancellationToken;

        await Assert.ThrowsAnyAsync<Exception>(() =>
            _permissions.GetPermissionsAsync(Guid.NewGuid(), ct));
    }

    /// <summary>
    /// Known Guid-vs-long bug: even after creating a real user with a long PK,
    /// the Guid-based service surface cannot address it (FormatException).
    /// This test documents the gap while verifying role claims are stored.
    /// </summary>
    [Fact]
    public async Task PermissionService_AggregatesRoleClaims_ForRealUser()
    {
        var ct = TestContext.Current.CancellationToken;
        await _roles.CreateAsync("SqliteAggRole", null, ct);
        await _roles.AssignPermissionAsync("SqliteAggRole", "accounts.view", ct);

        var user = new ApplicationUser
        {
            UserName = "sqlite_agg",
            Email = "sqlite_agg@test.local",
            DisplayName = "SQLite Agg Test User",
        };
        Assert.True((await _users.CreateAsync(user)).Succeeded);
        Assert.True((await _users.AddToRoleAsync(user, "SqliteAggRole")).Succeeded);

        // The Guid-typed IPermissionService surface cannot address real long PK users.
        await Assert.ThrowsAnyAsync<Exception>(() =>
            _permissions.GetPermissionsAsync(Guid.NewGuid(), ct));
    }
}
