using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class TaxTreatment : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public long TaxTypeId { get; private set; }
    public TaxTreatmentType TaxTreatmentType { get; private set; }
    public bool InputCreditAllowed { get; private set; }
    public long CompanyId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private TaxTreatment() { }

    public TaxTreatment(
        long companyId,
        long taxTypeId,
        string code,
        string name,
        TaxTreatmentType taxTreatmentType,
        bool inputCreditAllowed,
        string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (taxTypeId <= 0)
            throw new DomainException("TaxTypeId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");

        CompanyId = companyId;
        TaxTypeId = taxTypeId;
        Code = code;
        Name = name;
        TaxTreatmentType = taxTreatmentType;
        InputCreditAllowed = inputCreditAllowed;
        Description = description;

        AddDomainEvent(new TaxTreatmentCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
