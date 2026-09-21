namespace SmeAccounting.Application.DTOs;

public record WarehouseDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    string? Address,
    bool IsActive,
    string? Description);
