using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class FiscalYear : BaseEntity
{
    public long CompanyId { get; private set; }
    public int Year { get; private set; }
    public DateOnly StartDate { get; private set; }
    public DateOnly EndDate { get; private set; }
    public string? Description { get; private set; }
    public FiscalYearStatus Status { get; private set; } = FiscalYearStatus.Open;

    private readonly List<FiscalPeriod> _periods = [];
    public IReadOnlyCollection<FiscalPeriod> Periods => _periods.AsReadOnly();

    private FiscalYear() { }

    public FiscalYear(
        long companyId,
        int year,
        DateOnly startDate,
        DateOnly endDate,
        string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (startDate >= endDate)
            throw new DomainException("StartDate must be before EndDate.");

        CompanyId = companyId;
        Year = year;
        StartDate = startDate;
        EndDate = endDate;
        Description = description;

        AddDomainEvent(new FiscalYearCreated(Id, companyId, year, DateTimeOffset.UtcNow));
    }

    public FiscalPeriod AddPeriod(int month, DateOnly startDate, DateOnly endDate, PeriodType periodType)
    {
        var period = new FiscalPeriod(Id, month, startDate, endDate, periodType);
        _periods.Add(period);
        return period;
    }
}
