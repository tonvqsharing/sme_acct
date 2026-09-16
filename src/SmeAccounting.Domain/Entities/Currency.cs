using SmeAccounting.Domain.Events;

namespace SmeAccounting.Domain.Entities;

public class Currency : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public string Symbol { get; private set; } = string.Empty;
    public int DecimalPlaces { get; private set; } = 2;
    public bool IsDefault { get; private set; }
    public bool IsActive { get; private set; } = true;

    private Currency() { }

    public Currency(string code, string name, string symbol, int decimalPlaces = 2, bool isDefault = false)
    {
        Code = code ?? throw new ArgumentNullException(nameof(code));
        Name = name ?? throw new ArgumentNullException(nameof(name));
        Symbol = symbol ?? throw new ArgumentNullException(nameof(symbol));

        if (code.Length != 3 || !code.Equals(code.ToUpperInvariant(), StringComparison.Ordinal))
            throw new ArgumentException("Currency code must be 3 uppercase characters (ISO 4217).", nameof(code));

        DecimalPlaces = decimalPlaces;
        IsDefault = isDefault;

        AddDomainEvent(new CurrencyCreated(Id, DateTimeOffset.UtcNow));
    }
}
