namespace SmeAccounting.SharedKernel;

public interface IDomainEvent
{
    DateTime OccurredAtUtc { get; }
}

public abstract record DomainEvent(DateTime OccurredAtUtc) : IDomainEvent;