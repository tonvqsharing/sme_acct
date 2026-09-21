namespace SmeAccounting.Domain.Events;

public class UomCreated : DomainEvent
{
    public long UomId { get; }
    public long CompanyId { get; }

    public UomCreated(
        long uomId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        UomId = uomId;
        CompanyId = companyId;
    }
}
