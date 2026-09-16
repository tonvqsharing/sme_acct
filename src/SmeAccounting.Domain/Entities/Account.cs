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
    public long CompanyId { get; private set; }
    public string? Description { get; private set; }
    public NormalBalance NormalBalance { get; private set; }

    private readonly List<Account> _children = [];
    public IReadOnlyCollection<Account> Children => _children.AsReadOnly();

    private Account() { }

    public Account(AccountCode code, string name, AccountType accountType, long companyId,
        NormalBalance normalBalance, int level = 1, long? parentId = null, long? accountGroupId = null,
        string? description = null)
    {
        Code = code ?? throw new ArgumentNullException(nameof(code));
        Name = name ?? throw new ArgumentNullException(nameof(name));
        AccountType = accountType;
        CompanyId = companyId > 0 ? companyId : throw new ArgumentOutOfRangeException(nameof(companyId));
        NormalBalance = normalBalance;
        Level = level;
        ParentId = parentId;
        AccountGroupId = accountGroupId;
        Description = description;
    }

    public void Deprecate()
    {
        IsActive = false;
        AddDomainEvent(new AccountDeprecated(Id, DateTimeOffset.UtcNow));
    }

    public Account AddChild(AccountCode code, string name, AccountType accountType, long companyId,
        NormalBalance normalBalance, long? accountGroupId = null, string? description = null)
    {
        var child = new Account(code, name, accountType, companyId, normalBalance, Level + 1, Id, accountGroupId, description);
        _children.Add(child);
        return child;
    }
}
