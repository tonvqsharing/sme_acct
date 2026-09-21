using MediatR;
namespace SmeAccounting.Application.Commands;
public record CreateInventoryAdjustmentReasonCommand(long CompanyId, string Code, string Name, string? Description = null) : IRequest<CreateInventoryAdjustmentReasonResult>;
public record CreateInventoryAdjustmentReasonResult(long Id);
