namespace SmeAccounting.Domain.Events;

public class ItemReorderLevelCreated : DomainEvent
{
    public long ItemReorderLevelId { get; }
    public long CompanyId { get; }

    public ItemReorderLevelCreated(long itemReorderLevelId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        ItemReorderLevelId = itemReorderLevelId;
        CompanyId = companyId;
    }
}
