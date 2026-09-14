namespace SmeAccounting.Modules.Authorization.Domain;

public static class RolePermissionMap
{
    public static IReadOnlyDictionary<string, IReadOnlyList<string>> Map { get; } = new Dictionary<string, IReadOnlyList<string>>
    {
        [Roles.Admin] = Permissions.All,
        [Roles.ChiefAccountant] = [
            .. Permissions.Accounts.All,
            .. Permissions.Journal.All,
            .. Permissions.Reports.All,
            .. Permissions.Settings.All
        ],
        [Roles.Accountant] = [
            Permissions.Accounts.View,
            Permissions.Accounts.Create,
            Permissions.Accounts.Edit,
            Permissions.Journal.View,
            Permissions.Journal.Create,
            Permissions.Journal.Edit,
            Permissions.Reports.View
        ],
        [Roles.Viewer] = [
            Permissions.Accounts.View,
            Permissions.Journal.View,
            Permissions.Reports.View,
            Permissions.Audit.View
        ],
        [Roles.Auditor] = [
            Permissions.Audit.View,
            Permissions.Accounts.View,
            Permissions.Journal.View,
            Permissions.Reports.View,
            Permissions.Reports.Export
        ]
    };

    public static IReadOnlyList<string> GetPermissions(string roleName)
    {
        return Map.TryGetValue(roleName, out var perms) ? perms : [];
    }
}
