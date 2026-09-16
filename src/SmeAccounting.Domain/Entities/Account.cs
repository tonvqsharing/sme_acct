using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class Account : BaseEntity
{
    public AccountCode Code { get; private set; } = null!;
    public string Name { get; private set; } = string.Empty;
    public int Level { get; private set; }
    public long? ParentId { get; private set; }
    public AccountType AccountType { get; private set; }
    public bool IsActive { get; private set; } = true;
    public long? AccountGroupId { get; private set; }

    private readonly List<Account> _children = [];
    public IReadOnlyCollection<Account> Children => _children.AsReadOnly();

    private Account() { }

    public Account(AccountCode code, string name, AccountType accountType, int level = 1, long? parentId = null, long? accountGroupId = null)
    {
        Code = code ?? throw new ArgumentNullException(nameof(code));
        Name = name ?? throw new ArgumentNullException(nameof(name));
        AccountType = accountType;
        Level = level;
        ParentId = parentId;
        AccountGroupId = accountGroupId;
    }

    public void Deprecate()
    {
        IsActive = false;
        AddDomainEvent(new AccountDeprecated(Id, DateTimeOffset.UtcNow));
    }

    public Account AddChild(AccountCode code, string name, AccountType accountType, long? accountGroupId = null)
    {
        var child = new Account(code, name, accountType, Level + 1, Id, accountGroupId);
        _children.Add(child);
        return child;
    }
}
