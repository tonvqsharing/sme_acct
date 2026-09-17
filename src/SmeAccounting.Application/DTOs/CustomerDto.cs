namespace SmeAccounting.Application.DTOs;

public record CustomerDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    string? TaxCode,
    string? Address,
    string? Phone,
    string? Email,
    bool IsActive,
    string? Description);
