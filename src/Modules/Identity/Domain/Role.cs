using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Identity.Domain;

public class Role : BaseEntity
{
    protected Role()
    {
    }

    public string Name { get; set; } = default!;

    public string NormalizedName { get; set; } = default!;

    public string Description { get; set; } = default!;

    public int DisplayOrder { get; set; }
}
