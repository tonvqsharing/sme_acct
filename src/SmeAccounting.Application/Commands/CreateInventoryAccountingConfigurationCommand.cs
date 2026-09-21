using MediatR;
namespace SmeAccounting.Application.Commands;
public record CreateInventoryAccountingConfigurationCommand(long CompanyId, long InventoryAccountId, long CogsAccountId, long? InventoryAdjustmentGainAccountId = null, long? InventoryAdjustmentLossAccountId = null) : IRequest<CreateInventoryAccountingConfigurationResult>;
public record CreateInventoryAccountingConfigurationResult(long Id);
