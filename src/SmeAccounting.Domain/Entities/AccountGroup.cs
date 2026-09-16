using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class AccountGroup : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public AccountType AccountType { get; private set; }
    public long CompanyId { get; private set; }
    public int DisplayOrder { get; private set; }

    private AccountGroup() { }

    public AccountGroup(string code, string name, AccountType accountType, long companyId, int displayOrder = 0)
    {
        Code = code ?? throw new ArgumentNullException(nameof(code));
        Name = name ?? throw new ArgumentNullException(nameof(name));
        AccountType = accountType;
        CompanyId = companyId > 0 ? companyId : throw new ArgumentOutOfRangeException(nameof(companyId));
        DisplayOrder = displayOrder;
    }
}
