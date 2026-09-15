using System.Security.Claims;

namespace SmeAccounting.Modules.Authorization.Application.Authorization;

public static class ClaimsPrincipalExtensions
{
    public static long? GetUserId(this ClaimsPrincipal principal)
    {
        var claim = principal.FindFirst(ClaimTypes.NameIdentifier);
        return claim is not null && long.TryParse(claim.Value, out var id) ? id : null;
    }

    public static string? GetDisplayName(this ClaimsPrincipal principal)
    {
        return principal.FindFirst("display_name")?.Value
            ?? principal.FindFirst(ClaimTypes.Name)?.Value;
    }

    public static long? GetBranchId(this ClaimsPrincipal principal)
    {
        var claim = principal.FindFirst("branch_id");
        return claim is not null && long.TryParse(claim.Value, out var id) ? id : null;
    }

    public static IReadOnlyList<string> GetPermissions(this ClaimsPrincipal principal)
    {
        return principal.FindAll("permission").Select(c => c.Value).ToList();
    }

    public static bool HasPermission(this ClaimsPrincipal principal, string permission)
    {
        return principal.GetPermissions().Contains(permission);
    }
}
