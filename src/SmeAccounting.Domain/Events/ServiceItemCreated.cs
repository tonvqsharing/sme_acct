namespace SmeAccounting.Domain.Events;

public class ServiceItemCreated : DomainEvent
{
    public long ServiceItemId { get; }
    public long CompanyId { get; }

    public ServiceItemCreated(long serviceItemId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        ServiceItemId = serviceItemId;
        CompanyId = companyId;
    }
}
