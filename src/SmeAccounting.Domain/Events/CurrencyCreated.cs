namespace SmeAccounting.Domain.Events;

public class CurrencyCreated : DomainEvent
{
    public long CurrencyId { get; }

    public CurrencyCreated(long currencyId, DateTimeOffset occurredOn) : base(occurredOn)
    {
        CurrencyId = currencyId;
    }
}
