using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class WarehouseLocation : BaseEntity
{
    public long CompanyId { get; private set; }
    public long WarehouseId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private WarehouseLocation() { }

    public WarehouseLocation(
        long companyId,
        long warehouseId,
        string code,
        string name,
        string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (warehouseId <= 0)
            throw new DomainException("WarehouseId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");

        CompanyId = companyId;
        WarehouseId = warehouseId;
        Code = code;
        Name = name;
        Description = description;

        AddDomainEvent(new WarehouseLocationCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}