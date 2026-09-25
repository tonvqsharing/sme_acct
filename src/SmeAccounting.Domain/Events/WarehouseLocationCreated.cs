using SmeAccounting.Domain.Events;

namespace SmeAccounting.Domain.Events;

public sealed class WarehouseLocationCreated : DomainEvent
{
    public long WarehouseLocationId { get; }
    public long CompanyId { get; }

    public WarehouseLocationCreated(long warehouseLocationId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        WarehouseLocationId = warehouseLocationId;
        CompanyId = companyId;
    }
}