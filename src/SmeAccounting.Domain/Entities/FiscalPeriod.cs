using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class FiscalPeriod : BaseEntity
{
    public long YearId { get; private set; }
    public int Month { get; private set; }
    public DateOnly StartDate { get; private set; }
    public DateOnly EndDate { get; private set; }
    public PeriodType PeriodType { get; private set; }
    public PeriodStatus Status { get; private set; } = PeriodStatus.Open;
    public DateTimeOffset? OpenedAt { get; private set; }
    public DateTimeOffset? ClosedAt { get; private set; }

    private FiscalPeriod() { }

    public FiscalPeriod(
        long yearId,
        int month,
        DateOnly startDate,
        DateOnly endDate,
        PeriodType periodType)
    {
        YearId = yearId;
        Month = month;
        StartDate = startDate;
        EndDate = endDate;
        PeriodType = periodType;
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
