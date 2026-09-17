using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxAuthoritiesByCompanyHandler(
    ITaxAuthorityRepository repository)
    : IRequestHandler<GetTaxAuthoritiesByCompanyQuery, IReadOnlyList<TaxAuthorityDto>>
{
    public async Task<IReadOnlyList<TaxAuthorityDto>> Handle(
        GetTaxAuthoritiesByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new TaxAuthorityDto(
                e.Id, e.Code, e.Name,
                e.AuthorityLevel.ToString(),
                e.CompanyId, e.IsActive,
                e.Address, e.Phone, e.Description))
            .ToList();
    }
}
