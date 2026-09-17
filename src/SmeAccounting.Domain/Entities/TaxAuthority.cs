using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class TaxAuthority : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public TaxAuthorityLevel AuthorityLevel { get; private set; }
    public long CompanyId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Address { get; private set; }
    public string? Phone { get; private set; }
    public string? Description { get; private set; }

    private TaxAuthority() { }

    public TaxAuthority(
        long companyId,
        string code,
        string name,
        TaxAuthorityLevel authorityLevel,
        string? address = null,
        string? phone = null,
        string? description = null)
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
        AuthorityLevel = authorityLevel;
        Address = address;
        Phone = phone;
        Description = description;

        AddDomainEvent(new TaxAuthorityCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
