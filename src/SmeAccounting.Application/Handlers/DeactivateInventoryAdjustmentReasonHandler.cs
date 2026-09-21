using MediatR; using SmeAccounting.Application.Commands; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class DeactivateInventoryAdjustmentReasonHandler(IInventoryAdjustmentReasonRepository repo, IUnitOfWork uow) : IRequestHandler<DeactivateInventoryAdjustmentReasonCommand, DeactivateInventoryAdjustmentReasonResult>
{
    public async Task<DeactivateInventoryAdjustmentReasonResult> Handle(DeactivateInventoryAdjustmentReasonCommand req, CancellationToken ct)
    {
        var r = await repo.GetByIdAsync(req.Id);
        if (r == null) return new DeactivateInventoryAdjustmentReasonResult(false);
        r.Deactivate();
        await uow.SaveChangesAsync(ct);
        return new DeactivateInventoryAdjustmentReasonResult(true);
    }
}
