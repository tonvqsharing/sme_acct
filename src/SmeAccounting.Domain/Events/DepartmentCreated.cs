namespace SmeAccounting.Domain.Events;

public class DepartmentCreated : DomainEvent
{
    public long DepartmentId { get; }
    public long CompanyId { get; }

    public DepartmentCreated(
        long departmentId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        DepartmentId = departmentId;
        CompanyId = companyId;
    }
}
