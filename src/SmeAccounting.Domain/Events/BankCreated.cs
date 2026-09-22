namespace SmeAccounting.Domain.Events;

public class BankCreated : DomainEvent
{
    public long BankId { get; }
    public long CompanyId { get; }

    public BankCreated(long bankId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        BankId = bankId;
        CompanyId = companyId;
    }
}
