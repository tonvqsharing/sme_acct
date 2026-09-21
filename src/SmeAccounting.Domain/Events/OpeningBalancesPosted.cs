namespace SmeAccounting.Domain.Events;

public class OpeningBalancesPosted : DomainEvent
{
    public long PeriodId { get; }
    public long CompanyId { get; }

    public OpeningBalancesPosted(long periodId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        PeriodId = periodId;
        CompanyId = companyId;
    }
}
