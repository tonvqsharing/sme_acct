using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class FiscalYear : BaseEntity
{
    public int Year { get; private set; }
    public FiscalYearStatus Status { get; private set; } = FiscalYearStatus.Open;

    private readonly List<FiscalPeriod> _periods = [];
    public IReadOnlyCollection<FiscalPeriod> Periods => _periods.AsReadOnly();

    private FiscalYear() { }

    public FiscalYear(int year)
    {
        Year = year;
    }

    public FiscalPeriod AddPeriod(int month)
    {
        var period = new FiscalPeriod(Id, month);
        _periods.Add(period);
        return period;
    }
}
