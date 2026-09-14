using SmeAccounting.Infrastructure.Identity;
using System.Reflection;

namespace SmeAccounting.Security.Tests;

public class PermissionTests
{
    [Fact]
    public void AllPermissions_AreNonEmpty()
    {
        Assert.NotEmpty(Permissions.All);
    }

    [Fact]
    public void AllPermissions_HaveCorrectFormat()
    {
        foreach (var permission in Permissions.All)
        {
            Assert.Contains(".", permission);
            var parts = permission.Split('.');
            Assert.Equal(2, parts.Length);
            Assert.NotEmpty(parts[0]);
            Assert.NotEmpty(parts[1]);
        }
    }

    [Fact]
    public void EachModule_HasViewPermission()
    {
        Assert.Contains(Permissions.Accounts.View, Permissions.All);
        Assert.Contains(Permissions.Journal.View, Permissions.All);
        Assert.Contains(Permissions.Reports.View, Permissions.All);
    }

    [Fact]
    public void AdminRole_HasAllPermissions()
    {
        var adminPerms = RoleSeeder.StandardRoles
            .First(r => r.Name == "Admin")
            .Permissions;

        Assert.Equal(Permissions.All.Count, adminPerms.Count);
    }

    [Fact]
    public void ViewerRole_OnlyHasViewPermissions()
    {
        var viewerPerms = RoleSeeder.StandardRoles
            .First(r => r.Name == "Viewer")
            .Permissions;

        foreach (var perm in viewerPerms)
        {
            Assert.EndsWith(".view", perm);
        }
    }

    [Fact]
    public void PermissionConstants_AreUnique()
    {
        var allPerms = typeof(Permissions)
            .GetNestedTypes(BindingFlags.Public | BindingFlags.Static)
            .SelectMany(t => t.GetFields(BindingFlags.Public | BindingFlags.Static | BindingFlags.FlattenHierarchy))
            .Where(f => f.FieldType == typeof(string))
            .Select(f => (string)f.GetValue(null)!)
            .ToList();

        Assert.Equal(allPerms.Count, allPerms.Distinct().Count());
    }
}
