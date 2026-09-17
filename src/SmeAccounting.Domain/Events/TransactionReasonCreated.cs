namespace SmeAccounting.Domain.Events;

public class TransactionReasonCreated : DomainEvent
{
    public long TransactionReasonId { get; }
    public long CompanyId { get; }

    public TransactionReasonCreated(
        long transactionReasonId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TransactionReasonId = transactionReasonId;
        CompanyId = companyId;
    }
}
