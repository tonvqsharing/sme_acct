using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class ServiceItem : BaseEntity
{
    public long CompanyId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public long? UomId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private ServiceItem() { }

    public ServiceItem(long companyId, string code, string name, long? uomId = null, string? description = null)
    {
        if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code)) throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name)) throw new DomainException("Name is required.");

        CompanyId = companyId;
        Code = code;
        Name = name;
        UomId = uomId;
        Description = description;

        AddDomainEvent(new ServiceItemCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate() => IsActive = false;
}
