using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class ItemTaxClass : BaseEntity
{
    public long CompanyId { get; private set; }
    public long ItemId { get; private set; }
    public long TaxTypeId { get; private set; }
    public DateOnly EffectiveFrom { get; private set; }
    public DateOnly? EffectiveTo { get; private set; }
    public bool IsActive { get; private set; } = true;

    private ItemTaxClass() { }

    public ItemTaxClass(
        long companyId,
        long itemId,
        long taxTypeId,
        DateOnly effectiveFrom,
        DateOnly? effectiveTo = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (itemId <= 0)
            throw new DomainException("ItemId must be greater than zero.");
        if (taxTypeId <= 0)
            throw new DomainException("TaxTypeId must be greater than zero.");
        if (effectiveTo.HasValue && effectiveTo < effectiveFrom)
            throw new DomainException("EffectiveTo must be on or after EffectiveFrom.");

        CompanyId = companyId;
        ItemId = itemId;
        TaxTypeId = taxTypeId;
        EffectiveFrom = effectiveFrom;
        EffectiveTo = effectiveTo;

        AddDomainEvent(new ItemTaxClassCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}