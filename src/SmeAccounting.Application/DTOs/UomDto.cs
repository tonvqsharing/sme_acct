namespace SmeAccounting.Application.DTOs;

public record UomDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    string? Symbol,
    long? UomClassId,
    bool IsActive,
    string? Description);
