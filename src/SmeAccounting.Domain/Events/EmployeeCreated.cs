namespace SmeAccounting.Domain.Events;

public class EmployeeCreated : DomainEvent
{
    public long EmployeeId { get; }
    public long CompanyId { get; }

    public EmployeeCreated(long employeeId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        EmployeeId = employeeId;
        CompanyId = companyId;
    }
}
