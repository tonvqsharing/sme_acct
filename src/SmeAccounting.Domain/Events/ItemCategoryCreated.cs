namespace SmeAccounting.Domain.Events;

public class ItemCategoryCreated : DomainEvent
{
    public long ItemCategoryId { get; }
    public long CompanyId { get; }

    public ItemCategoryCreated(long itemCategoryId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        ItemCategoryId = itemCategoryId;
        CompanyId = companyId;
    }
}
