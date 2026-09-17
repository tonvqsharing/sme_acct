namespace SmeAccounting.Domain.Events;

public class TaxAccountingMappingCreated : DomainEvent
{
    public long TaxAccountingMappingId { get; }
    public long CompanyId { get; }

    public TaxAccountingMappingCreated(
        long taxAccountingMappingId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxAccountingMappingId = taxAccountingMappingId;
        CompanyId = companyId;
    }
}
