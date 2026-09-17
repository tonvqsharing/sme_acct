using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class Supplier : BaseEntity
{
    public long CompanyId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public string? TaxCode { get; private set; }
    public string? Address { get; private set; }
    public string? Phone { get; private set; }
    public string? Email { get; private set; }
    public long? PaymentTermId { get; private set; }
    public long? DefaultTaxTypeId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private Supplier() { }

    public Supplier(long companyId, string code, string name, string? taxCode = null, string? address = null, string? phone = null, string? email = null, long? paymentTermId = null, long? defaultTaxTypeId = null, string? description = null)
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
        TaxCode = taxCode;
        Address = address;
        Phone = phone;
        Email = email;
        PaymentTermId = paymentTermId;
        DefaultTaxTypeId = defaultTaxTypeId;
        Description = description;

        AddDomainEvent(new SupplierCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
