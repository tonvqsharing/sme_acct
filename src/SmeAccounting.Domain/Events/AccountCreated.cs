namespace SmeAccounting.Domain.Events;

public class AccountCreated : DomainEvent
{
    public long AccountId { get; }

    public AccountCreated(long accountId, DateTimeOffset occurredOn) : base(occurredOn)
    {
        AccountId = accountId;
    }
}
