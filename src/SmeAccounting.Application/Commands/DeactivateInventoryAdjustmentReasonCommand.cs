using MediatR;
namespace SmeAccounting.Application.Commands;
public record DeactivateInventoryAdjustmentReasonCommand(long Id) : IRequest<DeactivateInventoryAdjustmentReasonResult>;
public record DeactivateInventoryAdjustmentReasonResult(bool Success);
