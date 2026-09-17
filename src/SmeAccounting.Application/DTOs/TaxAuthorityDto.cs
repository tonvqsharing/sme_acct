namespace SmeAccounting.Application.DTOs;

public record TaxAuthorityDto(
    long Id,
    string Code,
    string Name,
    string AuthorityLevel,
    long CompanyId,
    bool IsActive,
    string? Address,
    string? Phone,
    string? Description);
