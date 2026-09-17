namespace SmeAccounting.Domain.Events;

public class CustomerCreated : DomainEvent
{
    public long CustomerId { get; }
    public long CompanyId { get; }

    public CustomerCreated(long customerId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        CustomerId = customerId;
        CompanyId = companyId;
    }
}
