using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class CompanyMembership : BaseEntity
{
    public long UserId { get; private set; }
    public long CompanyId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public DateTimeOffset JoinedAt { get; private set; }

    private CompanyMembership() { }

    public CompanyMembership(long userId, long companyId)
    {
        if (userId <= 0)
            throw new DomainException("UserId must be greater than zero.");
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");

        UserId = userId;
        CompanyId = companyId;
        JoinedAt = DateTimeOffset.UtcNow;

        AddDomainEvent(new CompanyMembershipCreated(Id, CompanyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
