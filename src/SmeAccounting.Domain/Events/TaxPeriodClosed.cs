namespace SmeAccounting.Domain.Events;

public class TaxPeriodClosed : DomainEvent
{
    public long TaxPeriodId { get; }
    public long CompanyId { get; }

    public TaxPeriodClosed(
        long taxPeriodId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxPeriodId = taxPeriodId;
        CompanyId = companyId;
    }
}
