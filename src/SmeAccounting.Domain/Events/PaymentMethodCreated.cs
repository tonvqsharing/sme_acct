namespace SmeAccounting.Domain.Events;

public class PaymentMethodCreated : DomainEvent
{
    public long PaymentMethodId { get; }
    public long CompanyId { get; }

    public PaymentMethodCreated(long paymentMethodId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        PaymentMethodId = paymentMethodId;
        CompanyId = companyId;
    }
}
