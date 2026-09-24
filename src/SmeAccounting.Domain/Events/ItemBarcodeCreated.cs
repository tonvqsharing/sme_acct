namespace SmeAccounting.Domain.Events;

public class ItemBarcodeCreated : DomainEvent
{
    public long ItemBarcodeId { get; }
    public long CompanyId { get; }

    public ItemBarcodeCreated(long itemBarcodeId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        ItemBarcodeId = itemBarcodeId;
        CompanyId = companyId;
    }
}