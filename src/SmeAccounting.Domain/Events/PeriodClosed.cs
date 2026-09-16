namespace SmeAccounting.Domain.Events;

public class PeriodClosed : DomainEvent
{
    public long PeriodId { get; }

    public PeriodClosed(long periodId, DateTimeOffset occurredOn) : base(occurredOn)
    {
        PeriodId = periodId;
    }
}
