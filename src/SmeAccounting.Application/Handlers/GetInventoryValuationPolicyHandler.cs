using MediatR; using SmeAccounting.Application.DTOs; using SmeAccounting.Application.Queries; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class GetInventoryValuationPolicyHandler(IInventoryValuationPolicyRepository repo) : IRequestHandler<GetInventoryValuationPolicyQuery, InventoryValuationPolicyDto?>, IRequestHandler<GetInventoryValuationPoliciesByCompanyQuery, IReadOnlyList<InventoryValuationPolicyDto>>
{
    public async Task<InventoryValuationPolicyDto?> Handle(GetInventoryValuationPolicyQuery req, CancellationToken ct)
    {
        var p = await repo.GetByIdAsync(req.Id);
        return p == null ? null : Map(p);
    }
    public async Task<IReadOnlyList<InventoryValuationPolicyDto>> Handle(GetInventoryValuationPoliciesByCompanyQuery req, CancellationToken ct)
    {
        var list = await repo.GetAllByCompanyAsync(req.CompanyId);
        return list.Select(Map).ToList();
    }
    private static InventoryValuationPolicyDto Map(SmeAccounting.Domain.Entities.InventoryValuationPolicy p) => new InventoryValuationPolicyDto(p.Id, p.CompanyId, p.Code, p.Name, p.ValuationMethod.ToString(), p.IsActive, p.Description);
}
