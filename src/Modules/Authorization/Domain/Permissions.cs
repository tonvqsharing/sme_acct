namespace SmeAccounting.Modules.Authorization.Domain;

public static class Permissions
{
    public static class Accounts
    {
        public const string View = "accounts.view";
        public const string Create = "accounts.create";
        public const string Edit = "accounts.edit";
        public const string Delete = "accounts.delete";

        public static IReadOnlyList<string> All { get; } = [View, Create, Edit, Delete];
    }

    public static class Journal
    {
        public const string View = "journal.view";
        public const string Create = "journal.create";
        public const string Edit = "journal.edit";
        public const string Post = "journal.post";
        public const string Reverse = "journal.reverse";

        public static IReadOnlyList<string> All { get; } = [View, Create, Edit, Post, Reverse];
    }

    public static class Reports
    {
        public const string View = "reports.view";
        public const string Export = "reports.export";

        public static IReadOnlyList<string> All { get; } = [View, Export];
    }

    public static class Settings
    {
        public const string View = "settings.view";
        public const string Manage = "settings.manage";

        public static IReadOnlyList<string> All { get; } = [View, Manage];
    }

    public static class Users
    {
        public const string View = "users.view";
        public const string Create = "users.create";
        public const string Edit = "users.edit";
        public const string Delete = "users.delete";
        public const string ManageRoles = "users.manage_roles";

        public static IReadOnlyList<string> All { get; } = [View, Create, Edit, Delete, ManageRoles];
    }

    public static class Audit
    {
        public const string View = "audit.view";

        public static IReadOnlyList<string> All { get; } = [View];
    }

    public static IReadOnlyList<string> All { get; } =
    [
        .. Accounts.All,
        .. Journal.All,
        .. Reports.All,
        .. Settings.All,
        .. Users.All,
        .. Audit.All
    ];
}
