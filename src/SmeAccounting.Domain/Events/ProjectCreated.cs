namespace SmeAccounting.Domain.Events;

public class ProjectCreated : DomainEvent
{
    public long ProjectId { get; }
    public long CompanyId { get; }

    public ProjectCreated(
        long projectId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        ProjectId = projectId;
        CompanyId = companyId;
    }
}
