using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class TaxRate : BaseEntity
{
    public long CompanyId { get; private set; }
    public long TaxTypeId { get; private set; }
    public decimal RateValue { get; private set; }
    public string RateName { get; private set; } = string.Empty;
    public DateOnly EffectiveFrom { get; private set; }
    public DateOnly? EffectiveTo { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private TaxRate() { }

    public TaxRate(
        long companyId,
        long taxTypeId,
        decimal rateValue,
        string rateName,
        DateOnly effectiveFrom,
        DateOnly? effectiveTo = null,
        string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (taxTypeId <= 0)
            throw new DomainException("TaxTypeId must be greater than zero.");
        if (rateValue < 0)
            throw new DomainException("RateValue must be greater than or equal to zero.");
        if (string.IsNullOrWhiteSpace(rateName))
            throw new DomainException("RateName is required.");

        CompanyId = companyId;
        TaxTypeId = taxTypeId;
        RateValue = rateValue;
        RateName = rateName;
        EffectiveFrom = effectiveFrom;
        EffectiveTo = effectiveTo;
        Description = description;

        AddDomainEvent(new TaxRateCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
