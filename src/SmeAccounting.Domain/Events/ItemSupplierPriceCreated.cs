namespace SmeAccounting.Domain.Events;

public class ItemSupplierPriceCreated : DomainEvent
{
    public long ItemSupplierPriceId { get; }
    public long CompanyId { get; }

    public ItemSupplierPriceCreated(long itemSupplierPriceId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        ItemSupplierPriceId = itemSupplierPriceId;
        CompanyId = companyId;
    }
}
