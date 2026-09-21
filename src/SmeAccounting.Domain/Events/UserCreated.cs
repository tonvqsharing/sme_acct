namespace SmeAccounting.Domain.Events;

public class UserCreated : DomainEvent
{
    public long UserId { get; }

    public UserCreated(long userId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        UserId = userId;
    }
}
