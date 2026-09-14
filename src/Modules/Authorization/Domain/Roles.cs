namespace SmeAccounting.Modules.Authorization.Domain;

public static class Roles
{
    public const string Admin = "Admin";
    public const string ChiefAccountant = "ChiefAccountant";
    public const string Accountant = "Accountant";
    public const string Viewer = "Viewer";
    public const string Auditor = "Auditor";

    public static IReadOnlyList<string> All { get; } = [Admin, ChiefAccountant, Accountant, Viewer, Auditor];
}
