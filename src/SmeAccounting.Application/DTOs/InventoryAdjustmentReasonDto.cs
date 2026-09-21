namespace SmeAccounting.Application.DTOs;
public record InventoryAdjustmentReasonDto(long Id, long CompanyId, string Code, string Name, bool IsActive, string? Description);
