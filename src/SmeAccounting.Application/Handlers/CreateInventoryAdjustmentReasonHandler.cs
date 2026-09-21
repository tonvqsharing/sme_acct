using MediatR; using SmeAccounting.Application.Commands; using SmeAccounting.Domain.Entities; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class CreateInventoryAdjustmentReasonHandler(IInventoryAdjustmentReasonRepository repo, IUnitOfWork uow) : IRequestHandler<CreateInventoryAdjustmentReasonCommand, CreateInventoryAdjustmentReasonResult>
{
    public async Task<CreateInventoryAdjustmentReasonResult> Handle(CreateInventoryAdjustmentReasonCommand req, CancellationToken ct)
    {
        var r = new InventoryAdjustmentReason(req.CompanyId, req.Code, req.Name, req.Description);
        await repo.AddAsync(r);
        await uow.SaveChangesAsync(ct);
        return new CreateInventoryAdjustmentReasonResult(r.Id);
    }
}
