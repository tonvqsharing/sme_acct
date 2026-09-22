using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class BankBranch : BaseEntity
{
    public long CompanyId { get; private set; }
    public long BankId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private BankBranch() { }

    public BankBranch(long companyId, long bankId, string code, string name, string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (bankId <= 0)
            throw new DomainException("BankId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");

        CompanyId = companyId;
        BankId = bankId;
        Code = code;
        Name = name;
        Description = description;

        AddDomainEvent(new BankBranchCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
