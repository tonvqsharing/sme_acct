using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class Uom : BaseEntity
{
    public long CompanyId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public string? Symbol { get; private set; }
    public long? UomClassId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private Uom() { }

    public Uom(long companyId, string code, string name, string? symbol = null, string? description = null, long? uomClassId = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");
        if (uomClassId.HasValue && uomClassId <= 0)
            throw new DomainException("UomClassId must be greater than zero when specified.");

        CompanyId = companyId;
        Code = code;
        Name = name;
        Symbol = symbol;
        UomClassId = uomClassId;
        Description = description;

        AddDomainEvent(new UomCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
