using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.ValueObjects;

public record AccountCode
{
    public string Value { get; }

    public AccountCode(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
            throw new DomainException("Account code cannot be null or empty.");

        if (!IsNumeric(value))
            throw new DomainException("Account code must be numeric.");

        if (value.Length < 4)
            throw new DomainException("Account code must be at least 4 digits.");

        Value = value;
    }

    private static bool IsNumeric(string value)
    {
        foreach (char c in value)
        {
            if (!char.IsDigit(c))
                return false;
        }
        return true;
    }
}
