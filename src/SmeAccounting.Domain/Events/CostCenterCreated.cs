namespace SmeAccounting.Domain.Events;

public class CostCenterCreated : DomainEvent
{
    public long CostCenterId { get; }
    public long CompanyId { get; }

    public CostCenterCreated(
        long costCenterId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        CostCenterId = costCenterId;
        CompanyId = companyId;
    }
}
