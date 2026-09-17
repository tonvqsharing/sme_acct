namespace SmeAccounting.Domain.Events;

public class TaxTypeCreated : DomainEvent
{
    public long TaxTypeId { get; }
    public long CompanyId { get; }

    public TaxTypeCreated(
        long taxTypeId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxTypeId = taxTypeId;
        CompanyId = companyId;
    }
}
