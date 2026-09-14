using Microsoft.AspNetCore.Identity;

namespace SmeAccounting.Modules.Identity.Infrastructure;

public class ApplicationUser : IdentityUser<long>
{
    public string DisplayName { get; set; } = default!;
    public long? BranchId { get; set; }
    public bool IsEnabled { get; set; } = true;
    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;
    public DateTime? LastLoginAtUtc { get; set; }
}
