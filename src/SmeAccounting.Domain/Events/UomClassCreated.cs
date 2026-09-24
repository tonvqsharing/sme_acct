namespace SmeAccounting.Domain.Events;

public class UomClassCreated : DomainEvent
{
    public long UomClassId { get; }
    public long CompanyId { get; }

    public UomClassCreated(long uomClassId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        UomClassId = uomClassId;
        CompanyId = companyId;
    }
}