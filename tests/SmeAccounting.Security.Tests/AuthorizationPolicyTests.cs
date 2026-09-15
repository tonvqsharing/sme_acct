using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.Extensions.Options;
using SmeAccounting.Modules.Authorization.Application.Authorization;
using SmeAccounting.Modules.Authorization.Domain;

namespace SmeAccounting.Security.Tests;

public class AuthorizationPolicyTests
{
    private static ClaimsPrincipal PrincipalWith(params string[] permissions)
    {
        var claims = permissions.Select(p => new Claim("permission", p));
        return new ClaimsPrincipal(new ClaimsIdentity(claims, "test"));
    }

    [Fact]
    public async Task Handler_Grants_WhenUserHasPermission()
    {
        var handler = new PermissionAuthorizationHandler();
        var requirement = new PermissionRequirement(Permissions.Accounts.View);
        var context = new AuthorizationHandlerContext([requirement], PrincipalWith(Permissions.Accounts.View), null);

        await handler.HandleAsync(context);

        Assert.True(context.HasSucceeded);
    }

    [Fact]
    public async Task Handler_Grants_OnAdminBypass()
    {
        var handler = new PermissionAuthorizationHandler();
        var requirement = new PermissionRequirement(Permissions.Journal.Post);
        var context = new AuthorizationHandlerContext([requirement], PrincipalWith(Permissions.Users.ManageRoles), null);

        await handler.HandleAsync(context);

        Assert.True(context.HasSucceeded);
    }

    [Fact]
    public async Task Handler_Denies_WhenUserLacksPermission()
    {
        var handler = new PermissionAuthorizationHandler();
        var requirement = new PermissionRequirement(Permissions.Journal.Post);
        var context = new AuthorizationHandlerContext([requirement], PrincipalWith(Permissions.Accounts.View), null);

        await handler.HandleAsync(context);

        Assert.False(context.HasSucceeded);
    }

    [Fact]
    public async Task PolicyProvider_BuildsPermissionPolicy()
    {
        var provider = new PermissionPolicyProvider(Options.Create(new AuthorizationOptions()));

        var policy = await provider.GetPolicyAsync("Permission:accounts.view");

        Assert.NotNull(policy);
        Assert.Contains(policy.Requirements.OfType<PermissionRequirement>(), r => r.Permission == "accounts.view");
    }

    [Fact]
    public async Task PolicyProvider_PrefixIsCaseInsensitive()
    {
        var provider = new PermissionPolicyProvider(Options.Create(new AuthorizationOptions()));

        var policy = await provider.GetPolicyAsync("permission:accounts.view");

        Assert.NotNull(policy);
    }

    [Fact]
    public async Task PolicyProvider_FallsBack_ForNonPermissionPolicy()
    {
        var provider = new PermissionPolicyProvider(Options.Create(new AuthorizationOptions()));

        var policy = await provider.GetPolicyAsync("NoSuchPolicy");

        Assert.Null(policy);
    }

    [Fact]
    public void Claims_GetUserId_ParsesLong()
    {
        var principal = new ClaimsPrincipal(new ClaimsIdentity([new Claim(ClaimTypes.NameIdentifier, "42")]));

        Assert.Equal(42L, principal.GetUserId());
    }

    [Fact]
    public void Claims_GetUserId_NonNumeric_ReturnsNull()
    {
        var principal = new ClaimsPrincipal(new ClaimsIdentity([new Claim(ClaimTypes.NameIdentifier, "not-a-long")]));

        Assert.Null(principal.GetUserId());
    }

    [Fact]
    public void Claims_GetPermissions_ReturnsPermissionClaims()
    {
        var principal = PrincipalWith(Permissions.Accounts.View, Permissions.Journal.View);

        var permissions = principal.GetPermissions();

        Assert.Equal(2, permissions.Count);
        Assert.Contains(Permissions.Accounts.View, permissions);
    }

    [Fact]
    public void Claims_HasPermission_MatchesExactly()
    {
        var principal = PrincipalWith(Permissions.Accounts.View);

        Assert.True(principal.HasPermission(Permissions.Accounts.View));
        Assert.False(principal.HasPermission(Permissions.Accounts.Delete));
    }

    [Fact]
    public void Claims_GetBranchId_ParsesLong()
    {
        var principal = new ClaimsPrincipal(new ClaimsIdentity([new Claim("branch_id", "7")]));

        Assert.Equal(7L, principal.GetBranchId());
    }
}
