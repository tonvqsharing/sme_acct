namespace SmeAccounting.Application.DTOs;

public record ItemGroupDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    bool IsActive,
    string? Description);