using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public enum ValuationMethod
{
    FIFO,
    LIFO,
    WeightedAverage
}

public class InventoryValuationPolicy : BaseEntity
{
    public long CompanyId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public ValuationMethod ValuationMethod { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private InventoryValuationPolicy() { }

    public InventoryValuationPolicy(long companyId, string code, string name, ValuationMethod method, string? description = null)
    {
        if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code)) throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name)) throw new DomainException("Name is required.");

        CompanyId = companyId;
        Code = code;
        Name = name;
        ValuationMethod = method;
        Description = description;

        AddDomainEvent(new InventoryValuationPolicyCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate() => IsActive = false;
}
