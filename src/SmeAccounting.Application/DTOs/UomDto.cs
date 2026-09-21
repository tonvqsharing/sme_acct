namespace SmeAccounting.Application.DTOs;

public record UomDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    string? Symbol,
    bool IsActive,
    string? Description);
