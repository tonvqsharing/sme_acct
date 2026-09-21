namespace SmeAccounting.Domain.Events;

public class ItemCreated : DomainEvent
{
    public long ItemId { get; }
    public long CompanyId { get; }

    public ItemCreated(long itemId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        ItemId = itemId;
        CompanyId = companyId;
    }
}
