namespace SmeAccounting.Domain.Events;

public class CompanyCreated : DomainEvent
{
    public long CompanyId { get; }

    public CompanyCreated(long companyId, DateTimeOffset occurredOn) : base(occurredOn)
    {
        CompanyId = companyId;
    }
}
