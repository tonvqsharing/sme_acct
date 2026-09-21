using MediatR; using SmeAccounting.Application.Commands; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class DeactivateInventoryAccountingConfigurationHandler(IInventoryAccountingConfigurationRepository repo, IUnitOfWork uow) : IRequestHandler<DeactivateInventoryAccountingConfigurationCommand, DeactivateInventoryAccountingConfigurationResult>
{
    public async Task<DeactivateInventoryAccountingConfigurationResult> Handle(DeactivateInventoryAccountingConfigurationCommand req, CancellationToken ct)
    {
        var cfg = await repo.GetByIdAsync(req.Id);
        if (cfg == null) return new DeactivateInventoryAccountingConfigurationResult(false);
        cfg.Deactivate();
        await uow.SaveChangesAsync(ct);
        return new DeactivateInventoryAccountingConfigurationResult(true);
    }
}
