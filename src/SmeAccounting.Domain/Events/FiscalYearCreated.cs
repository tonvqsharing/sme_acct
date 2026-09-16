namespace SmeAccounting.Domain.Events;

public class FiscalYearCreated : DomainEvent
{
    public long FiscalYearId { get; }
    public long CompanyId { get; }
    public int Year { get; }

    public FiscalYearCreated(
        long fiscalYearId,
        long companyId,
        int year,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        FiscalYearId = fiscalYearId;
        CompanyId = companyId;
        Year = year;
    }
}
