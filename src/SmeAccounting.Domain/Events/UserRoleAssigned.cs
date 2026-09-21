namespace SmeAccounting.Domain.Events;

public class UserRoleAssigned : DomainEvent
{
    public long UserRoleId { get; }
    public long CompanyId { get; }

    public UserRoleAssigned(long userRoleId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        UserRoleId = userRoleId;
        CompanyId = companyId;
    }
}
