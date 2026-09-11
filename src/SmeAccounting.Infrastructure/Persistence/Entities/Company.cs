using SmeAccounting.SharedKernel;

namespace SmeAccounting.Infrastructure.Persistence.Entities;

public class Company : BaseEntity, IAuditable, ISoftDeletable
{
    public string Name { get; set; } = default!;
    public string Code { get; set; } = default!;
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAtUtc { get; set; }
    public Guid? CreatedBy { get; set; }
    public DateTime? UpdatedAtUtc { get; set; }
    public Guid? UpdatedBy { get; set; }
    public bool IsDeleted { get; set; }
    public DateTime? DeletedAtUtc { get; set; }
    public Guid? DeletedBy { get; set; }

    public ICollection<Branch> Branches { get; set; } = [];
}
