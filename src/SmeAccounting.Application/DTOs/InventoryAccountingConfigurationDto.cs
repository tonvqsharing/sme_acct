namespace SmeAccounting.Application.DTOs;
public record InventoryAccountingConfigurationDto(long Id, long CompanyId, long InventoryAccountId, long CogsAccountId, long? InventoryAdjustmentGainAccountId, long? InventoryAdjustmentLossAccountId, bool IsActive);
