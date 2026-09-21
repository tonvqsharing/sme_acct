namespace SmeAccounting.Domain.Events;

public class CompanyMembershipCreated : DomainEvent
{
    public long MembershipId { get; }
    public long CompanyId { get; }

    public CompanyMembershipCreated(long membershipId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        MembershipId = membershipId;
        CompanyId = companyId;
    }
}
