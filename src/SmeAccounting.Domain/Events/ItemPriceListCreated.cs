namespace SmeAccounting.Domain.Events;

public class ItemPriceListCreated : DomainEvent
{
    public long ItemPriceListId { get; }
    public long CompanyId { get; }

    public ItemPriceListCreated(long itemPriceListId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        ItemPriceListId = itemPriceListId;
        CompanyId = companyId;
    }
}