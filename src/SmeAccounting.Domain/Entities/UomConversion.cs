using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class UomConversion : BaseEntity
{
    public long CompanyId { get; private set; }
    public long FromUomId { get; private set; }
    public long ToUomId { get; private set; }
    public decimal Factor { get; private set; }
    public bool IsActive { get; private set; } = true;

    private UomConversion() { }

    public UomConversion(long companyId, long fromUomId, long toUomId, decimal factor)
    {
        if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");
        if (fromUomId <= 0) throw new DomainException("FromUomId must be greater than zero.");
        if (toUomId <= 0) throw new DomainException("ToUomId must be greater than zero.");
        if (fromUomId == toUomId) throw new DomainException("FromUomId and ToUomId must be different.");
        if (factor <= 0) throw new DomainException("Factor must be greater than zero.");

        CompanyId = companyId;
        FromUomId = fromUomId;
        ToUomId = toUomId;
        Factor = factor;

        AddDomainEvent(new UomConversionCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate() => IsActive = false;
}
