using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class UserRole : BaseEntity
{
    public long UserId { get; private set; }
    public long RoleId { get; private set; }
    public long CompanyId { get; private set; }
    public bool IsActive { get; private set; } = true;

    private UserRole() { }

    public UserRole(long userId, long roleId, long companyId)
    {
        if (userId <= 0)
            throw new DomainException("UserId must be greater than zero.");
        if (roleId <= 0)
            throw new DomainException("RoleId must be greater than zero.");
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");

        UserId = userId;
        RoleId = roleId;
        CompanyId = companyId;

        AddDomainEvent(new UserRoleAssigned(Id, CompanyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
