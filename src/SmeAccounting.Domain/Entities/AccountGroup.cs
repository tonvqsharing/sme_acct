using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class AccountGroup : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public AccountType AccountType { get; private set; }

    private AccountGroup() { }

    public AccountGroup(string code, string name, AccountType accountType)
    {
        Code = code ?? throw new ArgumentNullException(nameof(code));
        Name = name ?? throw new ArgumentNullException(nameof(name));
        AccountType = accountType;
    }
}
