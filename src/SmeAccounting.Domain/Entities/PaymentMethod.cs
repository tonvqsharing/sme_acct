using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class PaymentMethod : BaseEntity
{
    public long CompanyId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public PaymentMethodCategory Category { get; private set; }
    public bool RequiresBankAccount { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private PaymentMethod() { }

    public PaymentMethod(long companyId, string code, string name, PaymentMethodCategory category, bool requiresBankAccount = false, string? description = null)
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
        Category = category;
        RequiresBankAccount = requiresBankAccount;
        Description = description;

        AddDomainEvent(new PaymentMethodCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
