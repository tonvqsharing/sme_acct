namespace SmeAccounting.Domain.Events;

public class ExchangeRateRecorded : DomainEvent
{
    public long ExchangeRateId { get; }
    public long CompanyId { get; }

    public ExchangeRateRecorded(
        long exchangeRateId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        ExchangeRateId = exchangeRateId;
        CompanyId = companyId;
    }
}
