using SmeAccounting.Modules.Authorization.Domain;
using IdentityPermissions = SmeAccounting.Modules.Identity.Application.Permissions;

namespace SmeAccounting.Security.Tests;

public class AuthorizationCatalogTests
{
    private static readonly string[] ExpectedPermissions =
    [
        "accounts.view", "accounts.create", "accounts.edit", "accounts.delete",
        "journal.view", "journal.create", "journal.edit", "journal.post", "journal.reverse",
        "reports.view", "reports.export",
        "settings.view", "settings.manage",
        "users.view", "users.create", "users.edit", "users.delete", "users.manage_roles",
        "audit.view"
    ];

    [Fact]
    public void Permissions_ExactSet_NoDuplicates()
    {
        Assert.Equal(19, Permissions.All.Count);
        Assert.Equal(ExpectedPermissions.Length, Permissions.All.Distinct().Count());
        Assert.Equal(
            new HashSet<string>(ExpectedPermissions),
            new HashSet<string>(Permissions.All));
    }

    [Fact]
    public void Roles_ExactSet()
    {
        Assert.Equal(
            new[] { "Admin", "ChiefAccountant", "Accountant", "Viewer", "Auditor" },
            Roles.All.ToArray());
    }

    [Fact]
    public void RolePermissionMap_CoversEveryRole()
    {
        Assert.Equal(
            new HashSet<string>(Roles.All),
            new HashSet<string>(RolePermissionMap.Map.Keys));
    }

    [Fact]
    public void RolePermissionMap_CoversEveryPermission()
    {
        var mapped = new HashSet<string>(RolePermissionMap.Map.Values.SelectMany(p => p));
        Assert.Equal(new HashSet<string>(Permissions.All), mapped);
    }

    [Fact]
    public void RolePermissionMap_ValuesAreKnownPermissions()
    {
        var known = new HashSet<string>(Permissions.All);
        foreach (var (role, perms) in RolePermissionMap.Map)
        {
            Assert.NotEmpty(perms);
            Assert.Equal(perms.Count, perms.Distinct().Count());
            foreach (var perm in perms)
            {
                Assert.Contains(perm, known);
            }
        }
    }

    [Fact]
    public void RolePermissionMap_UnknownRole_ReturnsEmpty()
    {
        Assert.Empty(RolePermissionMap.GetPermissions("NoSuchRole"));
        Assert.Empty(RolePermissionMap.GetPermissions(string.Empty));
    }

    [Fact]
    public void Admin_HasAllPermissions()
    {
        Assert.Equal(
            new HashSet<string>(Permissions.All),
            new HashSet<string>(RolePermissionMap.GetPermissions(Roles.Admin)));
    }

    [Fact]
    public void Catalogs_Parity_IdentityAndAuthorization()
    {
        Assert.Equal(
            new HashSet<string>(IdentityPermissions.All),
            new HashSet<string>(Permissions.All));
    }
}
