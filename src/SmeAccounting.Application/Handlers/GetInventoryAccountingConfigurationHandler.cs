using MediatR; using SmeAccounting.Application.DTOs; using SmeAccounting.Application.Queries; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class GetInventoryAccountingConfigurationHandler(IInventoryAccountingConfigurationRepository repo) : IRequestHandler<GetInventoryAccountingConfigurationQuery, InventoryAccountingConfigurationDto?>, IRequestHandler<GetInventoryAccountingConfigurationByCompanyQuery, InventoryAccountingConfigurationDto?>
{
    public async Task<InventoryAccountingConfigurationDto?> Handle(GetInventoryAccountingConfigurationQuery req, CancellationToken ct)
    {
        var cfg = await repo.GetByIdAsync(req.Id);
        return cfg == null ? null : Map(cfg);
    }
    public async Task<InventoryAccountingConfigurationDto?> Handle(GetInventoryAccountingConfigurationByCompanyQuery req, CancellationToken ct)
    {
        var cfg = await repo.GetByCompanyAsync(req.CompanyId);
        return cfg == null ? null : Map(cfg);
    }
    private static InventoryAccountingConfigurationDto Map(SmeAccounting.Domain.Entities.InventoryAccountingConfiguration c) => new InventoryAccountingConfigurationDto(c.Id, c.CompanyId, c.InventoryAccountId, c.CogsAccountId, c.InventoryAdjustmentGainAccountId, c.InventoryAdjustmentLossAccountId, c.IsActive);
}
