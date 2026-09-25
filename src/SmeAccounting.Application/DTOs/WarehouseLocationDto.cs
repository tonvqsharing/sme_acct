namespace SmeAccounting.Application.DTOs;

public record WarehouseLocationDto(
    long Id,
    long CompanyId,
    long WarehouseId,
    string Code,
    string Name,
    bool IsActive,
    string? Description);