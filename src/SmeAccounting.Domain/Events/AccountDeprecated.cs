namespace SmeAccounting.Domain.Events;

public class AccountDeprecated : DomainEvent
{
    public long AccountId { get; }

    public AccountDeprecated(long accountId, DateTimeOffset occurredOn) : base(occurredOn)
    {
        AccountId = accountId;
    }
}
