namespace SmeAccounting.Domain.Events;

public class TaxRateCreated : DomainEvent
{
    public long TaxRateId { get; }
    public long CompanyId { get; }

    public TaxRateCreated(
        long taxRateId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxRateId = taxRateId;
        CompanyId = companyId;
    }
}
