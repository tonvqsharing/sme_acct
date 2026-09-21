namespace SmeAccounting.Domain.Events;

public class UomConversionCreated : DomainEvent
{
    public long UomConversionId { get; }
    public long CompanyId { get; }

    public UomConversionCreated(long uomConversionId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        UomConversionId = uomConversionId;
        CompanyId = companyId;
    }
}
