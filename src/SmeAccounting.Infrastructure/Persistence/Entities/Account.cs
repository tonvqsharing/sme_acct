using SmeAccounting.SharedKernel;

namespace SmeAccounting.Infrastructure.Persistence.Entities;

public class Account : BaseEntity, IAuditable, ISoftDeletable, ICompanyScoped
{
    public long CompanyId { get; set; }
    public string Code { get; set; } = default!;
    public string Name { get; set; } = default!;
    public string AccountType { get; set; } = default!;
    public int Level { get; set; }
    public long? ParentId { get; set; }
    public string NormalBalance { get; set; } = "Debit";
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAtUtc { get; set; }
    public Guid? CreatedBy { get; set; }
    public DateTime? UpdatedAtUtc { get; set; }
    public Guid? UpdatedBy { get; set; }
    public bool IsDeleted { get; set; }
    public DateTime? DeletedAtUtc { get; set; }
    public Guid? DeletedBy { get; set; }

    public Account? Parent { get; set; }
    public ICollection<Account> Children { get; set; } = [];
}
