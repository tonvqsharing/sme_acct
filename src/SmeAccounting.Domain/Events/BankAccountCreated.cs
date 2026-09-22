namespace SmeAccounting.Domain.Events;

public class BankAccountCreated : DomainEvent
{
    public long BankAccountId { get; }
    public long CompanyId { get; }

    public BankAccountCreated(long bankAccountId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        BankAccountId = bankAccountId;
        CompanyId = companyId;
    }
}
