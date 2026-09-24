namespace SmeAccounting.Domain.Events;

public class PriceListCreated : DomainEvent
{
    public long PriceListId { get; }
    public long CompanyId { get; }

    public PriceListCreated(long priceListId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        PriceListId = priceListId;
        CompanyId = companyId;
    }
}