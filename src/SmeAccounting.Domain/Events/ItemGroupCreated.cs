namespace SmeAccounting.Domain.Events;

public class ItemGroupCreated : DomainEvent
{
    public long ItemGroupId { get; }
    public long CompanyId { get; }

    public ItemGroupCreated(
        long itemGroupId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        ItemGroupId = itemGroupId;
        CompanyId = companyId;
    }
}