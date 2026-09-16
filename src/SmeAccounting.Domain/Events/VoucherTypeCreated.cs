namespace SmeAccounting.Domain.Events;

public class VoucherTypeCreated : DomainEvent
{
    public long VoucherTypeId { get; }
    public long CompanyId { get; }

    public VoucherTypeCreated(
        long voucherTypeId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        VoucherTypeId = voucherTypeId;
        CompanyId = companyId;
    }
}
