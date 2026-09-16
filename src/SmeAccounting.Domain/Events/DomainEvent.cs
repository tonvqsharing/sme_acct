namespace SmeAccounting.Domain.Events;

public abstract class DomainEvent
{
    public DateTimeOffset OccurredOn { get; }
    public Guid EventId { get; }

    protected DomainEvent(DateTimeOffset occurredOn)
    {
        OccurredOn = occurredOn;
        EventId = Guid.NewGuid();
    }
}
