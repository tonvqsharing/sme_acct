using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class TaxRule : BaseEntity
{
    public long CompanyId { get; private set; }
    public long TaxTypeId { get; private set; }
    public long? TaxRateId { get; private set; }
    public long TaxTreatmentId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public string? Conditions { get; private set; }
    public string LegalReference { get; private set; } = string.Empty;
    public DateOnly EffectiveFrom { get; private set; }
    public DateOnly? EffectiveTo { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private TaxRule() { }

    public TaxRule(
        long companyId,
        long taxTypeId,
        long? taxRateId,
        long taxTreatmentId,
        string code,
        string name,
        string legalReference,
        DateOnly effectiveFrom,
        DateOnly? effectiveTo = null,
        string? conditions = null,
        string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (taxTypeId <= 0)
            throw new DomainException("TaxTypeId must be greater than zero.");
        if (taxRateId.HasValue && taxRateId.Value <= 0)
            throw new DomainException("TaxRateId must be greater than zero when provided.");
        if (taxTreatmentId <= 0)
            throw new DomainException("TaxTreatmentId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");
        if (string.IsNullOrWhiteSpace(legalReference))
            throw new DomainException("LegalReference is required for audit traceability.");

        CompanyId = companyId;
        TaxTypeId = taxTypeId;
        TaxRateId = taxRateId;
        TaxTreatmentId = taxTreatmentId;
        Code = code;
        Name = name;
        Conditions = conditions;
        LegalReference = legalReference;
        EffectiveFrom = effectiveFrom;
        EffectiveTo = effectiveTo;
        Description = description;

        AddDomainEvent(new TaxRuleCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
