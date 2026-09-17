using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetVoucherTypesByCompanyHandler(
    IVoucherTypeRepository repository)
    : IRequestHandler<GetVoucherTypesByCompanyQuery, IReadOnlyList<VoucherTypeDto>>
{
    public async Task<IReadOnlyList<VoucherTypeDto>> Handle(
        GetVoucherTypesByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllAsync();
        return entities
            .Where(e => e.CompanyId == request.CompanyId)
            .Select(e => new VoucherTypeDto(
                e.Id, e.Code, e.Name,
                e.VoucherCategory.ToString(),
                e.CompanyId, e.IsActive, e.Description))
            .ToList();
    }
}
