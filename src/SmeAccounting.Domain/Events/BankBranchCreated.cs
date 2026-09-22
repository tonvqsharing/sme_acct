namespace SmeAccounting.Domain.Events;

public class BankBranchCreated : DomainEvent
{
    public long BankBranchId { get; }
    public long CompanyId { get; }

    public BankBranchCreated(long bankBranchId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        BankBranchId = bankBranchId;
        CompanyId = companyId;
    }
}
