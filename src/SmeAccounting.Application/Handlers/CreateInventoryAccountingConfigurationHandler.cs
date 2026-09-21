using MediatR; using SmeAccounting.Application.Commands; using SmeAccounting.Domain.Entities; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class CreateInventoryAccountingConfigurationHandler(IInventoryAccountingConfigurationRepository repo, IUnitOfWork uow) : IRequestHandler<CreateInventoryAccountingConfigurationCommand, CreateInventoryAccountingConfigurationResult>
{
    public async Task<CreateInventoryAccountingConfigurationResult> Handle(CreateInventoryAccountingConfigurationCommand req, CancellationToken ct)
    {
        var cfg = new InventoryAccountingConfiguration(req.CompanyId, req.InventoryAccountId, req.CogsAccountId, req.InventoryAdjustmentGainAccountId, req.InventoryAdjustmentLossAccountId);
        await repo.AddAsync(cfg);
        await uow.SaveChangesAsync(ct);
        return new CreateInventoryAccountingConfigurationResult(cfg.Id);
    }
}
