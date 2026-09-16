using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class FiscalPeriod : BaseEntity
{
    public long YearId { get; private set; }
    public int Month { get; private set; }
    public PeriodStatus Status { get; private set; } = PeriodStatus.Open;
    public DateTimeOffset? OpenedAt { get; private set; }
    public DateTimeOffset? ClosedAt { get; private set; }

    private FiscalPeriod() { }

    public FiscalPeriod(long yearId, int month)
    {
        YearId = yearId;
        Month = month;
    }

    public void Open(DateTimeOffset openedAt)
    {
        Status = PeriodStatus.Open;
        OpenedAt = openedAt;
    }

    public void Close(DateTimeOffset closedAt)
    {
        Status = PeriodStatus.Closed;
        ClosedAt = closedAt;
        AddDomainEvent(new PeriodClosed(Id, closedAt));
    }
}
