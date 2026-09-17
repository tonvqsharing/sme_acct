using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class TaxAccountingMapping : BaseEntity
{
    public long CompanyId { get; private set; }
    public long TaxTypeId { get; private set; }
    public long TaxTreatmentId { get; private set; }
    public long AccountId { get; private set; }
    public TaxAccountingMappingType MappingType { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private TaxAccountingMapping() { }

    public TaxAccountingMapping(
        long companyId,
        long taxTypeId,
        long taxTreatmentId,
        long accountId,
        TaxAccountingMappingType mappingType,
        string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (taxTypeId <= 0)
            throw new DomainException("TaxTypeId must be greater than zero.");
        if (taxTreatmentId <= 0)
            throw new DomainException("TaxTreatmentId must be greater than zero.");
        if (accountId <= 0)
            throw new DomainException("AccountId must be greater than zero.");

        CompanyId = companyId;
        TaxTypeId = taxTypeId;
        TaxTreatmentId = taxTreatmentId;
        AccountId = accountId;
        MappingType = mappingType;
        Description = description;

        AddDomainEvent(new TaxAccountingMappingCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
