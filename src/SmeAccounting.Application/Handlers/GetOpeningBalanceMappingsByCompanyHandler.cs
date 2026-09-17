using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetOpeningBalanceMappingsByCompanyHandler(
    IOpeningBalanceMappingRepository repository)
    : IRequestHandler<GetOpeningBalanceMappingsByCompanyQuery, IReadOnlyList<OpeningBalanceMappingDto>>
{
    public async Task<IReadOnlyList<OpeningBalanceMappingDto>> Handle(
        GetOpeningBalanceMappingsByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new OpeningBalanceMappingDto(
                e.Id, e.CompanyId, e.VoucherTypeId,
                e.DebitAccountId, e.CreditAccountId,
                e.IsActive, e.Description))
            .ToList();
    }
}
