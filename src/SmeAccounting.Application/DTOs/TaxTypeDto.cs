namespace SmeAccounting.Application.DTOs;

public record TaxTypeDto(
    long Id,
    string Code,
    string Name,
    string TaxCategory,
    long CompanyId,
    bool IsActive,
    string? Description);
