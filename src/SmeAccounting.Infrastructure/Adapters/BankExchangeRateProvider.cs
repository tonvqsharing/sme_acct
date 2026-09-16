using SmeAccounting.Domain.Ports;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Infrastructure.Adapters;

public class BankExchangeRateProvider : IForeignExchangeRateProvider
{
    public Task<Money> ConvertAsync(Money amount, string targetCurrency, DateTimeOffset date)
    {
        if (amount.Currency == targetCurrency)
            return Task.FromResult(amount);

        decimal mockRate = amount.Currency switch
        {
            "VND" when targetCurrency == "USD" => 25000m,
            "USD" when targetCurrency == "VND" => 25000m,
            "VND" when targetCurrency == "EUR" => 27000m,
            "EUR" when targetCurrency == "VND" => 27000m,
            _ => 1m
        };

        var converted = amount.Currency == "VND" || amount.Currency == "EUR"
            ? amount.Amount / mockRate
            : amount.Amount * mockRate;

        return Task.FromResult(new Money(converted, targetCurrency));
    }
}
