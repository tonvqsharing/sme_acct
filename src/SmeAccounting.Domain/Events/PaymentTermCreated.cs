namespace SmeAccounting.Domain.Events;

public class PaymentTermCreated : DomainEvent
{
    public long PaymentTermId { get; }
    public long CompanyId { get; }

    public PaymentTermCreated(long paymentTermId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        PaymentTermId = paymentTermId;
        CompanyId = companyId;
    }
}
