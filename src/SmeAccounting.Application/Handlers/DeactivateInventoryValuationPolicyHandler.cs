using MediatR; using SmeAccounting.Application.Commands; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class DeactivateInventoryValuationPolicyHandler(IInventoryValuationPolicyRepository repo, IUnitOfWork uow) : IRequestHandler<DeactivateInventoryValuationPolicyCommand, DeactivateInventoryValuationPolicyResult>
{
    public async Task<DeactivateInventoryValuationPolicyResult> Handle(DeactivateInventoryValuationPolicyCommand req, CancellationToken ct)
    {
        var p = await repo.GetByIdAsync(req.Id);
        if (p == null) return new DeactivateInventoryValuationPolicyResult(false);
        p.Deactivate();
        await uow.SaveChangesAsync(ct);
        return new DeactivateInventoryValuationPolicyResult(true);
    }
}
