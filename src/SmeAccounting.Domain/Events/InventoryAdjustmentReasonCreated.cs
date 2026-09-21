namespace SmeAccounting.Domain.Events;
public class InventoryAdjustmentReasonCreated : DomainEvent
{
    public long ReasonId { get; }
    public long CompanyId { get; }
    public InventoryAdjustmentReasonCreated(long reasonId, long companyId, DateTimeOffset occurredOn) : base(occurredOn) { ReasonId = reasonId; CompanyId = companyId; }
}
