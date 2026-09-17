using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class TaxPeriod : BaseEntity
{
    public long CompanyId { get; private set; }
    public long FiscalPeriodId { get; private set; }
    public long TaxTypeId { get; private set; }
    public DateOnly FilingDeadline { get; private set; }
    public FilingFrequency FilingFrequency { get; private set; }
    public TaxPeriodStatus Status { get; private set; } = TaxPeriodStatus.Open;
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private TaxPeriod() { }

    public TaxPeriod(
        long companyId,
        long fiscalPeriodId,
        long taxTypeId,
        FilingFrequency filingFrequency,
        DateOnly filingDeadline,
        string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (fiscalPeriodId <= 0)
            throw new DomainException("FiscalPeriodId must be greater than zero.");
        if (taxTypeId <= 0)
            throw new DomainException("TaxTypeId must be greater than zero.");

        CompanyId = companyId;
        FiscalPeriodId = fiscalPeriodId;
        TaxTypeId = taxTypeId;
        FilingFrequency = filingFrequency;
        FilingDeadline = filingDeadline;
        Description = description;

        AddDomainEvent(new TaxPeriodCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void MarkFiled()
    {
        if (Status != TaxPeriodStatus.Open)
            throw new DomainException("Only open tax periods can be marked as filed.");
        Status = TaxPeriodStatus.Filed;
    }

    public void Close()
    {
        if (Status != TaxPeriodStatus.Filed)
            throw new DomainException("Only filed tax periods can be closed.");
        Status = TaxPeriodStatus.Closed;
        AddDomainEvent(new TaxPeriodClosed(Id, CompanyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
