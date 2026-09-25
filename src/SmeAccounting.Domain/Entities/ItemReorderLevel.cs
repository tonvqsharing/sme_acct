using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class ItemReorderLevel : BaseEntity
{
    public long CompanyId { get; private set; }
    public long ItemId { get; private set; }
    public long? WarehouseId { get; private set; }
    public decimal MinimumQuantity { get; private set; }
    public decimal? MaximumQuantity { get; private set; }
    public bool IsActive { get; private set; } = true;

    private ItemReorderLevel() { }

    public ItemReorderLevel(long companyId, long itemId, decimal minimumQuantity, long? warehouseId = null, decimal? maximumQuantity = null)
    {
        if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");
        if (itemId <= 0) throw new DomainException("ItemId must be greater than zero.");
        if (warehouseId.HasValue && warehouseId <= 0) throw new DomainException("WarehouseId must be greater than zero when specified.");
        if (minimumQuantity < 0) throw new DomainException("MinimumQuantity must be greater than or equal to zero.");
        if (maximumQuantity.HasValue && maximumQuantity < minimumQuantity) throw new DomainException("MaximumQuantity must be greater than or equal to MinimumQuantity.");

        CompanyId = companyId;
        ItemId = itemId;
        WarehouseId = warehouseId;
        MinimumQuantity = minimumQuantity;
        MaximumQuantity = maximumQuantity;

        AddDomainEvent(new ItemReorderLevelCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate() => IsActive = false;
}
