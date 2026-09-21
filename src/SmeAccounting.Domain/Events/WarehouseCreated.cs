namespace SmeAccounting.Domain.Events;

public class WarehouseCreated : DomainEvent
{
    public long WarehouseId { get; }
    public long CompanyId { get; }

    public WarehouseCreated(long warehouseId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        WarehouseId = warehouseId;
        CompanyId = companyId;
    }
}
