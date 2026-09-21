namespace SmeAccounting.Domain.Events;

public class OpeningBalancePeriodCreated : DomainEvent
{
    public long PeriodId { get; }
    public long CompanyId { get; }

    public OpeningBalancePeriodCreated(long periodId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        PeriodId = periodId;
        CompanyId = companyId;
    }
}
