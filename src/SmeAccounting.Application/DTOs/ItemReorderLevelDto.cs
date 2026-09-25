namespace SmeAccounting.Application.DTOs;

public record ItemReorderLevelDto(
    long Id,
    long CompanyId,
    long ItemId,
    long? WarehouseId,
    decimal MinimumQuantity,
    decimal? MaximumQuantity,
    bool IsActive);
