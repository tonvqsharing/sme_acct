using Microsoft.AspNetCore.Identity;

namespace SmeAccounting.Modules.Identity.Infrastructure;

public class ApplicationRole : IdentityRole<long>
{
    public string Description { get; set; } = default!;
    public int DisplayOrder { get; set; }
}
