using MediatR; using SmeAccounting.Application.DTOs; using SmeAccounting.Application.Queries; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class GetInventoryAdjustmentReasonHandler(IInventoryAdjustmentReasonRepository repo) : IRequestHandler<GetInventoryAdjustmentReasonQuery, InventoryAdjustmentReasonDto?>, IRequestHandler<GetInventoryAdjustmentReasonsByCompanyQuery, IReadOnlyList<InventoryAdjustmentReasonDto>>
{
    public async Task<InventoryAdjustmentReasonDto?> Handle(GetInventoryAdjustmentReasonQuery req, CancellationToken ct)
    {
        var r = await repo.GetByIdAsync(req.Id);
        return r == null ? null : new InventoryAdjustmentReasonDto(r.Id, r.CompanyId, r.Code, r.Name, r.IsActive, r.Description);
    }
    public async Task<IReadOnlyList<InventoryAdjustmentReasonDto>> Handle(GetInventoryAdjustmentReasonsByCompanyQuery req, CancellationToken ct)
    {
        var list = await repo.GetAllByCompanyAsync(req.CompanyId);
        return list.Select(r => new InventoryAdjustmentReasonDto(r.Id, r.CompanyId, r.Code, r.Name, r.IsActive, r.Description)).ToList();
    }
}
