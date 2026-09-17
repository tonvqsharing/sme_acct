using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class TaxExemptionReason : BaseEntity
{
    public long CompanyId { get; private set; }
    public long TaxTypeId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public string LegalBasis { get; private set; } = string.Empty;
    public string? Description { get; private set; }
    public bool IsActive { get; private set; } = true;

    private TaxExemptionReason() { }

    public TaxExemptionReason(
        long companyId,
        long taxTypeId,
        string code,
        string name,
        string legalBasis,
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
        if (string.IsNullOrWhiteSpace(legalBasis))
            throw new DomainException("LegalBasis is required for audit traceability.");

        CompanyId = companyId;
        TaxTypeId = taxTypeId;
        Code = code;
        Name = name;
        LegalBasis = legalBasis;
        Description = description;

        AddDomainEvent(new TaxExemptionReasonCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
