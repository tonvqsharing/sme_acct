using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Ports;

public interface IExchangeRateRepository
{
    Task<ExchangeRate?> GetByIdAsync(long id);
    Task<ExchangeRate?> GetByCurrencyPairAsync(string fromCurrencyCode, string toCurrencyCode, ExchangeRateType rateType, DateOnly effectiveDate);
    Task<IReadOnlyList<ExchangeRate>> GetAllAsync();
    Task AddAsync(ExchangeRate exchangeRate);
}
