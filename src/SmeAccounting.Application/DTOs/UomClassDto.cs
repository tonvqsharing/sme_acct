namespace SmeAccounting.Application.DTOs;

public record UomClassDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    bool IsActive,
    string? Description);