using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class TaxType : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public TaxCategory TaxCategory { get; private set; }
    public long CompanyId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private TaxType() { }

    public TaxType(long companyId, string code, string name, TaxCategory taxCategory, string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");

        CompanyId = companyId;
        Code = code;
        Name = name;
        TaxCategory = taxCategory;
        Description = description;

        AddDomainEvent(new TaxTypeCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
