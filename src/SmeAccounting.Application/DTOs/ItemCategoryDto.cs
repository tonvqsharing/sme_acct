namespace SmeAccounting.Application.DTOs;

public record ItemCategoryDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    long? ParentId,
    bool IsActive,
    string? Description);
