namespace SmeAccounting.Domain.Events;

public class SupplierCreated : DomainEvent
{
    public long SupplierId { get; }
    public long CompanyId { get; }

    public SupplierCreated(long supplierId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        SupplierId = supplierId;
        CompanyId = companyId;
    }
}
