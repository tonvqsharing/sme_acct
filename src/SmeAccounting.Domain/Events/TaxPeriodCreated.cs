namespace SmeAccounting.Domain.Events;

public class TaxPeriodCreated : DomainEvent
{
    public long TaxPeriodId { get; }
    public long CompanyId { get; }

    public TaxPeriodCreated(
        long taxPeriodId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxPeriodId = taxPeriodId;
        CompanyId = companyId;
    }
}
