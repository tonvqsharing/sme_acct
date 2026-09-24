namespace SmeAccounting.Application.DTOs;

public record ItemDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    long? ItemCategoryId,
    long? UomId,
    bool IsStockItem,
    bool IsServiceItem,
    long? ItemGroupId,
    bool IsActive,
    string? Description);
