using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class Employee : BaseEntity
{
    public long CompanyId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public string? EmployeeNumber { get; private set; }
    public string? TaxCode { get; private set; }
    public string? Address { get; private set; }
    public string? Phone { get; private set; }
    public string? Email { get; private set; }
    public DateOnly? HireDate { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private Employee() { }

    public Employee(long companyId, string code, string name, string? employeeNumber = null, string? taxCode = null, string? address = null, string? phone = null, string? email = null, DateOnly? hireDate = null, string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");

        CompanyId = companyId;
        Code = code;
        Name = name;
        EmployeeNumber = employeeNumber;
        TaxCode = taxCode;
        Address = address;
        Phone = phone;
        Email = email;
        HireDate = hireDate;
        Description = description;

        AddDomainEvent(new EmployeeCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
