using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Ports;

public interface IForeignExchangeRateProvider
{
    Task<Money> ConvertAsync(Money amount, string targetCurrency, DateTimeOffset date);
}
