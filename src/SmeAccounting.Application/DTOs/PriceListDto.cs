namespace SmeAccounting.Application.DTOs;

public record PriceListDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    bool IsActive,
    string? Description);