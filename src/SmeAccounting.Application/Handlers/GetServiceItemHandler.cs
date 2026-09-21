using MediatR; using SmeAccounting.Application.DTOs; using SmeAccounting.Application.Queries; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class GetServiceItemHandler(IServiceItemRepository repo) : IRequestHandler<GetServiceItemQuery, ServiceItemDto?>, IRequestHandler<GetServiceItemsByCompanyQuery, IReadOnlyList<ServiceItemDto>>
{
    public async Task<ServiceItemDto?> Handle(GetServiceItemQuery req, CancellationToken ct)
    {
        var s = await repo.GetByIdAsync(req.Id);
        return s == null ? null : new ServiceItemDto(s.Id, s.CompanyId, s.Code, s.Name, s.UomId, s.IsActive, s.Description);
    }
    public async Task<IReadOnlyList<ServiceItemDto>> Handle(GetServiceItemsByCompanyQuery req, CancellationToken ct)
    {
        var list = await repo.GetAllByCompanyAsync(req.CompanyId);
        return list.Select(s => new ServiceItemDto(s.Id, s.CompanyId, s.Code, s.Name, s.UomId, s.IsActive, s.Description)).ToList();
    }
}
