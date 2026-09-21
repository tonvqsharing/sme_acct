namespace SmeAccounting.Domain.Events;

public class RoleCreated : DomainEvent
{
    public long RoleId { get; }
    public long CompanyId { get; }

    public RoleCreated(long roleId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        RoleId = roleId;
        CompanyId = companyId;
    }
}
