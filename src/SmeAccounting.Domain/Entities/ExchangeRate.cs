using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class ExchangeRate : BaseEntity
{
    public long CompanyId { get; private set; }
    public string FromCurrencyCode { get; private set; } = string.Empty;
    public string ToCurrencyCode { get; private set; } = string.Empty;
    public decimal Rate { get; private set; }
    public ExchangeRateType RateType { get; private set; }
    public DateOnly EffectiveDate { get; private set; }
    public string? Source { get; private set; }

    private ExchangeRate() { }

    public ExchangeRate(
        long companyId,
        string fromCurrencyCode,
        string toCurrencyCode,
        decimal rate,
        ExchangeRateType rateType,
        DateOnly effectiveDate,
        string? source = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(fromCurrencyCode))
            throw new DomainException("FromCurrencyCode is required.");
        if (string.IsNullOrWhiteSpace(toCurrencyCode))
            throw new DomainException("ToCurrencyCode is required.");
        if (fromCurrencyCode.Equals(toCurrencyCode, StringComparison.OrdinalIgnoreCase))
            throw new DomainException("FromCurrencyCode and ToCurrencyCode must be different.");
        if (rate <= 0)
            throw new DomainException("Rate must be greater than zero.");

        CompanyId = companyId;
        FromCurrencyCode = fromCurrencyCode.ToUpperInvariant();
        ToCurrencyCode = toCurrencyCode.ToUpperInvariant();
        Rate = rate;
        RateType = rateType;
        EffectiveDate = effectiveDate;
        Source = source;

        AddDomainEvent(new ExchangeRateRecorded(Id, companyId, DateTimeOffset.UtcNow));
    }
}
